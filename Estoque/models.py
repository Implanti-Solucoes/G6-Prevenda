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
        uteis = Uteis()
        database = uteis.conexao

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
            uteis.fecha_conexao()
            return True

    @staticmethod
    def list():
        # Importe Uteis para criar conexao com mongo
        uteis = Uteis()
        database = uteis.conexao

        # Declarando collection que deve ser consultado
        collection = database["TabelasPreco"]

        # Declarando vetor para retorno de dados
        retorno: List[Any] = []

        # Definindo filtros
        query = {}

        cursor = collection.find(query)
        try:
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                doc['Operacao']['t'] = doc['Operacao']['_t']
                del doc['Operacao']['_t']
                del doc['_id']
                if doc['Operacao']['BaseCalculoTabelaPreco'] == 0:
                    doc['Operacao']['BaseCalculoTabelaPrecoEx'] = 'Venda'
                elif doc['Operacao']['BaseCalculoTabelaPreco'] == 1:
                    doc['Operacao']['BaseCalculoTabelaPrecoEx'] = 'Custo'
                retorno.append(doc)
        finally:
            uteis.fecha_conexao()
            return retorno

    @staticmethod
    def get(id):
        # Importe Uteis para criar conexao com mongo
        uteis = Uteis()
        database = uteis.conexao

        # Declarando collection que deve ser consultado
        collection = database["TabelasPreco"]

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
            uteis.fecha_conexao()
            return e

        finally:
            # Caso der tudo certo, feche a conexao e retorne os dados
            uteis.fecha_conexao()
            return retorno


class Products:
    def list(self):
        # Importe Uteis para criar conexao com mongo
        uteis = Uteis()
        database = uteis.conexao

        # Declarando collection que deve ser consultado
        collection = database['ProdutosServicosEmpresa']

        # Declarando vetor para retorno de dados
        retorno: List[Any] = []

        # Pipeline para dar aggregate
        pipeline = [
            {
                u'$lookup': {
                    u'from': u'ProdutosServicos',
                    u'localField': u'ProdutoServicoReferencia',
                    u'foreignField': u'_id',
                    u'as': u'ProdutoServico'
                }
            },
            {
                u'$lookup': {
                    u'from': u'Precos',
                    u'localField': u'PrecoReferencia',
                    u'foreignField': u'_id',
                    u'as': u'Precos'
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
                del doc['_id']
                retorno.append(doc)
        finally:
            uteis.fecha_conexao()
            return retorno

    def get_precos(self, id):
        # Importe Uteis para criar conexao com mongo
        uteis = Uteis()
        database = uteis.conexao

        # Setando coletion que vai ser consultado
        collection = database["Precos"]

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
                retorno.append(doc)
        finally:
            uteis.fecha_conexao()
            return retorno
