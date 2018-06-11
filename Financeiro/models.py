from bson import ObjectId, Regex

from core.models import Uteis
from bson.tz_util import FixedOffset

class Pessoas:
    def __init__(self):
        self.uteis = Uteis()

    def get_pessoa(self, id):
        if len(id) == 24:
            self.database = self.uteis.conexao
            query = {'_id': id}
            pessoa = self.database['Pessoas'].find_one(query)
            self.uteis.fecha_conexao()
        return pessoa

    def get_nome(self, id):
        if len(id) == 24:
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
        if len(id) == 24:
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
        if len(id) == 24:
            saldo_devedor = self.get_saldo_devedor(id)
            extenso = self.uteis.num_to_currency(saldo_devedor)
            return extenso

class Financeiro:
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
        if len(id) == 24:
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

    def get_contas(self):
        uteis = Uteis()
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        busca = uteis.execute('Contas', self.query, projection=self.projection, sort=self.sort)
        self.unset_all()
        return busca

    def get_centros_custos(self):
        uteis = Uteis()
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        self.projection["Branches"] = 1.0
        self.projection["CodigoUnico"] = 1.0
        buscas = uteis.execute('CentrosCusto', self.query, projection=self.projection, sort=self.sort)
        x = 0
        for busca in buscas:
            i = 0
            for branches in busca['Branches']:
                buscas[x]['Branches'][i]['id'] = str(buscas[x]['Branches'][i]['_id'])
                i = i + 1
            x = x + 1
        self.unset_all()
        return buscas

    def get_codigo_unico_centros_custos(self, id):
        uteis = Uteis()
        database = uteis.conexao
        self.query["_id"] = ObjectId(id)
        if database['CentrosCusto'].count(self.query) == 1:
            cursor = database['CentrosCusto'].find_one(self.query)
            self.unset_all()
            return cursor

        self.query["Branches"] = Regex(u".*"+id+".*", "i")
        if database['CentrosCusto'].count(self.query) == 1:
            cursor = database['CentrosCusto'].find_one(self.query)
            print(id)
            self.unset_all()
            return cursor["Branches"]


    def get_planos_conta(self):
        uteis = Uteis()
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        self.projection["Branches"] = 1.0
        self.projection["CodigoUnico"] = 1.0
        buscas = uteis.execute('PlanosConta', self.query, projection=self.projection, sort=self.sort)
        x = 0
        for busca in buscas:
            i = 0
            for branches in busca['Branches']:
                buscas[x]['Branches'][i]['id'] = str(buscas[x]['Branches'][i]['_id'])
                i = i + 1
            x = x + 1

        self.unset_all()
        return buscas

    def execute_all(self):
        uteis = Uteis()
        busca = uteis.execute('Recebimentos', self.query, projection=self.projection, sort=self.sort)
        self.unset_all()
        return busca

    def execute_one(self):
        uteis = Uteis()
        busca = uteis.execute('Recebimentos', self.query, projection=self.projection, sort=self.sort, limit=1)
        self.unset_all()
        return busca

    def create_parcela(self):
        pass
