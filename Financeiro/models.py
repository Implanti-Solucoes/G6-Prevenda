from core.models import Uteis
from bson.tz_util import FixedOffset

class Pessoas:
    def __init__(self):
        self.uteis = Uteis()

    def get_pessoa(self, id):
        self.database = self.uteis.conexao
        query = {'_id': id}
        pessoa = self.database['Pessoas'].find_one(query)
        self.uteis.fecha_conexao()
        return pessoa

    def get_nome(self, id):
        pessoa = self.get_pessoa(id)
        return pessoa['Nome']

    def get_emitente(self):
        self.database = self.uteis.conexao
        query = {'_t.2': u'Emitente'}
        emitente = self.database['Pessoas'].find_one(query)
        self.uteis.fecha_conexao()
        return emitente

    def get_nome_emitente(self):
        emitente = self.get_emitente()
        return emitente['Nome']

    def get_cnpj_emitente(self):
        emitente = self.get_emitente()
        return emitente['Cnpj']

    def get_saldo_devedor(self, id):
        self.database = self.uteis.conexao
        total_devedor = 0

        query = {}
        query["Situacao._t"] = {
            u"$ne": u"Quitada"
        }
        query["PessoaReferencia"] = id

        projection = {"Historico": 1.0}

        cursor = self.database["Recebimentos"].find(query, projection=projection)
        try:
            for doc in cursor:
                total_devedor = total_devedor + doc['Historico'][0]['Valor']
        finally:
            self.uteis.fecha_conexao()
        return total_devedor

    def get_saldo_devedor_extenso(self, id):
        saldo_devedor = self.get_saldo_devedor(id)
        extenso = self.uteis.num_to_currency(saldo_devedor)
        return extenso

class Parcelas:
    def __init__(self):
        self.uteis = Uteis()

        self.query = {}
        self.projection = {}
        self.sort = []

    def unset_all(self):
        self.query = {}
        self.projection = {}
        self.sort = []

    def set_query_id(self, con):
        self.query['_id'] = con

    def set_query_situacao(self, con):
        self.query['Situacao._t'] = con

    def set_query_vencimento(self, con):
        self.query['Vencimento'] = con

    def set_query_data_quitacao(self, con):
        self.query['DataQuitacao'] = con

    def set_query_vencimento_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u"$gte": inicial.replace(tzinfo = FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo = FixedOffset(-180, "-0300"))
        }

    def set_query_data_quitacao_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u"$gte": inicial.replace(tzinfo = FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo = FixedOffset(-180, "-0300"))
        }

    def set_sort_vencimento(self, con='desc'):
        if con == 'asc':
            self.sort.append((u"Vencimento", 1))
        else:
            self.sort.append((u"Vencimento", -1))

    def set_sort_data_quitacao(self, con='desc'):
        if con == 'asc':
            self.sort.append((u"DataQuitacao", 1))
        else:
            self.sort.append((u"DataQuitacao", -1))

    def execute_all(self, limit=500):
        database = self.uteis.conexao
        busca = []

        if self.sort == {}:
            cursor = database['Recebimentos'].find(self.query).limit(500)
        else:
            cursor = database['Recebimentos'].find(self.query, sort=self.sort).limit(500)

        try:
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                busca.append(doc)
        finally:
            self.unset_all()
            self.uteis.fecha_conexao

        return busca

    def execute_one(self):
        from core.models import Uteis
        uteis = Uteis()
        database = uteis.conexao

        if self.sort == {}:
            cursor = database['Recebimentos'].find_one(self.query)
        else:
            cursor = database['Recebimentos'].find_one(self.query, sort=self.sort)

        uteis.fecha_conexao()
        return cursor

