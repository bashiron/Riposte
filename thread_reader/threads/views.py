from multiprocessing import context
from urllib import response
from wsgiref import headers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import requests, os, json, re
import environ
from .forms import LinkForm

env = environ.Env()

def home(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            tw_id = extractId(form.cleaned_data['tw_link'])
            return HttpResponseRedirect(f'thread/{tw_id}')
    else:
        form = LinkForm()

    return render(request, 'threads/home.html', {'form': form})

# links para probar:
# https://twitter.com/VideoArtGame/status/1548668846050988032
# https://twitter.com/VideoArtGame/status/1548668846050988032?s=20&t=ddJrMfddkleybcG2dZqU-g

def extractId(url):
    rx_url = r"^(?:[^\/]*\/){5}([^\/]*)"            #regex para links copiados de la barra de url
    rx_btn = r"^(?:[^\/]*\/){5}([^\/]*.+?(?=\?))"   #regex para links copiados con "copy link to tweet" (tienen un '?')
    return re.search(rx_btn if url.find('?') != -1 else rx_url, url).group(1)

def thread(request, id):
    url = f'https://api.twitter.com/2/tweets/{str(id)}'
    payload = {'tweet.fields': 'created_at,attachments', 'expansions': 'author_id'}
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    res = requests.get(url, params=payload, headers=heads).json()
    return render(request, 'threads/thread.html', fillContext({}, res))

def fillContext(ctx, res):
    ctx['name'] = res['includes']['users'][0]['name']
    ctx['username'] = res['includes']['users'][0]['username']
    ctx['text'] = res['data']['text']
    ctx['id'] = res['data']['id']
    ctx['date'] = trimDate(res['data']['created_at'])
    return ctx

def trimDate(date):
    rx = r".+?(?=T)"
    return re.search(rx, date).group(0)
