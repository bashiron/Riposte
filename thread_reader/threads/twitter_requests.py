import requests, environ

M = 'mock'
R = 'real'
env = environ.Env()

class Fetcher:
    """Provee metodos para interactuar con algunos endpoints del api de Twitter.
    """

    def __init__(self, mode):
        self.mode = mode
        self.tweet = None
        self.thread = []
        self.conv = None

    def set_mocks(self, mocks):
        self.tweet, *self.thread = mocks   #descompongo la lista en las dos variables

    def set_conv_id(self, conv):
        self.conv = conv

    def obtain_tweet(self, twt_id):
        if self.mode is M:
            res = self.tweet
        else:
            res = self.__request_tweet(twt_id)
        return res

    def __request_tweet(self, twt_id):
        url = f'https://api.twitter.com/2/tweets/{twt_id}'
        payload = {'tweet.fields': 'created_at,attachments,conversation_id', 'expansions': 'author_id'}  #TODO agregar public_metrics
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()

    def obtain_thread(self, user_id, twid, token=None):
        if self.mode is M:
            res = self.thread.pop(0)
        else:
            res = self.__request_thread(user_id, token)
        return self.__compose_thread(res, twid)

    def __request_thread(self, user_id, token):
        url = 'https://api.twitter.com/2/tweets/search/recent'
        payload = {'query': f'conversation_id:{self.conv} to:{user_id}', 'tweet.fields': 'referenced_tweets,entities', 'expansions': 'author_id,attachments.media_keys', 'user.fields': 'name,username'}
        # payload = {'query': f'conversation_id:{self.conv} to:{user_id}', 'tweet.fields': 'referenced_tweets,entities', 'expansions': 'author_id,attachments.media_keys', 'user.fields': 'name,username', 'sort_order': 'relevancy'}
        if token is not None:
            payload['next_token'] = token
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()

    # construimos un nuevo json iterando sobre la respuesta
    def __compose_thread(self, res, twid):
        print('RECIBIDOS: ' + str(len(res['data'])))
        conjunto = list(zip(res['data'], res['includes']['users']))             #juntamos las dos listas
        merged = list(map(lambda c: self.__merge_tweet_data(c, twid), conjunto))  #creamos nueva lista con datos obtenidos al iterar sobre el conjunto. el lambda es para poder enviar un argumento ademas de la lista
        filtrados = list(filter(None, merged))                                  #filtro los None que quedaron en el medio
        try:
            token = res['meta']['next_token']
        except KeyError:
            token = False
        return {'token': token, 'items': filtrados}

    # esto funciona porque el usuario en posicion n de la segunda lista corresponde al usuario en posicion n que creo el tweet en la primera
    def __merge_tweet_data(self, tupla, twid):
        item = None
        condition = (twid == tupla[0]['referenced_tweets'][0]['id']) if self.mode is R else True
        if condition:
            item = {
                'text': self.__demention(tupla[0]['text'], tupla[0]['entities']),
                'id': tupla[0]['id'],
                'user_id': tupla[1]['id'],
                'username': tupla[1]['username'],
                'name': tupla[1]['name']
            }
        return item

    # quita la mencion del texto
    def __demention(self, texto, ents):
        pos = ents['mentions'][0]['end'] + 1
        return texto[pos:]
