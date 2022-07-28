from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from thread_reader.settings import BASE_DIR
import requests, re, json
import environ
from .forms import LinkForm

env = environ.Env()
tweet_ctx = {'base': {}, 'aux': {}}

def home(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            tw_id = extract_id(form.cleaned_data['tw_link'])
            return HttpResponseRedirect(f'tweet/{tw_id}')
    else:
        form = LinkForm()

    return render(request, 'threads/home.html', {'form': form})

# links para probar:
# https://twitter.com/VideoArtGame/status/1548668846050988032
# https://twitter.com/VideoArtGame/status/1548668846050988032?s=20&t=ddJrMfddkleybcG2dZqU-g
# con cuatro imagenes:
# https://twitter.com/c_o_l_a/status/1546465898848190465
# https://twitter.com/c_o_l_a/status/1546465898848190465?s=20&t=zI1XMFXtJotfy1RACRLyqg

def extract_id(url):
    rx_url = r"^(?:[^\/]*\/){5}([^\/]*)"            #regex para links copiados de la barra de url
    rx_btn = r"^(?:[^\/]*\/){5}([^\/]*.+?(?=\?))"   #regex para links copiados con "copy link to tweet" (tienen un '?')
    return re.search(rx_btn if url.find('?') != -1 else rx_url, url).group(1)

def tweet(request, id):
    res = request_tweet(str(id))
    # with open(BASE_DIR / 'threads/json_mocks/fake/long_tweet.json', encoding='utf-8') as mock:
    #     res = json.load(mock)
    return render(request, 'threads/tweet.html', fill_tweet_context(tweet_ctx, res))

def fill_tweet_context(ctx, res):
    ctx['base']['name'] = res['includes']['users'][0]['name']
    ctx['base']['username'] = res['includes']['users'][0]['username']
    ctx['base']['text'] = res['data']['text']
    ctx['base']['id'] = res['data']['id']
    ctx['base']['date'] = trim_date(res['data']['created_at'])
    ctx['aux']['user_id'] = res['includes']['users'][0]['id']
    return ctx

def trim_date(date):
    rx = r".+?(?=T)"
    return re.search(rx, date).group(0)

def request_tweet(twt_id):
    url = f'https://api.twitter.com/2/tweets/{twt_id}'
    payload = {'tweet.fields': 'created_at,attachments', 'expansions': 'author_id'} #TODO agregar public_metrics
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    return requests.get(url, params=payload, headers=heads).json()

#TODO HACER UNA EXCEPTION SI EL TWEET ES MAS ANTIGUO QUE UNA SEMANA
def thread(request, id):
    user_id = tweet_ctx['aux']['user_id']
    res = request_thread(str(id), user_id)
    return render(request, 'threads/thread.html', fill_thread_context(tweet_ctx, compose_thread(res)))

def fill_thread_context(ctx, res):
    ctx['tweets'] = res['items']
    ctx['token'] = res['token']
    return ctx

def request_thread(conv_id, user_id, token=None):
    url = 'https://api.twitter.com/2/tweets/search/recent'
    payload = {'query': f'conversation_id:{conv_id} to:{user_id}', 'tweet.fields': 'conversation_id,referenced_tweets,entities', 'expansions': 'author_id,attachments.media_keys', 'user.fields': 'name,username'}
    if (token is not None):
        payload['next_token'] = token
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    return requests.get(url, params=payload, headers=heads).json()

#construimos un nuevo json iterando sobre la respuesta
def compose_thread(res):
    conjunto = list(zip(res['data'], res['includes']['users']))     #juntamos las dos listas
    merged = list(map(merge_tweet_data, conjunto))                  #creamos nueva lista con datos obtenidos al iterar sobre el conjunto
    filtrados = list(filter(None, merged))                          #filtro los None que quedaron en el medio
    try:
        token = res['meta']['next_token']
    except KeyError:
        token = False
    return {'token': token, 'items': filtrados}

#esto funciona porque el usuario en posicion n de la segunda lista corresponde al usuario en posicion n que creo el tweet en la primera
def merge_tweet_data(tupla):
    item = None
    if (tupla[0]['conversation_id'] == tupla[0]['referenced_tweets'][0]['id']):
        item = {
            'text': demention(tupla[0]['text'], tupla[0]['entities']),
            'id': tupla[0]['id'],
            'user_id': tupla[1]['id'],
            'username': tupla[1]['username'],
            'name': tupla[1]['name']
        }
    return item

#quita la mencion del texto
def demention(texto, ents):
    pos = ents['mentions'][0]['end'] + 1
    return texto[pos:]

#mas respuestas en un thread
def expand_thread(request):
    token = request.GET['token']
    conv_id = request.GET['conv_id']
    user_id = request.GET['user_id']
    # with open(BASE_DIR / 'threads/json_mocks/fake/no_token.json', encoding='utf-8') as mock:
    #     res = json.load(mock)
    res = request_thread(conv_id, user_id, token)
    res = compose_thread(res)
    return JsonResponse(res)

#el thread de una respuesta
def new_thread(request):
    pass
