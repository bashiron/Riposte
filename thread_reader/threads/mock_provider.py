from thread_reader.settings import BASE_DIR
import json as json_lib

def sequence(items):
    seq = []
    for item in items:
        with open(BASE_DIR / 'threads/json_mocks' / (item + '.json'), encoding='utf-8') as json:
            seq.append(json_lib.loads(json.read()))
    return seq
