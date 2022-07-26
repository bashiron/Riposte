from multiprocessing import context
from urllib import response
from wsgiref import headers
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
import requests, os, json, re
import environ
from .forms import LinkForm

env = environ.Env()
tweet_ctx = {'base': {}}

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
    url = f'https://api.twitter.com/2/tweets/{str(id)}'
    payload = {'tweet.fields': 'created_at,attachments', 'expansions': 'author_id'} #TODO agregar public_metrics
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    res = requests.get(url, params=payload, headers=heads).json()
    return render(request, 'threads/tweet.html', fill_tweet_context(tweet_ctx, res))


def fill_tweet_context(ctx, res):
    ctx['base']['name'] = res['includes']['users'][0]['name']
    ctx['base']['username'] = res['includes']['users'][0]['username']
    ctx['base']['text'] = res['data']['text']
    ctx['base']['id'] = res['data']['id']
    ctx['base']['date'] = trim_date(res['data']['created_at'])
    return ctx


def trim_date(date):
    rx = r".+?(?=T)"
    return re.search(rx, date).group(0)

#TODO HACER UNA EXCEPTION SI EL TWEET ES MAS ANTIGUO QUE UNA SEMANA
#TODO AGREGAR EL "TO:" AL QUERY PARA QUE SOLO HAYAN RESPUESTAS DIRECTAS AL TWEET ORIGINAL
def thread(request, id):
    url = 'https://api.twitter.com/2/tweets/search/recent'
    payload = {'query': f'conversation_id:{str(id)}', 'expansions': 'author_id,attachments.media_keys', 'user.fields': 'name,username'}
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    res = requests.get(url, params=payload, headers=heads).json()
    return render(request, 'threads/thread.html', fill_thread_context(tweet_ctx, res))

def fill_thread_context(ctx, res):
    ctx['tweets'] = res['data']
    ctx['token'] = res['meta']['next_token']
    return ctx


#mas respuestas en un thread
def expand_thread(request):
    token = request.GET['token']
    conv_id = request.GET['conv_id']
    url = 'https://api.twitter.com/2/tweets/search/recent'
    payload = {'query': f'conversation_id:{conv_id}', 'expansions': 'author_id,attachments.media_keys', 'user.fields': 'name,username', 'next_token': token}
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    res = requests.get(url, params=payload, headers=heads).json()
    return JsonResponse(res)


#el thread de una respuesta
def new_thread(request):
    pass