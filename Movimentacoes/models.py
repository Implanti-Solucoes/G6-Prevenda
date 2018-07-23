from bson import ObjectId
from bson.regex import Regex
from core.models import Uteis

class Movimentacoes():
    def __init__(self):
        self.query = {}
        self.projection = {}
        self.sort = []
        self.limit = 500
        self.uteis = Uteis()

    def set_query_id(self, con):
        if len(con) == 24:
            self.query['_id'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['_id'] = con

    def set_query_situacao_codigo(self, con):
        self.query['Situacao.Codigo'] = con

    def set_query_t(self, con, and_or):
        if and_or == 'and':
            if '$and' not in self.query:
                self.query['$and'] = {}

            self.query['$and'].append({'_t': Regex(u'.*'+con+'.*', 'i')})

        elif and_or == 'or':
            if '$or' not in self.query:
                self.query['$or'] = []

            self.query['$or'].append({'_t': Regex(u'.*' + con + '.*', 'i')})

        elif '$and' in self.query or '$or' in self.query:
            print('É necessario definir modo de operação and ou or')
            return False

        else:
            self.query['_t'] = Regex(u'.*' + con + '.*', 'i')

    def set_query_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u'$gte': inicial,
            u'$lt': final
        }

    def set_query_convertida(self, con = False):
        if con == True:
            self.query['Convertida'] = True
        else:
            self.query['Convertida'] = False

    def set_query_fiscal(self, con):
        if '_t' not in self.query:
            self.query['_t'] = Regex(u'.*DocumentoFiscalEletronico.*', 'i')
        elif '$and' not in self.query:
            self.query['$and'] = [{'_t': Regex(u'.*DocumentoFiscalEletronico.*', 'i')}]
        else:
            self.query['$and'].append({'_t': Regex(u'.*DocumentoFiscalEletronico.*', 'i')})

        if con == 'Saida':
            if '$and' not in self.query:
                self.query['$and'] = [
                    {
                        u'_t': {
                            u'$not': Regex(u'.*NotaFiscalEletronicaEntrada.*', 'i')
                        }
                    },
                    {
                        u'_t': {
                            u'$not': Regex(u'.*NotaFiscalCompra.*', 'i')
                        }
                    }
                ]
            else:
                self.query['$and'].append(
                    {
                        u'_t': {
                            u'$not': Regex(u'.*NotaFiscalEletronicaEntrada.*', 'i')
                        }
                    },
                    {
                        u'_t': {
                            u'$not': Regex(u'.*NotaFiscalCompra.*', 'i')
                        }
                    }
                )


    def set_query_pessoa_id(self, con):
        if len(con) == 24:
            self.query['Pessoa.PessoaReferencia'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['Pessoa.PessoaReferencia'] = con

    def set_query_vendedor_id(self, con):
        if len(con) == 24:
            self.query['Vendedor.PessoaReferencia'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['Vendedor.PessoaReferencia'] = con

    def set_projection_numero(self):
        self.projection['Numero'] = 1.0

    def set_projection_pessoa(self):
        self.projection['Pessoa'] = 1.0

    def set_projection_pessoa_nome(self):
        if 'Pessoa' not in self.projection:
            self.projection['Pessoa.Nome'] = 1.0

    def set_projection_endereco(self):
        if 'Pessoa' not in self.projection:
            self.projection['Pessoa.EnderecoPrincipal'] = 1.0

    def set_projection_empresa(self):
        self.projection['Empresa'] = 1.0

    def set_projection_itens(self):
        self.projection['ItensBase'] = 1.0

    def set_projection_emissao(self):
        self.projection['DataHoraEmissao'] = 1.0

    def set_projection_situacao(self):
        self.projection['Situacao'] = 1.0

    def set_sort_emissao(self, type='desc'):
        if type == 'asc':
            self.sort.append((u'DataHoraEmissao', 1))
        else:
            self.sort.append((u'DataHoraEmissao', -1))

    def set_limit(self, limit):
        self.limit = limit

    def unset_all(self):
        self.query = {}
        self.projection = {}
        self.sort = []
        self.limit = 500

    def execute_all(self):
        busca = self.uteis.execute('Movimentacoes',
                              self.query,
                              projection=self.projection,
                              sort=self.sort,
                              limit=self.limit)
        self.unset_all()
        return busca

    def execute_one(self):
        busca = self.uteis.execute('Movimentacoes', self.query, projection=self.projection, sort=self.sort, limit=1)
        self.unset_all()
        return busca

    def get_vendedores(self):
        database = self.uteis.conexao

        vendedores = []
        query = {'Vendedor': {u'$exists': True}}
        projection = {'_id': 1.0, 'Nome': 1.0}
        cursor = database['Pessoas'].find(query, projection=projection)

        try:
            for vendedor in cursor:
                vendedor['id'] = str(vendedor['_id'])
                vendedores.append(vendedor)
        finally:
            self.uteis.fecha_conexao()

        return vendedores

    def get_clientes(self):
        database = self.uteis.conexao

        clientes = []
        query = {'Cliente': {u'$exists': True}}
        projection = {'_id': 1.0, 'Nome': 1.0}
        cursor = database['Pessoas'].find(query, projection=projection, sort=[('Nome', 1)])
        try:
            for cliente in cursor:
                cliente['id'] = str(cliente['_id'])
                clientes.append(cliente)
        finally:
            self.uteis.fecha_conexao()
        return clientes

    def edit_status_aprovado(self, id):
        database = self.uteis.conexao
        Aprovado = {
            '_t': [
                'SituacaoMovimentacao',
                'Aprovado'
            ],
            'Codigo': 8,
            'Descricao': 'Aprovado',
            'Cor': '#006400',
            'DescricaoComando': 'Tornar pendente'
        }
        try:
            database['Movimentacoes'].find_one_and_update({'_id': ObjectId(id)},
                                                          {'$set': {'Situacao': Aprovado}})
        finally:
            self.uteis.fecha_conexao()