from typing import List, Any
from core.models import Uteis
from bson import ObjectId


class Tabela_Preco:
    # Esse metodo cria uma nova tabela de preço
    # name = Vai recebe o nome da tabela de preço
    # t = Vai receber o tipo de alteração que pode ser 0 = Acrescimo ou 1 = Desconto
    # percen = Vai receber a porcentagem que vai afetar o preço
    ## Caso o t seja desconto 'percen' não pode ser menor ou igual a 0
    ## 'percen' não pode ser maior 999.9999
    # base: Esse atributo vai informar qual a base a ser utilizada no calculo, sendo possivel
    # 0 = Preço de venda e 1 = Preço de custo
    @staticmethod
    def create(situacao, name, t, percen, base):
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Declarando lista para validação de bases
        bases = [0, 1]

        # Validando nome para não ser vazio
        if name == '':
            print("Falha de validação do 'name'")
            return False

        # Validando o atributo 't' e 'percen'
        if t == 0 and 0 < percen <= 999.9999:
            t = 'Acrescimo'
        elif t == 1 and 0 < percen < 100:
            t = 'Desconto'
        else:
            print("Falha de validação do 't' e 'percen'")
            return False

        # Validando as situações possiveis
        if situacao == 1:
            situacao = True
        elif situacao == 0:
            situacao = False
        else:
            print("Falha de validação da 'situacao'")
            return False

        # Validando a base informada nas 'bases' possiveis
        if base not in bases:
            print("Falha de validação da 'bases'")
            return False

        model = {
            '_t': 'TabelaPreco',
            'InformacoesPesquisa': name.split(' '),
            'Versao': '736926.15:47:54.5365034',
            'Ativo': situacao,
            'Descricao': name,
            'Operacao': {
                '_t': t,
                'Percentual': percen,
                'BaseCalculoTabelaPreco': base
            },
            'Itens': [

            ]
        }
        try:
            insert = database['TabelasPreco'].insert(model)
        finally:
            Uteis().fecha_conexao()
            return True

    @staticmethod
    def list():
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Declarando collection que deve ser consultado
        collection = database['TabelasPreco']

        # Declarando vetor para retorno de dados
        retorno: List[Any] = []

        # Definindo filtros
        query = {}

        cursor = collection.find(query)
        try:
            for doc in cursor:
                # Adicionando campos personalizados
                doc['id'] = str(doc['_id'])
                doc['Operacao']['t'] = doc['Operacao']['_t']

                # Caso o sistema esteja desatualizado so trabalha
                # em cima do preço de venda
                if 'BaseCalculoTabelaPreco' in doc['Operacao']:
                    if doc['Operacao']['BaseCalculoTabelaPreco'] == 0:
                        doc['Operacao']['BaseCalculoTabelaPrecoEx'] = 'Venda'
                    elif doc['Operacao']['BaseCalculoTabelaPreco'] == 1:
                        doc['Operacao']['BaseCalculoTabelaPrecoEx'] = 'Custo'
                else:
                    doc['Operacao']['BaseCalculoTabelaPrecoEx'] = 'Venda'
                retorno.append(doc)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get(id):
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Declarando collection que deve ser consultado
        collection = database["TabelasPreco"]

        # Variavel de retorno vazio caso necessario
        retorno = []

        # Fazendo busca e retornando dados
        try:
            # Verificando se o ID veio como String ou ObjectId e tratando
            if type(id) == str and len(id) == 24:
                retorno = collection.find_one({'_id': ObjectId(id)})
                retorno['id'] = str(retorno['_id'])
            elif type(id) == ObjectId:
                retorno = collection.find_one({'_id': id})
                retorno['id'] = str(retorno['_id'])
        except Exception as e:
            # Se der qualquer erro, feche a conexao e retorne o erro
            Uteis().fecha_conexao()
            return e

        finally:
            # Caso der tudo certo, feche a conexao e retorne os dados
            Uteis().fecha_conexao()
            return retorno


