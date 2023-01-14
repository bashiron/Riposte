from riposte.settings import BASE_DIR
from .twitter_requests import Fetcher, R
from .mention_parser import *
from .misc import f_put

import re
from collections.abc import Callable
from time import time
import json as json_lib
from random import randint
from queue import Queue, LifoQueue


def sequence(items):
    """Recibe una lista de `paths` a archivos json y devuelve una lista con esos jsons convertidos a ``dict`` para su
    uso en python.
    """
    seq = []
    for item in items:
        seq.append(load_as_json(item))
    return seq


def generate(kind, twid, funs: list[Callable[[str, dict], None]] = None):
    """Trae un tweet o chat de la api y lo almacena en disco, con un procesado opcional de por medio.

    Parameters
    ----------
    kind : `str`
        String que indica el tipo de dato a conseguir. Posibles valores: `tweet` | `chat`.
    twid : `str`
        Id del tweet a conseguir.
    funs
        Lista de funciones a aplicar al objeto traido de la api. Estas funciones deben aceptar el parametro kind
        (tipo de dato) y res (objeto de respuesta de la api).

    Notes
    -----
    1. Evalua el tipo de objeto a ser conseguido con un `match`
    2. Pide el payload estandar al fetcher y lo simplifica porque necesita los datos minimos, las funciones de procesado
    se encargaran de rellenar los datos extra
    3. Consigue el objeto haciendo un pedido con payload personalizado (simplificado)
    4. Aplica las funciones de procesado al objeto conseguido
    5. Almacena el objeto final en disco
    """
    if funs is None:
        funs = []
    fetcher = Fetcher(R)
    res = None
    filename = re.search(r"^.+?(?=\.)", str(time())).group(0)  # basicamente un numero que no se repite

    match kind:
        case 'tweet':
            payload = fetcher.tweet_payload()
            simplify(payload, kind)
            res = fetcher.custom_request_tweet(twid, payload)
            for fn in funs:
                fn(kind, res)  # aplicamos la funcion a lo traido de la api

        case 'chat':
            payload = fetcher.chat_payload(twid)
            simplify(payload, kind)
            res = fetcher.custom_request_chat(payload)
            for fn in funs:
                fn(kind, res)

    save_as_json(kind, res, filename)


def simplify(payload, kind):
    """Simplifica el payload quitando los campos que contienen datos extra.

    Parameters
    ----------
    payload : `dict`
        Payload a simplificar.
    kind : `str`
        Tipo de dato.
    """
    match kind:
        case 'tweet':
            payload['tweet.fields'] = payload['tweet.fields'].replace(',attachments', '')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '')
            payload.pop('media.fields')

        case 'chat':
            payload['tweet.fields'] = payload['tweet.fields'].replace(',attachments', '')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '')
            payload.pop('media.fields')


# TODO: al borrar las entities se pierden los datos de url que no son menciones
def remove_mentions(mode, kind, data):
    match kind:
        case 'tweet':
            obj = data['data']
            try:
                parent_id = obj['in_reply_to_user_id']
            except KeyError:
                try:
                    obj.pop('entities')
                except KeyError:
                    pass
            else:
                obj.pop('in_reply_to_user_id')
                if mode == 'parent':
                    obj['text'] = rm_parents_mentions(obj['text'], obj['entities']['mentions'])
                else:
                    obj['text'] = rm_all_mentions(obj['text'], obj['entities']['mentions'])
                obj.pop('entities')
                users = data['includes']['users']
                data['includes']['users'] = [u for u in users if u['id'] != parent_id]

        case 'chat':
            parent_id = data['data'][0]['in_reply_to_user_id']  # todos tienen el mismo parent
            for obj in data['data']:
                if mode == 'parent':
                    obj['text'] = rm_parents_mentions(obj['text'], obj['entities']['mentions'])
                else:
                    obj['text'] = rm_all_mentions(obj['text'], obj['entities']['mentions'])
                obj.pop('entities')
                obj.pop('in_reply_to_user_id')

            users = data['includes']['users']
            data['includes']['users'] = [u for u in users if u['id'] != parent_id]


# Inserta datos de imagenes en una respuesta json de tipo 'tweet' o 'chat'
def insert_pics(kind, data):
    match kind:
        case 'tweet':
            keys, pairs = make_pairs()
            data['data']['attachments'] = {'media_keys': keys}
            data['includes']['media'] = list(map(lambda x: {'media_key': x[1], 'type': 'photo', 'url': x[0]}, pairs))
        case 'chat':
            media = []
            for obj in data['data']:
                keys, pairs = make_pairs()
                media.extend(pairs)
                obj['attachments'] = {'media_keys': keys}

            data['includes']['media'] = list(map(lambda x: {'media_key': x[1], 'type': 'photo', 'url': x[0]}, media))


