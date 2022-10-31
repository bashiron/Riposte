class NoReplies(Exception):
    """Esta excepcion es lanzada cuando se intento cargar la conversacion de un tweet que no tiene respuestas.
    """

    def __init__(self):
        self.message = 'El tweet no tiene respuestas'
        super().__init__(self.message)

    def message(self):
        return self.message

    @staticmethod
    def web_name():
        """Representacion textual para identificar y parsear la excepcion.
        """
        return 'NoReplies'
