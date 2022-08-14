from thread_reader.settings import BASE_DIR
from .twitter_requests import Fetcher, R
import re
from time import time
import json as json_lib
from random import randint


def sequence(items):
    seq = []
    for item in items:
        with open( BASE_DIR / 'threads/json_mocks' / (item + '.json'), encoding='utf-8') as json:
            seq.append(json_lib.loads(json.read()))
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
            payload['tweet.fields'] = payload['tweet.fields'].replace(',attachments', '').replace(',entities', '')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '')
            payload.pop('media.fields')

        case 'thread':
            payload.pop('tweet.fields')
            payload['expansions'] = payload['expansions'].replace(',attachments.media_keys', '').replace(',in_reply_to_user_id', '')
            payload.pop('media.fields')

def save_as_json(kind, data, name):
    with open( BASE_DIR / 'threads/json_mocks/gen' / kind / ( name + '.json'), 'w') as file:
        file.write(json_lib.dumps(data))

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