# Decide una cantidad entre 1 y 4 y crea los keys y los pares (key, url).
def make_pairs():
    amount = randint(1, 4)
    pics = choose_pics(amount)
    keys = keygen(amount)
    pairs = zip(pics, keys)
    return keys, pairs


# Devuelve una lista de 'amount' cantidad de imagenes elegidas aleatoriamente de la variable global 'images'.
# TODO: darle la capacidad de no elegir ninguna imagen
# TODO: hacer que no use imagenes repetidas
def choose_pics(amount):
    ls = []
    for _ in range(amount):
        rand = randint(0, len(images) - 1)
        ls.append(images[rand])
    return ls


# Genera una cantidad de 'amount' codigos de 8 digitos.
def keygen(amount):
    ls = []
    for _ in range(amount):
        ls.append(str(randint(0, 99999999)).zfill(8))
    return ls


# Devuelve un LIFO de los jsons (en forma dict) con sus datos editados para reflejar los niveles de respuesta
# TODO: por ahora se construye asumiendo el flujo de siempre expandir la primer respuesta del chat
# TODO: hacer que en el Fetcher al pedir un chat esas respuestas vengan con los datos de nivel del clickeado
# TODO: y si se expande un chat (horizontalmente) solo se entrega un chat sin insertar info sobre niveles
def build_chat(items):
    tweet, *chats = items
    tweet = load_as_json(tweet)
    que = Queue()
    for json in [load_as_json(j) for j in chats]:
        que.put(json)
    levels = [level_data(tweet, 'tweet')]
    res = linked_chat(levels, que)
    res.put(tweet)
    return res


# Construye un LIFO de jsons (dicts) donde cada uno tiene añadidos datos de nivel
def linked_chat(levels, jsons):
    match jsons.empty():
        case True:
            return LifoQueue()
        case False:
            chat = jsons.get()  # esto quita un elemento del queue
            que = linked_chat([level_data(chat)] + levels, jsons)
            item = insert_level(chat, levels)
            return f_put(que, item)


def level_data(json, kind='chat'):
    match kind:
        case 'tweet':
            obj = json['data']
            user = json['includes']['users'][0]
            return {
                'user_id': obj['author_id'],
                'user_name': user['name'],
                'user_username': user['username'],
                'twt_id': obj['id']
            }

        case 'chat':
            obj = json['data'][0]  # asumimos que elegiremos el primero porque si
            user = json['includes']['users'][0]  # suponemos orden
            return {
                'user_id': obj['author_id'],
                'user_name': user['name'],
                'user_username': user['username'],
                'twt_id': obj['id']
            }


#
def insert_level(chat, levels):
    last = levels[0]
    for obj in chat['data']:
        obj['in_reply_to_user_id'] = last['user_id']
        entities_mention(obj, levels)
        text_mention(obj, levels)

    user_obj = {
        'id': last['user_id'],
        'name': last['user_name'],
        'username': last['user_username']
    }
    chat['includes']['users'].append(user_obj)
    return chat


# -------- almacenado --------

def load_as_json(name):
    with open(BASE_DIR / 'chat/json_mocks' / (name + '.json'), encoding='utf-8') as json:
        ret = json_lib.loads(json.read())
    return ret


def save_as_json(kind, data, name):
    with open(BASE_DIR / 'chat/json_mocks/gen' / kind / (name + '.json'), 'w') as file:
        file.write(json_lib.dumps(data))


images = [
    'https://pbs.twimg.com/media/FaACOIIXoAM-SU_?format=jpg',
    'https://pbs.twimg.com/media/FZ-PNHqWYAADmm-?format=jpg',
    'https://pbs.twimg.com/media/FZ7cfkmXwAAxaNA?format=png',
    'https://pbs.twimg.com/media/FaB_og7XEAE4SIa?format=jpg',
    'https://pbs.twimg.com/media/FZ7CHZOaIAA-I42?format=png',
    'https://pbs.twimg.com/media/FZ-F4o7akAElSKk?format=jpg',
    'https://pbs.twimg.com/media/FaBrs1VacAEpTOq?format=jpg',
    'https://pbs.twimg.com/media/FZ93ToJUcAAtQRs?format=jpg',
    'https://pbs.twimg.com/media/FaCXJWdaUAE0LK2?format=jpg',
    'https://pbs.twimg.com/media/FZzIihWacAAjlaF?format=jpg'
]
