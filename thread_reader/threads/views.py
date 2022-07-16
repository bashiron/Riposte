from urllib import response
from wsgiref import headers
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests, os, json, re
import environ
from .forms import LinkForm
from pdb import set_trace

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

def extractId(url):
    return re.search(r"\d{19}", url).group()

def thread(request, id):
    heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
    res = requests.get('https://api.twitter.com/2/tweets/', params={'ids': str(id)}, headers=heads)
    # set_trace()
    return render(request, 'threads/thread.html', {'response': res})