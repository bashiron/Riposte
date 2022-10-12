from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
import re
from .forms import LinkForm
from .utils.twitter_requests import R, M, Fetcher
from .utils.mock_provider import sequence
from datetime import datetime, timezone

tweet_ctx = {}

def home(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            tw_id = extract_id(form.cleaned_data['tw_link'])
            return process_request(request, form, tw_id)
    else:
        form = LinkForm()
    return render(request, 'threads/home.html', {'form': form, 'error': ''})

def extract_id(url):
    rx_url = r"^(?:[^\/]*\/){5}([^\/]*)"            #regex para links copiados de la barra de url
    rx_btn = r"^(?:[^\/]*\/){5}([^\/]*.+?(?=\?))"   #regex para links copiados con "copy link to tweet" (tienen un '?')
    return re.search(rx_btn if url.find('?') != -1 else rx_url, url).group(1)


def process_request(request, form, twid):
    mode = M    # definir si usar el modo real o mock
    root, recent = False, False
    global fetcher
    fetcher = Fetcher(mode)
    fetcher.set_mocks(sequence(['gen/tweet/t1', 'gen/thread/t2', 'gen/thread/t3', 'gen/thread/t4']))
    res = fetcher.obtain_tweet(twid)
    if mode == R:
        root, recent = eval_link(res, root)
    else:
        root, recent = True, True

    if root and recent:
        fill_tweet_context(tweet_ctx, res)
        response = HttpResponseRedirect(f'tweet/{twid}')
    if not root and recent:
        response = render(request, 'threads/home.html', {'form': form, 'error': 'el tweet insertado no es un tweet raiz'})
    if root and not recent:
        response = render(request, 'threads/home.html', {'form': form, 'error': 'el tweet insertado es mas antiguo que una semana'})
    if not (root or recent):
        response = render(request, 'threads/home.html', {'form': form, 'error': 'el tweet insertado no es un tweet raiz y ademas es mas antiguo que una semana'})
    return response

def eval_link(res, root):
    try:
        res['data']['in_reply_to_user_id']
    except KeyError:
        root = True
    recent = is_recent(res['data']['created_at'])
    return root, recent

def is_recent(raw_twt_date):
    twt_date = datetime.strptime(raw_twt_date, "%Y-%m-%dT%H:%M:%S.%fZ").astimezone(timezone.utc)
    now_date = datetime.now(timezone.utc)
    diff = now_date - twt_date
    return diff.days < 7

def tweet(request, twid):
    return render(request, 'threads/tweet.html', tweet_ctx)

def fill_tweet_context(ctx, res):
    urls = base_media(res['includes']['media'], res['data']['attachments']['media_keys'])
    ctx['name'] = res['includes']['users'][0]['name']
    ctx['username'] = res['includes']['users'][0]['username']
    ctx['text'] = res['data']['text']
    ctx['id'] = res['data']['id']
    ctx['date'] = trim_date(res['data']['created_at'])
    ctx['urls'] = urls
    ctx['url_count'] = len(urls)
    return ctx

def trim_date(date):
    rx = r".+?(?=T)"
    return re.search(rx, date).group(0)

def base_media(media, keys):
    return [m['url'] for m in media if m['type'] == 'photo' and m['media_key'] in keys]

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

# Ajax - colapsar niveles de thread
def collapse_thread(request):
    amount = int(request.GET['num'])
    fetcher.del_userids(amount)
    return HttpResponse(f'<borrados {amount} niveles>')
    # return HttpResponse('success')

