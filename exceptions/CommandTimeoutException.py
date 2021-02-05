class CommandTimeoutException(Exception):
    def __init__(self):
        super().__init__("***Tempo de espera excedido, favor recomeçar***")
