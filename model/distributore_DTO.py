from dataclasses import dataclass
from database.prezzo_DAO import PrezzoDAO

'''
    DTO (Data Transfer Object) dell'entità Distributore
'''

@dataclass()
class Distributore:
    id: int
    nome: str
    indirizzo: str

    # RELAZIONI
    # prima è None: non carichiamo subito tutti i 365 prezzi per ogni distributore
    # quando creiamo l'oggetto, per evitare query inutili al database...approccio Lazy Loading
    lista_prezzi: list = None

    def get_prezzi(self):
        """ Aggiorna e Restituisce la lista di prezzi (self.lista_prezzi) associati al distributore"""
        # controllo se i prezzi per questo distributore non sono ancora stati scaricati dal DB
        if self.lista_prezzi is None:
            # chiamo il DAO passando l'id del distributore corrente (self.id) per ottenere
            #la lista di oggetti Prezzo associati e la salvo nell'attributo dell'istanza.
            #Cosi, se chiamerò get_prezzi() una seconda volta, i dati saranno già in memoria
            # senza dover interrogare nuovamente MySQL
            self.lista_prezzi = PrezzoDAO.get_prezzi(self.id)
        return self.lista_prezzi
        # TODO

    def __eq__(self, other):
        return isinstance(other, Distributore) and self.id == other.id

    def __str__(self):
        return f"{self.id} | {self.nome} | Indirizzo: {self.indirizzo}"

    def __repr__(self):
        return f"{self.id} | {self.nome} | Indirizzo: {self.indirizzo}"
