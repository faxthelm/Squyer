class TournamentTypeException(Exception):
    def __init__(self,  *args):
        super().__init__("***Os tipos de torneio disponíveis são \"Premium\" ou \"Principal\"***")
