from database.distributore_DAO import DistributoreDAO
from database.DB_connect import DBConnect

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        # lista che conterrà le tuple (nome_distributore, prezzo_medio) richieste dal Controller
        risultato = []
        # controllo nel caso in cui il caricamento iniziale dal DB sia fallito
        if self._distributori is None:
            return risultato

        for distributore in self._distributori:
            # Sfrutto l'ORM: chiedo direttamente all'oggetto distributore i suoi prezzi
            prezzi = distributore.get_prezzi()
            if prezzi is not None:
                #list comprehension: estraggo solo il valore numerico (prezzo_litro)
                # dei giorni in cui il mese della data (oggetto datetime.date) coincide con quello scelto
                prezzi_mese = [p.prezzo_litro for p in prezzi if p.data.month == mese]
                # evito la divisione per zero (ZeroDivisionError) nel caso non ci siano dati per quel mese
                if len(prezzi_mese) > 0:
                    media = sum(prezzi_mese) / len(prezzi_mese)
                    # aggiungo la tupla nel formato atteso dalla View/Controller
                    risultato.append((distributore.nome, media))

        return risultato
        # TODO

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        # Resetto le variabili di stato prima di avviare una nuova ricerca ricorsiva
        # altrimenti rimarrebbero 'sporche' da esecuzioni precedenti
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        #preparo in anticipo i dati dei primi 7 giorni per non interrogare continuamente gli oggetti
        # durante i rami della ricorsione )
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        # Avvio la ricorsione partendo da
        # sequenza_parziale = [] (nessun distributore ancora scelto)
        # giorno = 1 (livello della ricorsione: partiamo dal 1 giorno)
        # ultimo_distributore = None (il primo giorno non c'è spostamento precedente)
        # costo_corrente = 0 (costo accumulato iniziale)
        # prezzi settimana = dizionario con i prezzi dei 7 giorni
        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        # Condizione terminale caso base: completati i 7 giorni (giorno arriva a 8)
        if giorno > 7:
            # se è la prima soluzione completa trovata  OPPURE
            # se il costo di questa sequenza è strettamente minore del miglior costo trovato finora:
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                # IMPORTANTE uso list(sequenza_parziale) per salvare una COPIA della lista
                # assegnassi direttamente sequenza_parziale, il backtracking successivo la svuoterebbe
                self.__sequenza_ottima = list(sequenza_parziale)
            return

        #esplora la scelta di ciascun distributore per il giorno corrente
        for id_distributore, lista_prezzi in prezzi_settimana.items():
            # costo carburante del giorno (100 litri * prezzo al litro; indice giorno-1)
            costo_giorno = lista_prezzi[giorno - 1] * 100

            # Costo fisso di 5€ se ci si sposta da un distributore all'altro
            if ultimo_distributore is not None and id_distributore != ultimo_distributore:
                costo_giorno += 5

            nuovo_costo = costo_corrente + costo_giorno

            # Pruning (filtro opzionale ma utile) procedi solo se non hai già superato il costo ottimo trovato
            if self.__costo_ottimo == -1 or nuovo_costo < self.__costo_ottimo:
                sequenza_parziale.append(id_distributore)
                self.__ricorsione(sequenza_parziale, giorno + 1, id_distributore, nuovo_costo, prezzi_settimana)
                sequenza_parziale.pop()  # Backtracking
        # TODO

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        prezzi_settimana = {}
        if self._distributori is None:
            return prezzi_settimana

        for distributore in self._distributori:
            prezzi = distributore.get_prezzi()
            if prezzi is not None:
                # Filtra i primi 7 giorni del mese e ordina per data crescente
                prezzi_filtrati = [
                    p for p in prezzi
                    if p.data.month == mese and 1 <= p.data.day <= 7
                ]
                prezzi_filtrati.sort(key=lambda p: p.data)
                prezzi_settimana[distributore.id] = [p.prezzo_litro for p in prezzi_filtrati]

        return prezzi_settimana
        #TODO

'''
ricordo utile:
1. ho usato list(sequenza_parziale) quando salvo __sequenza_ottima 
perché le liste sono oggetti mutabili passati per riferimento: 
senza creare una copia (list(...) o .copy()), le successive chiamate a .pop() del backtracking 
cancellerebbero anche la soluzione migliore salvata

2. perché __costo_ottimo parte da -1? 
È un valore sentinella: siccome i costi sono sempre positivi
-1 indica che non è ancora stata completata nessuna sequenza valida 
e che la prima soluzione che arriva a giorno > 7 diventerà l'ottimo iniziale

3. complessità della ricorsione
con 2 distributori e 7 giorni, senza potatura (pruning) l'algoritmo esplora 2^7 = 128 foglie
il controllo nuovo_costo < self.__costo_ottimo taglia subito i rami 
che già a metà settimana costano più della migliore soluzione intera trovata finora
'''