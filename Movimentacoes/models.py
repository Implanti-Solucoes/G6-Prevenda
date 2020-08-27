from bson import ObjectId
from bson.regex import Regex
from Pessoas.models import PessoasMongo
from core.models import Uteis


class Movimentacoes:
    def __init__(self):
        self.query = {}
        self.projection = {}
        self.sort = []
        self.limit = 100
        self.uteis = Uteis()
        self.set_query_agrregate_receitas = False
        self.__pipeline__ = []

    @staticmethod
    def set_query_agrregate_receitas_base():
        pipeline = {
                u"$lookup": {
                    u"from": u"Receitas",
                    u"localField": u"_id",
                    u"foreignField": u"MovimentacaoReferencia",
                    u"as": u"Receitas"
                }
            }
        return pipeline

    def set_query_id(self, con):
        if type(con) == str and len(con) == 24:
            self.query['_id'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['_id'] = con

    def set_query_situacao_codigo(self, con, ne=0):
        self.query['Situacao.Codigo'] = con
        if ne != 0:
            self.query['Situacao.Codigo'] = {
                u"$ne": con
            }

    def set_query_t(self, con, and_or=''):
        if and_or == 'and':
            if '$and' not in self.query:
                self.query['$and'] = {}

            self.query['$and'].append({'_t': Regex(u'.*' + con + '.*', 'i')})

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

    def set_query_convertida(self, con=False):
        if con:
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

    def set_projection_id(self):
        self.projection['_id'] = 1.0

    def set_projection_numero(self):
        self.projection['Numero'] = 1.0

    def set_projection_t(self):
        self.projection['_t'] = 1.0

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
        self.limit = 100

    def execute_all(self):
        if self.set_query_agrregate_receitas is False:
            busca = self.uteis.execute(
                'Movimentacoes',
                self.query,
                projection=self.projection,
                sort=self.sort,
                limit=self.limit
            )
            self.unset_all()
            return busca
        else:
            if len(self.query) > 0:
                self.__pipeline__.append({
                    u"$match": self.query
                })
            self.__pipeline__.append(self.set_query_agrregate_receitas_base())
            conexao = self.uteis.conexao
            collection = conexao['Movimentacoes']
            cursor = collection.aggregate(
                self.__pipeline__,
                allowDiskUse=False
            )
            items = []
            try:
                for doc in cursor:
                    items.append(doc)
            finally:
                self.uteis.fecha_conexao()
                return items

    def execute_one(self):
        busca = self.uteis.execute('Movimentacoes', self.query, projection=self.projection, sort=self.sort, limit=1)
        self.unset_all()
        if busca is not None:
            if 'Pessoa' in busca:
                if busca['Pessoa']['_t'] == 'FisicaHistorico':
                    busca['Pessoa']['tipo'] = 'CPF'
                    busca['Pessoa']['Documento'] = '%s.%s.%s-%s' % (
                        busca['Pessoa']['Documento'][0:3],
                        busca['Pessoa']['Documento'][3:6],
                        busca['Pessoa']['Documento'][6:9],
                        busca['Pessoa']['Documento'][9:11]
                    )
                elif busca['Pessoa']['_t'] == 'EmpresaHistorico':
                    busca['Pessoa']['tipo'] = 'CNPJ'
                    busca['Pessoa']['Documento'] = '%s.%s.%s/%s-%s' % (
                        busca['Pessoa']['Documento'][0:2],
                        busca['Pessoa']['Documento'][2:5],
                        busca['Pessoa']['Documento'][5:8],
                        busca['Pessoa']['Documento'][8:12],
                        busca['Pessoa']['Documento'][12:14]
                    )

            if 'Empresa' in busca:
                busca['Empresa']['tipo'] = 'CNPJ'
                busca['Empresa']['Documento'] = '%s.%s.%s/%s-%s' % (
                    busca['Empresa']['Documento'][0:2],
                    busca['Empresa']['Documento'][2:5],
                    busca['Empresa']['Documento'][5:8],
                    busca['Empresa']['Documento'][8:12],
                    busca['Empresa']['Documento'][12:14]
                )
        return busca

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

    # Metodo feito para inserir informações de controle
    @staticmethod
    def informacoes_controle(busca):
        items = []
        for doc in busca:
            if 'PreVenda' in doc['_t']:
                doc['PreVenda'] = 1
            elif 'NotaFiscalServico' in doc['_t']:
                doc['NotaFiscalServico'] = 1
            elif 'DocumentoAuxiliarVenda' in doc['_t']:
                doc['DocumentoAuxiliarVenda'] = 1
            elif 'DocumentoAuxiliarVendaOrdemServico' in doc['_t']:
                doc['DocumentoAuxiliarVendaOrdemServico'] = 1

            if 'Documento' in doc['Pessoa']:
                if len(doc['Pessoa']['Documento']) == 14:
                    doc['Pessoa']['Tipo'] = 'CPF'
                else:
                    doc['Pessoa']['Tipo'] = 'CNPJ'
            items.append(doc)
        return items

    # Configurando o cadastro do cliente para ser inserido na movimentação
    @staticmethod
    def pessoas_movimentacao(id_cliente):
        cursor = PessoasMongo()
        cursor.set_query_id(id_cliente)
        pessoa: list = cursor.execute_all()
        if len(pessoa) > 0:
            return False
        cliente: dict = pessoa[0]

        pessoa_dict = {}
        if 'Fisica' in cliente['_t']:
            pessoa_dict['_t'] = 'FisicaHistorico'
            if 'Cpf' in cliente:
                pessoa_dict['Documento'] = cliente['Cpf']
            else:
                print("Você precisa coloca CPF no cliente")

            if 'Rg' in cliente:
                pessoa_dict['Rg'] = cliente['Rg']
                if 'Uf' in pessoa_dict['Rg']:
                    pessoa_dict['Rg']['Uf']['_t'] = cliente['Rg']
                else:
                    pessoa_dict['Rg']['Uf'] = None

                if 'OrgaoEmissor' not in pessoa_dict['Rg']:
                    pessoa_dict['Rg']['OrgaoEmissor'] = None

            if 'Numero' in cliente['Carteira']['Ie']:
                pessoa_dict['Ie'] = cliente['Carteira']['Ie']['Numero']

            pessoa_dict['Cliente'] = {'LimiteCredito': cliente['LimiteCredito']}

        elif 'Emitente' in cliente['_t']:
            pessoa_dict['_t'] = 'EmpresaHistorico'
            if 'Cnpj' in cliente:
                pessoa_dict['Documento'] = cliente['Cnpj']
            else:
                print("Você precisa coloca CNPJ no cliente")

            pessoa_dict['Ie'] = cliente['Carteira']['Ie']['Numero']

        elif 'Juridica' in cliente['_t']:
            pessoa_dict['_t'] = 'JuridicaHistorico'
            if 'Cnpj' in cliente:
                pessoa_dict['Documento'] = cliente['Cnpj']
            else:
                print("Você precisa coloca CNPJ no cliente")

            if 'Numero' in cliente['Carteira']['Ie']:
                pessoa_dict['Ie'] = cliente['Carteira']['Ie']['Numero']

        elif len(cliente['_t']) and cliente['_t'][0] == 'Pessoa' and cliente['_t'][1] == 'Consumidor':
            pessoa_dict['_t'] = 'ConsumidorHistorico'
            pessoa_dict['Cliente'] = {'LimiteCredito': 0.0}

        pessoa_dict['PessoaReferencia'] = cliente['_id']
        pessoa_dict['Nome'] = cliente['Nome']
        pessoa_dict['Classificacao'] = cliente['Classificacao']

        if 'TelefonePrincipal' in cliente:
            pessoa_dict['TelefonePrincipal'] = cliente['TelefonePrincipal']['Numero']

        # Configurando o endereço do cliente
        pessoa_dict['EnderecoPrincipal'] = cliente['Carteira']['EnderecoPrincipal']
        del pessoa_dict['EnderecoPrincipal']['_t']
        del pessoa_dict['EnderecoPrincipal']['InformacoesPesquisa']

        if pessoa_dict['Classificacao']['_t'] == 'NaoContribuinte':
            pessoa_dict['IndicadorOperacaoConsumidorFinal'] = {
                '_t': 'ConsumidorFinal',
                'Codigo': 1,
                'Descricao': 'Consumidor final'
            }
            pessoa_dict['IndicadorIeDestinatario'] = {
                '_t': 'NaoContribuinte'
            }

        else:
            pessoa_dict['IndicadorOperacaoConsumidorFinal'] = {
                '_t': 'Normal',
                'Codigo': 0,
                'Descricao': 'Normal'
            }
            pessoa_dict['IndicadorIeDestinatario'] = {
                '_t': 'ContribuinteIcms'
            }

        pessoa_dict['InformacoesPesquisa'] = cliente['InformacoesPesquisa']
        return pessoa_dict
