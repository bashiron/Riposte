from thread_reader.settings import BASE_DIR
from .twitter_requests import Fetcher, R
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
def generate(kind, twid, fun=(lambda y, x: x)):
    fetcher = Fetcher(R)
    res = None
    filename = re.search(r"^.+?(?=\.)", str(time())).group(0)    # basicamente un numero que no se repite

    match kind:
        case 'tweet':
            payload = fetcher.tweet_payload()
            simplify(payload, kind)
            res = fetcher.custom_request_tweet(twid, payload)
            fun(kind, res)

        case 'thread':
            payload = fetcher.thread_payload(twid)
            simplify(payload, kind)
            res = fetcher.custom_request_thread(payload)
            fun(kind, res)

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

def remove_mentions(mode, kind, data):
    match kind:
        case 'tweet':
            obj = data['data']
            rm_parents_mentions(obj) if mode == 'parent' else rm_all_mentions(obj)
            obj.pop('entities')

        case 'thread':
            for obj in data['data']:
                rm_parents_mentions(obj) if mode == 'parent' else rm_all_mentions(obj)
                obj.pop('entities')

def rm_parents_mentions(obj):     #TODO hacer version que quite las menciones de todos los padres anteriores
    # ya que las mentions estan ordenadas para borrar todas las menciones padre podria tomar todas las posiciones en orden hasta llegar a la mention que refiere al padre (comparando con in_reply_to_user_id)
    mentions = obj['entities']['mentions']
    pos = [m['end'] for m in mentions if (m['id'] == obj['in_reply_to_user_id'])][0] + 1
    obj['text'] = obj['text'][pos:]

def rm_all_mentions(obj):       #TODO esto solo funciona si todas las menciones estan al comienzo del texto
    # deberia tomar la primer parte del texto (al start) y concatenarla con la segunda parte a partir del 'end', entonces se reconstruye el texto desapareciendo la mencion
    mentions = obj['entities']['mentions']
    pos_ls = [m['end'] - m['start'] + 1 for m in mentions]  # el (+1) es por el espacio entre mentions
    for pos in pos_ls:
        obj['text'] = obj['text'][pos:]

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
def build_thread(items):
    que = Queue()
    for json in [load_as_json(j) for j in items]:
        que.put(json)
    return linked_thread([], que)

# Construye un LIFO de jsons (dicts) donde cada uno tiene añadidos datos de nivel
def linked_thread(levels, jsons):
    match jsons.empty():
        case True:
            return LifoQueue()
        case False:
            thread = jsons.get()    # esto quita un elemento del queue
            que = linked_thread([level_data(thread)] + levels, jsons)
            item = insert_level(thread, levels) if levels else thread
            return f_put(que, item)

def f_put(que, item):
    que.put(item)
    return que

#
def level_data(thread):
    obj = thread['data'][0]
    user = thread['includes']['users'][0]
    return {
        'user_id': obj['author_id'],
        'twt_id': obj['id'],
        'username': user['username']
    }

#
def insert_level(thread, levels):
    for obj in thread['data']:
        obj['in_reply_to_user_id'] = levels[-1]['user_id']
        entities_mention(obj, levels)
        text_mention(obj, levels)

    return thread

def entities_mention(obj, levels):
    obj['entities'] = {'mentions': []}
    length_ls = [-1]    # de esta forma el primer start es 0 (-1 + 1)

    for lv in levels:
        length = len(lv['username'])
        mention = {
            'start': length_ls[-1] + 1,
            'end': length + 1,
            'username': lv['username'],
            'id': lv['user_id']
        }
        obj['entities']['mentions'].append(mention)
        length_ls.append(length + 1)

def text_mention(obj, levels):
    pos = 0

    for lv in levels:
        mention = '@' + lv['username'] + ' '
        txt = obj['text']
        obj['text'] = txt[:pos] + mention + txt[pos:]
        pos += len(mention)

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
