from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests, os, json
import environ
from .forms import LinkForm

env = environ.Env()

def home(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            tw_id = extractId(form.cleaned_data)
            return HttpResponseRedirect(f'thread/{tw_id}')
    else:
        form = LinkForm()

    return render(request, 'threads/home.html', {'form': form})

def extractId(url):
    #<extraer el id del url usando regex>
    return 0

def thread(request):
    #<Traer thread de la API y cargarlo en el context>
    context = {}
    return render(request, 'threads/thread.html', context)