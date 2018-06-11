from bson import ObjectId
from bson.regex import Regex
from bson.tz_util import FixedOffset

class Movimentacoes():
    def __init__(self):
        self.query = {}
        self.projection = {}
        self.sort = []

    def set_query_id(self, con):
        if len(con) == 24:
            self.query["_id"] = ObjectId(con)

    def set_query_situacao_codigo(self, con):
        self.query["Situacao.Codigo"] = con

    def set_query_t(self, con):
        self.query["_t"] = Regex(u".*"+con+".*", "i")

    def set_query_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u"$gte": inicial.replace(tzinfo = FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo = FixedOffset(-180, "-0300"))
        }

    def set_query_convertida(self, con = False):
        if con == True:
            self.query["Convertida"] = True
        else:
            self.query["Convertida"] = False

    def set_query_fiscal(self, con):
        self.query["ItensBase.0.OperacaoFiscal"] = {
            u"$exists": True
        }
        if con == 'Saida':
            self.query["_t"] = {
                u"$not": Regex(u".*NotaFiscalCompra.*", "i")
            }

    def set_query_pessoa_id(self, con):
        self.query["Pessoa.PessoaReferencia"] = ObjectId(con)

    def set_projection_numero(self):
        self.projection["Numero"] = 1.0

    def set_projection_pessoa(self):
        self.projection["Pessoa"] = 1.0

    def set_projection_pessoa_nome(self):
        if "Pessoa" not in self.projection:
            self.projection["Pessoa.Nome"] = 1.0

    def set_projection_endereco(self):
        if "Pessoa" not in self.projection:
            self.projection["Pessoa.EnderecoPrincipal"] = 1.0

    def set_projection_empresa(self):
        self.projection["Empresa"] = 1.0

    def set_projection_itens(self):
        self.projection["ItensBase"] = 1.0

    def set_projection_emissao(self):
        self.projection["DataHoraEmissao"] = 1.0

    def set_projection_situacao(self):
        self.projection["Situacao"] = 1.0

    def set_sort_emissao(self, type='desc'):
        if type == 'asc':
            self.sort.append((u"DataHoraEmissao", 1))
        else:
            self.sort.append((u"DataHoraEmissao", -1))

    def unset_all(self):
        self.query = {}
        self.projection = {}
        self.sort = []

    def execute_all(self):
        from core.models import Uteis
        uteis = Uteis()
        busca = uteis.execute('Movimentacoes', self.query, projection=self.projection, sort=self.sort)
        self.unset_all()
        return busca

    def execute_one(self):
        from core.models import Uteis
        uteis = Uteis()
        busca = uteis.execute('Movimentacoes', self.query, projection=self.projection, sort=self.sort, limit=1)
        self.unset_all()
        return busca


    def get_clientes(self):
        from core.models import Uteis
        uteis = Uteis()
        database = uteis.conexao

        clientes = []
        query = {"Cliente": {u"$exists": True}}
        projection = {"_id":1.0, "Nome":1.0}
        cursor = database['Pessoas'].find(query, projection=projection)
        try:
            for cliente in cursor:
                cliente['id'] = str(cliente['_id'])
                clientes.append(cliente)
        finally:
            uteis.fecha_conexao()
        return clientes