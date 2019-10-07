import base64
from bson import ObjectId
from django.db import models
from core.models import Uteis
from bson.int64 import Int64
import clr
import io
clr.AddReference(
    R'C:\DigiSat\SuiteG6\Sistema\DigisatServer.Infrastructure.Crosscutting.dll'
)


class MesasConta(models.Model):
    mesa = models.IntegerField('mesa', default=0)
    conta = models.IntegerField('conta', default=0)
    total = models.FloatField('Total', default=0.0)
    dinheiro = models.FloatField('Dinheiro', default=0.0)
    cartao_credito = models.FloatField('Cartão credito', default=0.0)
    cartao_debito = models.FloatField('Cartão debito', default=0.0)
    outros = models.FloatField('Outros', default=0.0)


class ItensMesaContaMongo(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__query__ = {}
        self.__projection__ = {}
        self.__sort__ = []
        self.__limit__ = 250
        self.__aggregate_garcom_referencia__ = False

    def set_query_id(self, data):
        if type(data) == str and len(data) == 24:
            self.__query__['_id'] = ObjectId(data)
        elif type(data) == ObjectId:
            self.__query__['_id'] = data

    def set_query_situacao(self, data: int):
        self.__query__['Situacao'] = Int64(data)

    def set_query_cancelado(self, data: bool = False):
        self.__query__['Cancelado'] = data

    def set_query_numero_mesa(self, data: int):
        self.__query__[u"NumeroMesa"] = data

    def set_query_numero_mesa_conta(self, data: int):
        self.__query__[u"NumeroMesaConta"] = data

    def set_sort_data_hora(self, data: str = '1'):
        if data == 'asc' or data == '1':
            self.__sort__.append([u"DataHora", 1])
        if data == 'desc' or data == '2':
            self.__sort__.append([u"DataHora", -1])

    def set_sort_numero_mesa(self, data: str = '1'):
        if data == 'asc' or data == '1':
            self.__sort__.append([u"NumeroMesa", 1])
        if data == 'desc' or data == '2':
            self.__sort__.append([u"NumeroMesa", -1])

    def set_sort_numero_mesa_conta(self, data: str = '1'):
        if data == 'asc' or data == '1':
            self.__sort__.append([u"NumeroMesaConta", 1])
        if data == 'desc' or data == '2':
            self.__sort__.append([u"NumeroMesaConta", -1])

    def set_aggregate_garcom(self):
        self.__aggregate_garcom_referencia__ = True

    def fechar_mesa(self, data: ObjectId):
        uteis = Uteis()
        database = uteis.conexao
        collection = database["ItensMesaConta"]
        collection.update_one(
            {'_id': data}, {
                '$set': {
                    'Situacao': 3,
                    'ContaEmitida': True
                }
            })
        uteis.fecha_conexao()

    def execute_all(self):
        dados = []
        uteis = Uteis()
        if self.__aggregate_garcom_referencia__ is False:
            cursor = uteis.execute(
                tabela='ItensMesaConta',
                query=self.__query__,
                projection=self.__projection__,
                sort=self.__sort__,
                limit=self.__limit__
            )
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                dados.append(doc)
            return dados
        else:
            database = uteis.conexao
            collection = database["ItensMesaConta"]
            pipeline = []
            if self.__query__ != {}:
                pipeline.append({
                    u"$match": self.__query__
                })
            pipeline.append({
                u"$lookup": {
                    u"from": u"Pessoas",
                    u"localField": u"GarcomReferencia",
                    u"foreignField": u"_id",
                    u"as": u"GarcomReferencia"
                }
            })
            cursor = collection.aggregate(
                pipeline,
                allowDiskUse=False
            )
            try:
                for doc in cursor:
                    doc['id'] = str(doc['_id'])
                    dados.append(doc)
                return dados
            finally:
                uteis.fecha_conexao()

    class Meta:
        default_permissions = (
            'index',
            'mesa_conta',
            'get_add_item_mesa',
            'set_add_item_mesa',
            'fechar_conta',
        )

    id_g6 = models.CharField('ID do produto', max_length=24)
    produto = models.CharField('Nome do produto', max_length=100)
    cancelado = models.BooleanField(default=False)
    id_garcom = models.CharField('ID do Garcom', max_length=24, blank=True)
    garcom_nome = models.CharField('Garcom', max_length=100, blank=True)
    percent_comissao = models.FloatField(
        'Percentual da comissao', default=0.0, blank=True)
    comissao = models.FloatField('Comissao', default=0.0)
    unidade_medida = models.CharField('Unidade de medida', max_length=10)
    quantidade = models.FloatField('Quantidade', default=0.0)
    unitario = models.FloatField('Unitario', default=0.0)
    total = models.FloatField('Total', default=0.0)
    mesa_conta = models.ForeignKey(
        MesasConta, on_delete=models.CASCADE, related_name='itens')


class CardapiosMongo:
    def __init__(self):
        super().__init__()
        self.__query__ = {}
        self.__projection__ = {}
        self.__sort__ = []
        self.__limit__ = 250
        self.__pipeline__ = []

    def set_query_id(self, data):
        if type(data) == str and len(data) == 24:
            self.__query__['_id'] = ObjectId(data)
        elif type(data) == ObjectId:
            self.__query__['_id'] = data

    def set_aggregate_produto_empresa_referencia(self):
        self.__unwind_itens_cardapio__()
        self.__pipeline__.append(
            {u"$lookup": {
                u"from": u"ProdutosServicosEmpresa",
                u"localField": u"ItensCardapio.ProdutoEmpresaReferencia",
                u"foreignField": u"_id",
                u"as": u"ItensCardapio.ProdutoEmpresaReferencia"
            }}
        )

    def aggregate_produto_servico_referencia(self):
        self.set_aggregate_produto_empresa_referencia()
        self.__pipeline__.append({
            u"$lookup": {
                u"from": u"ProdutosServicos",
                u"localField": u"ItensCardapio.ProdutoEmpresaReferencia.0.ProdutoServicoReferencia",
                u"foreignField": u"_id",
                u"as": u"ItensCardapio.ProdutoServico"
            }}
        )

    def __unwind_itens_cardapio__(self):
        self.__pipeline__.append({u"$unwind": {
            u"path": u"$ItensCardapio",
            u"includeArrayIndex": u"arrayIndex",
            u"preserveNullAndEmptyArrays": False
        }})

    def group_itens_cardapio(self):
        self.__pipeline__.append({
            u"$group": {
                u"_id": u"$_id",
                u"_t": {
                    u"$first": u"$_t"
                },
                u"InformacoesPesquisa": {
                    u"$first": u"$InformacoesPesquisa"
                },
                u"ItensCardapio": {
                    u"$push": u"$ItensCardapio"
                },
                u"Versao": {
                    u"$first": u"$Versao"
                },
                u"Ativo": {
                    u"$first": u"$Ativo"
                },
                u"EmpresaReferencia": {
                    u"$first": u"$EmpresaReferencia"
                },
                u"Descricao": {
                    u"$first": u"$Descricao"
                },
                u"ImpressoraReferencia": {
                    u"$first": u"$ImpressoraReferencia"
                },
                u"Imagem": {
                    u"$first": u"$Imagem"
                },
                u"MostrarOnline": {
                    u"$first": u"$MostrarOnline"
                }
            }}
        )

    def execute_all(self):
        from DigisatServer.Infrastructure.Crosscutting.Helper import \
            HelperImage

        dados = []
        class_imported1 = HelperImage
        uteis = Uteis()
        if len(self.__pipeline__) == 0:
            cursor = uteis.execute(
                tabela='Cardapios',
                query=self.__query__,
                projection=self.__projection__,
                sort=self.__sort__,
                limit=self.__limit__
            )
            for doc in cursor:
                byte_image = io.BytesIO(
                    bytearray(class_imported1.Decompress(doc['Imagem']))
                )
                doc['Imagem'] = base64.b64encode(byte_image.getvalue())
                doc['Imagem'] = doc['Imagem'].decode("utf-8")
                dados.append(doc)
            return dados
        else:
            database = uteis.conexao
            collection = database["Cardapios"]
            cursor = collection.aggregate(
                self.__pipeline__,
                allowDiskUse=False
            )
            try:
                for doc in cursor:
                    doc['id'] = str(doc['_id'])
                    byte_image = io.BytesIO(
                        bytearray(class_imported1.Decompress(doc['Imagem']))
                    )
                    doc['Imagem'] = base64.b64encode(byte_image.getvalue())
                    doc['Imagem'] = doc['Imagem'].decode("utf-8")
                    x = 0
                    for item in doc['ItensCardapio']:
                        doc['ItensCardapio'][x]['ProdutoEmpresaReferencia'][0]['id'] = \
                            str(doc['ItensCardapio'][x]['ProdutoEmpresaReferencia'][0]['_id'])
                        doc['ItensCardapio'][x]['ProdutoServico'][0]['id'] = \
                            str(doc['ItensCardapio'][x]['ProdutoServico'][0]['_id'])
                        byte_image = io.BytesIO(
                            bytearray(
                                class_imported1.Decompress(
                                    doc['ItensCardapio'][x]['ProdutoServico'][0]['Imagem']
                                )
                            )
                        )
                        doc['ItensCardapio'][x]['ProdutoServico'][0]['Imagem']\
                            = base64.b64encode(byte_image.getvalue())
                        doc['ItensCardapio'][x]['ProdutoServico'][0]['Imagem']\
                            = doc['ItensCardapio'][x]['ProdutoServico'][0]['Imagem'].decode("utf-8")
                        x += 1
                    dados.append(doc)
            finally:
                uteis.fecha_conexao()
                return dados

