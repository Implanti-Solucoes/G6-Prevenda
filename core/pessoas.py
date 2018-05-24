from pymongo import MongoClient
from pymongo.cursor import Cursor

from .uteis import Uteis
class Pessoas():
    def __init__(self):
        print('ok')

    def Cliente(self, id):
        database = Uteis.Conexao(self)
        query = {'_id': id}
        cliente = database['Pessoas'].find_one(query)
        return cliente

    def NomeCliente(self, id):
        cliente = self.Cliente(id)
        return cliente['Nome']

    def Emitente(self):
        database = Uteis.Conexao()
        query = {}
        query['_t.2'] = u'Emitente'
        Emitente = database['Pessoas'].find_one(query)
        return Emitente

    def NomeEmitente(self):
        emitente = self.Emitente()
        return emitente['Nome']

    def CnpjEmitente(self):
        emitente = self.Emitente()
        return emitente['Cnpj']

    def SaldoDevedor(self, id):
        database = Uteis.Conexao(self)
        total_devedor = 0

        query = {}
        query["Situacao._t"] = {
            u"$ne": u"Quitada"
        }
        query["PessoaReferencia"] = id

        projection = {"Historico": 1.0}

        cursor: Cursor = database["Recebimentos"].find(query, projection=projection)
        for doc in cursor:
            total_devedor = total_devedor + doc['Historico'][0]['Valor']

        return total_devedor

    def SaldoDevedorExtenso(self, id):
        saldo_devedor = self.SaldoDevedor(id)
        return Uteis.numToCurrency(saldo_devedor)