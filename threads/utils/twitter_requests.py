from queue import Queue, LifoQueue

import environ
import requests

from .mention_parser import rm_auto_mentions

M = 'mock'
R = 'real'
env = environ.Env()

class Fetcher:
    """Provee metodos para interactuar con algunos endpoints del api de Twitter.

    Attributes:
    ----------
    mode : ``str``
       Modo de operacion del Fetcher, M (mock) o R (real)
    tweet : ``dict``
       Tweet base falso a ser provisto.
    thread : ``Queue``
       Cola de threads falsos a ser provistos en orden FIFO (primero en entrar primero en salir).
    user_stack : ``LifoQueue``
       Cola de usuarios que aumenta en profundidad a medida que se abren threads nuevos, registra los nombres de usuario
       en una cola LIFO (ultimo en entrar primero en salir) para poder limpiar el texto del tweet de las menciones
       autogeneradas.
    """

    def __init__(self, mode):
        self.mode = mode
        self.tweet = None
        self.thread = Queue()
        self.user_stack = LifoQueue()

    def set_mocks(self, mocks):
        """Define los datos falsos a ser provistos por el Fetcher.
        """
        self.tweet, *thr = mocks   #descompongo la lista en las dos variables
        for t in thr:
            self.thread.put(t)

    def del_userids(self, num):
        """Borra ``num`` niveles de la pila de usuarios.
        """
        for i in range(num):
            self.user_stack.get()

    def obtain_tweet(self, twt_id):
        """Obtiene los datos procesados de un tweet que coincida con el id.

        Parameters
        ----------
        twt_id : `str`
            Id del tweet a conseguir.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        if self.mode is M:
            res = self.tweet
        else:
            res = self.request_tweet(twt_id)
        return res

    def request_tweet(self, twt_id):
        """Trae de la API, en formato json, los datos crudos de un tweet que coincida con el id.

        Parameters
        ----------
        twt_id : `str`
            Id del tweet a conseguir.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        url = f'https://api.twitter.com/2/tweets/{twt_id}'
        payload = self.tweet_payload()
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()

    def tweet_payload(self):
        return {
            'tweet.fields': 'created_at,attachments,conversation_id,entities,public_metrics',
            'expansions': 'author_id,attachments.media_keys,in_reply_to_user_id',
            'media.fields': 'url'
        }

    def obtain_thread(self, twid, token=None):
        """Obtiene los datos procesados del thread de un tweet que coincida con el id.

        Parameters
        ----------
        twid : `str`
            Id del tweet.
        token : `str`
            Token para pedir la siguiente pagina de respuestas.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        if self.mode is M:
            res = self.thread.get()
        else:
            res = self.request_thread(twid, token)
        if token is None:
            self.user_stack.put(res['data'][0]['in_reply_to_user_id'])
        return self.__compose_thread(res)

    def request_thread(self, twid, token):
        """Trae de la API, en formato json, los datos crudos del thread de un tweet que coincida con el id.

        Parameters
        ----------
        twid : `str`
            Id del tweet.
        token : `str`
            Token para pedir la siguiente pagina de respuestas.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        url = 'https://api.twitter.com/2/tweets/search/recent'
        payload = self.thread_payload(twid)
        if token is not None:
            payload['next_token'] = token
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()

    def thread_payload(self, twid):
        return {
            'query': f'in_reply_to_tweet_id: {twid}',
            'tweet.fields': 'entities,attachments,public_metrics',
            'expansions': 'author_id,attachments.media_keys,in_reply_to_user_id',
            'media.fields': 'url',
            'user.fields': 'name,username',
            # 'sort_order': 'relevancy'
            'sort_order': 'recency'
            }

    def __compose_thread(self, res):
        """Construye un diccionario iterando sobre la respuesta, el cual esta creado para ser parseado en javascript
        y eventualmente convertido en `HTML`.

        Parameters
        ----------
        res : `dict`
            Datos en formato json.

        Returns
        -------
        res : `dict`
            Diccionario de dos valores donde el primero es el siguiente token (si es que hay) y el segundo es la lista
            con los datos de cada tweet procesados.

        Notes
        -----
        1. Se empieza por definir ``media`` accediendo al ``includes``
        2. Luego se crea un conjunto donde `zipeamos` los datos mas relevantes de cada tweet en el thread, para poder
        procesarlos por separado en ``merge_tweet_data``
        3. Procesamos cada item del conjunto haciendo `map`
        4. Definimos el ``token`` accediendo al ``meta``
        """
        try:
            media = res['includes']['media']
        except KeyError:    # si no tiene es una lista vacia
            media = []

        conjunto = self.__zip_data(res['data'], res['includes']['users'], media, res['meta']['result_count'])
        merged = list(map(self.__merge_tweet_data, conjunto))  # creamos nueva lista con datos obtenidos al iterar sobre el conjunto

        try:
            token = res['meta']['next_token']
        except KeyError:    # si no tiene es False
            token = False

        return {'token': token, 'items': merged}

    def __zip_data(self, data, users, media, count):
        """Recibe las tres listas de objetos de la conversacion y retorna una lista de tuplas triples donde cada una
        contiene los objetos asociados a un tweet para poder ser procesados por separado.

        Parameters
        ----------
        data : `list`
            Datos basicos de un tweet/respuesta.
        users : `list`
            Usuarios involucrados en la conversacion.
        media : `list`
            Informacion sobre archivos multimedia incluidos.
        count : `int`
            Cantidad de tweets.

        Returns
        -------
        conjunto : `list`
            Lista de tuplas triples.
        """
        conjunto = []
        for n in range(count):
            datos = data[n]
            usuario = [user for user in users if user['id'] == datos['author_id']][0]  # el [0] es para tomar el primero y unico item de la lista generada
            urls = self.__get_urls(data[n]['attachments']['media_keys'], media) if ('attachments' in datos) else []     # se recolectan los urls, excepto que no haya attachments
            conjunto.append((datos, usuario, urls))
        return conjunto

    def __get_urls(self, keys, media):
        """Recolecta los urls del multimedia de un tweet, restringido a imagenes.
        """
        return [m['url'] for m in media if (m['media_key'] in keys) and m['type'] == 'photo']

    def __merge_tweet_data(self, tupla):
        """Procesa una tupla (triple) de datos de tweet para su posterior parseo en javascript.

        Parameters
        ----------
        tupla : `tuple`
            Tupla triple de datos referentes a un tweet. Con [0] se accede a los datos basicos, con [1] a los datos de
            usuario y con [2] a los urls.

        Returns
        -------
        objeto : `dict`
            Objeto que contiene los datos relevantes asociados a un tweet/respuesta, compuesto para facilidad de acceso.
        """
        try:
            mentions = tupla[0]['entities']['mentions']
        except KeyError:
            mentions = []
        return {
                'text': rm_auto_mentions(tupla[0]['text'], mentions, set(self.user_stack.queue)),
                'id': tupla[0]['id'],
                'user_id': tupla[1]['id'],
                'username': tupla[1]['username'],
                'name': tupla[1]['name'],
                'urls': tupla[2],
                'metrics': {
                    'likes': tupla[0]['public_metrics']['like_count'],
                    'replies': tupla[0]['public_metrics']['reply_count'],
                    'retweets': tupla[0]['public_metrics']['retweet_count']
                }
            }

    def custom_request_tweet(self, twt_id, payload):
        """Trae datos crudos de tweet de la API, aceptando un payload personalizado.

        Parameters
        ----------
        twt_id : `str`
            Id del tweet a conseguir.
        payload : `dict`
            Payload personalizado para usar en el pedido.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        url = f'https://api.twitter.com/2/tweets/{twt_id}'
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()

    def custom_request_thread(self, payload):
        """Trae datos crudos del thread de un tweet de la API, aceptando un payload personalizado.

        Parameters
        ----------
        payload : `dict`
            Payload personalizado para usar en el pedido, el cual incluye el id del tweet.

        Returns
        -------
        res : `dict`
            Datos en formato json.
        """
        url = 'https://api.twitter.com/2/tweets/search/recent'
        heads = {'Authorization': f'Bearer { env("BEARER_TOKEN") }'}
        return requests.get(url, params=payload, headers=heads).json()
