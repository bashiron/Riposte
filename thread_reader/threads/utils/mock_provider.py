from thread_reader.settings import BASE_DIR
from .twitter_requests import Fetcher, R
from .mention_parser import *
from .misc import f_put
import re
from time import time
import json as json_lib
from random import randint
from queue import Queue, LifoQueue


def sequence(items):
    seq = []
    for item in items:
        seq.append(load_as_json(item))
    return seq

# Trae un tweet o thread de la api y lo almacena en disco, con un procesado opcional de por medio.
def generate(kind, twid, funs=None):
    if funs is None:
        funs = []
    fetcher = Fetcher(R)
    res = None
    filename = re.search(r"^.+?(?=\.)", str(time())).group(0)    # basicamente un numero que no se repite

    match kind:
        case 'tweet':
            payload = fetcher.tweet_payload()
            simplify(payload, kind)
            res = fetcher.custom_request_tweet(twid, payload)
            for fn in funs:
                fn(kind, res)

        case 'thread':
            payload = fetcher.thread_payload(twid)
            simplify(payload, kind)
            res = fetcher.custom_request_thread(payload)
            for fn in funs:
                fn(kind, res)

    save_as_json(kind, res, filename)

def simplify(payload, kind):
    match kind:
        case 'tweet':
            payload['tweet.fields'] = payload['tweet.fields'].replace(',attachments', '')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '')
            payload.pop('media.fields')

        case 'thread':
            payload['tweet.fields'] = payload['tweet.fields'].replace(',attachments', '')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '')
            payload.pop('media.fields')

#
def remove_mentions(mode, kind, data):
    match kind:
        case 'tweet':
            obj = data['data']
            parent_id = obj['in_reply_to_user_id']
            obj.pop('in_reply_to_user_id')
            if mode == 'parent':
                obj['text'] = rm_parents_mentions(obj['text'], obj['entities']['mentions'])
            else:
                obj['text'] = rm_all_mentions(obj['text'], obj['entities']['mentions'])
            obj.pop('entities')
            users = data['includes']['users']
            data['includes']['users'] = [u for u in users if u['id'] != parent_id]

        case 'thread':
            parent_id = data['data'][0]['in_reply_to_user_id']  # todos tienen el mismo parent
            for obj in data['data']:
                rm_parents_mentions(obj) if mode == 'parent' else rm_all_mentions(obj['text'], obj['entities']['mentions'])
                obj.pop('entities')
                obj.pop('in_reply_to_user_id')

            users = data['includes']['users']
            data['includes']['users'] = [u for u in users if u['id'] != parent_id]

# Inserta datos de imagenes en una respuesta json de tipo 'tweet' o 'thread'
def insert_pics(kind, data):
    match kind:
        case 'tweet':
            keys, pairs = make_pairs()
            data['data']['attachments'] = {'media_keys': keys}
            data['includes']['media'] = list(map(lambda x: {'media_key': x[1], 'type': 'photo', 'url': x[0]}, pairs))
        case 'thread':
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
        rand = randint(0, len(images)-1)
        ls.append(images[rand])
    return ls

# Genera una cantidad de 'amount' codigos de 8 digitos.
def keygen(amount):
    ls = []
    for _ in range(amount):
        ls.append(str(randint(0, 99999999)).zfill(8))
    return ls

# Devuelve un LIFO de los jsons (en forma dict) con sus datos editados para reflejar los niveles de respuesta
# TODO: por ahora se construye asumiendo el flujo de siempre expandir la primer respuesta del thread
# TODO: hacer que en el Fetcher al pedir un thread esas respuestas vengan con los datos de nivel del clickeado
# TODO: y si se expande un thread (horizontalmente) solo se entrega un thread sin insertar info sobre niveles
def build_thread(items):
    tweet, *threads = items
    tweet = load_as_json(tweet)
    que = Queue()
    for json in [load_as_json(j) for j in threads]:
        que.put(json)
    levels = [level_data(tweet, 'tweet')]
    res = linked_thread(levels, que)
    res.put(tweet)
    return res

# Construye un LIFO de jsons (dicts) donde cada uno tiene añadidos datos de nivel
def linked_thread(levels, jsons):
    match jsons.empty():
        case True:
            return LifoQueue()
        case False:
            thread = jsons.get()    # esto quita un elemento del queue
            que = linked_thread([level_data(thread)] + levels, jsons)
            item = insert_level(thread, levels)
            return f_put(que, item)

def level_data(json, kind='thread'):
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

        case 'thread':
            obj = json['data'][0]   # asumimos que eligiremos el primero porque si
            user = json['includes']['users'][0]  # suponemos orden
            return {
                'user_id': obj['author_id'],
                'user_name': user['name'],
                'user_username': user['username'],
                'twt_id': obj['id']
            }

#
def insert_level(thread, levels):
    last = levels[0]
    for obj in thread['data']:
        obj['in_reply_to_user_id'] = last['user_id']
        entities_mention(obj, levels)
        text_mention(obj, levels)

    user_obj = {
        'id': last['user_id'],
        'name': last['user_name'],
        'username': last['user_username']
    }
    thread['includes']['users'].append(user_obj)
    return thread

# -------- almacenado --------

def load_as_json(name):
    with open(BASE_DIR / 'threads/json_mocks' / (name + '.json'), encoding='utf-8') as json:
        ret = json_lib.loads(json.read())
    return ret

def save_as_json(kind, data, name):
    with open( BASE_DIR / 'threads/json_mocks/gen' / kind / ( name + '.json'), 'w') as file:
        file.write(json_lib.dumps(data))

images = [
    'https://pbs.twimg.com/media/FaACOIIXoAM-SU_?format=jpg&name=large',
    'https://pbs.twimg.com/media/FZ-PNHqWYAADmm-?format=jpg&name=large',
    'https://pbs.twimg.com/media/FZ7cfkmXwAAxaNA?format=png&name=240x240',
    'https://pbs.twimg.com/media/FaB_og7XEAE4SIa?format=jpg&name=4096x4096',
    'https://pbs.twimg.com/media/FZ7CHZOaIAA-I42?format=png&name=900x900',
    'https://pbs.twimg.com/media/FZ-F4o7akAElSKk?format=jpg&name=large',
    'https://pbs.twimg.com/media/FaBrs1VacAEpTOq?format=jpg&name=medium',
    'https://pbs.twimg.com/media/FZ93ToJUcAAtQRs?format=jpg&name=medium',
    'https://pbs.twimg.com/media/FaCXJWdaUAE0LK2?format=jpg&name=4096x4096',
    'https://pbs.twimg.com/media/FZzIihWacAAjlaF?format=jpg&name=large'
]