class Products:
    def __init__(self):
        self.__query__ = {}
        self.__projection__ = {}
        self.__sort__ = []
        self.__limit__ = 250

        self.__collection__ = 'ProdutosServicos'
        self.__aggregate_pre__ = False  # Precos
        self.__aggregate_estoq__ = False  # Quantidades
        self.__aggregate_pro_ser__ = False  # Produtos e Servicos
        self.__aggregate_pro_emp__ = False  # Produtos e Empresa

    @staticmethod
    def list():
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Declarando collection que deve ser consultado
        collection = database['ProdutosServicosEmpresa']

        # Declarando vetor para retorno de dados
        retorno: List[Any] = []

        # Pipeline para dar aggregate
        pipeline = [
            {
                u"$lookup": {
                    u"from": u"Precos",
                    u"localField": u"PrecoReferencia",
                    u"foreignField": u"_id",
                    u"as": u"Precos"
                }
            },
            {
                u"$lookup": {
                    u"from": u"ProdutosServicos",
                    u"localField": u"ProdutoServicoReferencia",
                    u"foreignField": u"_id",
                    u"as": u"ProdutoServico"
                }
            },
            {
                u"$lookup": {
                    u"from": u"Estoques",
                    u"localField": u"EstoqueReferencia",
                    u"foreignField": u"_id",
                    u"as": u"Estoques"
                }
            }
        ]

        cursor = collection.aggregate(
            pipeline,
            allowDiskUse=False
        )

        try:
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                doc['Precos'][0]['id'] = str(doc['Precos'][0]['_id'])
                doc['Estoques'][0]['id'] = str(doc['Estoques'][0]['_id'])
                doc['ProdutoServico'][0]['id'] = str(
                    doc['ProdutoServico'][0]['_id'])
                retorno.append(doc)
        finally:
            Uteis().fecha_conexao()
            return retorno

    def get_full_product(self, id):
        if type(id) == str and len(id) == 24:
            pass
        elif type(id) == ObjectId:
            pass
        else:
            return []

        retorno = {'empresa': self.get_produto_empresa(id)}
        retorno['preco'] = self.get_preco(
            retorno['empresa'][0]['PrecoReferencia'])
        retorno['estoque'] = self.get_estoque(
            retorno['empresa'][0]['EstoqueReferencia'])
        retorno['produto'] = self.get_produto_servico(
            retorno['empresa'][0]['ProdutoServicoReferencia'])

        return retorno

    @staticmethod
    def get_preco(id):
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['Precos']

        # Declarando variavel de filtros
        query = {}
        retorno = []

        try:
            if type(id) == str and len(id) == 24:
                query['_id'] = ObjectId(id)
            elif type(id) == ObjectId:
                query['_id'] = id

            cursor = collection.find(query)

            for doc in cursor:
                doc['id'] = str(doc['_id'])
                retorno.append(doc)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get_servicos():
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['ProdutosServicos']

        # Declarando variavel de filtros
        query = {'TipoItem.Codigo': 9}
        retorno = []

        try:
            for x in collection.find(query):
                retorno.append(x)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get_produtos():
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['ProdutosServicos']

        # Declarando variavel de filtros
        query = {'TipoItem.Codigo': 0}
        retorno = []

        try:
            for x in collection.find(query):
                retorno.append(x)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get_estoque(id):
        if type(id) == str and len(id) == 24:
            query = {'_id': ObjectId(id)}
        elif type(id) == ObjectId:
            query = {'_id': id}
        else:
            return []

        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['Estoques']

        # Declarando variavel de retorno
        retorno = []

        try:
            ok = collection.find_one(query)
            ok['id'] = str(ok['_id'])
            retorno.append(ok)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get_produto_servico(id=None, ms=None):
        if type(id) == str and len(id) == 24:
            query = {'_id': ObjectId(id)}
        elif type(id) == ObjectId:
            query = {'_id': id}
        elif ms is not None and len(str(ms)) == 13:
            query = {'RegistroMinisterioSaude': str(ms)}
        else:
            return []
        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['ProdutosServicos']

        # Declarando variavel de retorno
        retorno = []

        try:
            ok = collection.find_one(query)
            ok['id'] = str(ok['_id'])
            retorno.append(ok)
        finally:
            Uteis().fecha_conexao()
            return retorno

    @staticmethod
    def get_produto_empresa(id):
        if type(id) == str and len(id) == 24:
            query = {'_id': ObjectId(id)}
        elif type(id) == ObjectId:
            query = {'_id': id}
        else:
            return []

        # Importe Uteis para criar conexao com mongo
        database = Uteis().conexao

        # Setando coletion que vai ser consultado
        collection = database['ProdutosServicosEmpresa']

        # Declarando variavel de retorno
        retorno = []

        try:
            for x in collection.find(query):
                x['id'] = str(x['_id'])
                retorno.append(x)
        finally:
            Uteis().fecha_conexao()
            return retorno

    def set_query_id(self, data):
        if type(data) == str and len(data) == 24:
            self.__query__['_id'] = ObjectId(data)
        elif type(data) == ObjectId:
            self.__query__['_id'] = data

    def set_collection(self, data: str = '1'):
        if data == '1' or data == 'ProdutosServicos':
            self.__collection__ = 'ProdutosServicos'

        if data == '2' or data == 'ProdutosServicosEmpresa':
            self.__collection__ = 'ProdutosServicosEmpresa'

    def set_aggregate_produtos_servicos(self):
        self.__aggregate_pro_ser__ = True

    def set_aggregate_produtos_servicos_empresa(self):
        self.__aggregate_pro_emp__ = True

    def set_aggregate_precos(self):
        self.__aggregate_pre__ = True

    def set_aggregate_quantidades(self):
        self.__aggregate_estoq__ = True

    def execute_all(self):
        dados = []
        uteis = Uteis()
        database = uteis.conexao
        pipeline = []
        if self.__aggregate_estoq__ is True or \
                self.__aggregate_pre__ is True or self.__aggregate_pro_emp__ \
                is True or self.__aggregate_pro_ser__ is True:
            if len(self.__query__) > 0:
                pipeline.append({
                    u"$match": self.__query__
                })

        if self.__aggregate_estoq__ is True or \
                self.__aggregate_pre__ is True or self.__aggregate_pro_emp__ \
                is True:
            if 'ProdutosServicos' == self.__collection__:
                pipeline.append(
                    {
                        u"$lookup": {
                            u"from": u"ProdutosServicosEmpresa",
                            u"localField": u"_id",
                            u"foreignField": u"ProdutoServicoReferencia",
                            u"as": u"ProdutosServicosEmpresa"
                        }
                    }
                )

        if self.__aggregate_pro_ser__ is True and \
                'ProdutosServicosEmpresa' == self.__collection__:
            pipeline.append(
                {
                    u"$lookup": {
                        u"from": u"ProdutosServicos",
                        u"localField": u"ProdutoServicoReferencia",
                        u"foreignField": u"_id",
                        u"as": u"ProdutosServicos"
                    }
                }
            )

        if self.__aggregate_estoq__ is True:
            pipeline.append(
                {
                    u"$lookup": {
                        u"from": u"Estoques",
                        u"localField": u"ProdutosServicosEmpresa.0.EstoqueReferencia" if 'ProdutosServicos' == self.__collection__ else u"EstoqueReferencia",
                        u"foreignField": u"_id",
                        u"as": u"Estoques"
                    }
                }
            )

        if self.__aggregate_pre__ is True:
            pipeline.append(
                {
                    u"$lookup": {
                        u"from": u"Precos",
                        u"localField": u"ProdutosServicosEmpresa.0.PrecoReferencia" if 'ProdutosServicos' == self.__collection__ else u"PrecoReferencia",
                        u"foreignField": u"_id",
                        u"as": u"Precos"
                    }
                }
            )

        collection = database[self.__collection__]
        if len(pipeline) > 0:
            cursor = collection.aggregate(
                pipeline,
                allowDiskUse=False
            )
            try:
                for doc in cursor:
                    doc['id'] = str(doc['_id'])
                    dados.append(doc)
            finally:
                uteis.fecha_conexao()
                return dados
