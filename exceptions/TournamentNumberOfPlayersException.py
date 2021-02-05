class TournamentNumberOfPlayersException(Exception):
    def __init__(self,  *args):
        super().__init__("***Somente é possível criar torneios de 2, 4, 8, 16, 32 jogadores***")
