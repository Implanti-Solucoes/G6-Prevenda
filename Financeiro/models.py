from bson import ObjectId, Regex
from core.models import Uteis
from bson.tz_util import FixedOffset
from django.db import models


class Financeiro:
    def __init__(self):
        self.sort = []
        self.unset_all()

    def unset_all(self):
        self.query = {}
        self.projection = {}
        self.limit = 250

    def set_query_id(self, con):
        if type(con) == str and len(con) == 24:
            self.query['_id'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['_id'] = con

    def set_query_pessoa_referencia(self, con):
        if type(con) == str and len(con) == 24:
            self.query['PessoaReferencia'] = ObjectId(con)
        elif type(con) == ObjectId:
            self.query['PessoaReferencia'] = con

    def set_query_ativo(self, con):
        self.query['Ativo'] = con

    def set_query_situacao(self, con):
        self.query['Situacao._t'] = con

    def set_query_situacao_codigo(self, con):
        self.query['Situacao.Codigo'] = con

    def set_query_vencimento(self, con):
        self.query['Vencimento'] = con

    def set_query_data_quitacao(self, con):
        self.query['DataQuitacao'] = con

    def set_query_vencimento_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u"$gte": inicial.replace(tzinfo=FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo=FixedOffset(-180, "-0300"))
        }

    def set_query_data_quitacao_periodo(self, inicial, final):
        self.query['DataHoraEmissao'] = {
            u"$gte": inicial.replace(tzinfo=FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo=FixedOffset(-180, "-0300"))
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
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        busca = Uteis().execute('Contas',
                                self.query,
                                projection=self.projection,
                                sort=self.sort)
        self.unset_all()
        return busca

    def get_centros_custos(self):
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        self.projection["Branches"] = 1.0
        self.projection["CodigoUnico"] = 1.0
        buscas = Uteis().execute('CentrosCusto', self.query, projection=self.projection, sort=self.sort)
        dados = []
        for busca in buscas:
            if len(busca['Branches']) > 0:
                dados.append(busca)
                dados.extend(self.branches(busca['Branches']))
            else:
                dados.append(busca)
        self.unset_all()
        return dados

    def branches(self, dados):
        branche = []
        for dado in dados:
            if len(dado['Branches']) > 0:
                branche.append(dado)
                branche.extend(self.branches(dado['Branches']))
            else:
                branche.append(dado)
        return branche

    def get_planos_conta(self):
        self.query["Ativo"] = True
        self.projection["_id"] = 1.0
        self.projection["Descricao"] = 1.0
        self.projection["Branches"] = 1.0
        self.projection["CodigoUnico"] = 1.0
        buscas = Uteis().execute('PlanosConta',
                                 self.query,
                                 projection=self.projection,
                                 sort=self.sort)
        dados = []
        for busca in buscas:
            if len(busca['Branches']) > 0:
                dados.append(busca)
                dados.extend(self.branches(busca['Branches']))
            else:
                dados.append(busca)
        self.unset_all()
        return dados

    def execute_all(self):
        busca = Uteis().execute('Recebimentos',
                                self.query,
                                projection=self.projection,
                                sort=self.sort,
                                limit=self.limit)
        self.unset_all()
        return busca

    def execute_one(self):
        busca = Uteis().execute('Recebimentos',
                                self.query,
                                projection=self.projection,
                                sort=self.sort,
                                limit=1)
        self.unset_all()
        return busca


class Contratos(models.Model):

    tipo = models.IntegerField()
    id_g6 = models.CharField('id da movimentacao', max_length=24)
    id_g6_cliente = models.CharField('id do cliente', max_length=24)
    excluido = models.BooleanField()
    motivo = models.CharField('Motivo do cancelamento', max_length=250)


class Parcelas(models.Model):

    orcamento = models.ForeignKey(Contratos, on_delete=models.CASCADE, related_name='parcelas')
    id_g6 = models.CharField('id da parcela', max_length=24)
