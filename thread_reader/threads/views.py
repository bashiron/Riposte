from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
import re
from .forms import LinkForm
from .twitter_requests import R, M, Fetcher
from .mock_provider import sequence

tweet_ctx = {'aux': {}}
fetcher = Fetcher(M)    # definir si usar el modo real o mock

def home(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            tw_id = extract_id(form.cleaned_data['tw_link'])
            return HttpResponseRedirect(f'tweet/{tw_id}')
    else:
        form = LinkForm()
    return render(request, 'threads/home.html', {'form': form})

def extract_id(url):
    rx_url = r"^(?:[^\/]*\/){5}([^\/]*)"            #regex para links copiados de la barra de url
    rx_btn = r"^(?:[^\/]*\/){5}([^\/]*.+?(?=\?))"   #regex para links copiados con "copy link to tweet" (tienen un '?')
    return re.search(rx_btn if url.find('?') != -1 else rx_url, url).group(1)

def tweet(request, twid):
    fetcher.set_mocks(sequence(['tweet/fake/long_word',  'thread/fake/long_username', 'thread/real/japanese', 'thread/fake/weird_chars', 'thread/fake/end']))
    res = fetcher.obtain_tweet(str(twid))
    return render(request, 'threads/tweet.html', fill_tweet_context(tweet_ctx, res))

def fill_tweet_context(ctx, res):
    ctx['name'] = res['includes']['users'][0]['name']
    ctx['username'] = res['includes']['users'][0]['username']
    ctx['text'] = res['data']['text']
    ctx['id'] = res['data']['id']
    ctx['date'] = trim_date(res['data']['created_at'])
    ctx['aux']['user_id'] = res['includes']['users'][0]['id']
    return ctx

def trim_date(date):
    rx = r".+?(?=T)"
    return re.search(rx, date).group(0)

# Ajax - el thread de una respuesta
def new_thread(request):
    twid = request.GET['twid']
    res = fetcher.obtain_thread(twid)
    return JsonResponse(res)

# Ajax - mas respuestas en un thread
def expand_thread(request):
    token = request.GET['token']
    twid = request.GET['twid']
    res = fetcher.obtain_thread(twid, token)
    return JsonResponse(res)

