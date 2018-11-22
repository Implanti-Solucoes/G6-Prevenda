# Create your models here.
from datetime import datetime, timedelta
from pymongo import errors
from math import ceil
from core.models import Uteis
from bson import ObjectId
from django.db import models
from bson.tz_util import FixedOffset


class PessoasMongo:
    def get_pessoa(self, id, atrasados=False):
        database = Uteis().conexao
        if type(id) == str and len(id) == 24:
            query = {'_id': ObjectId(id)}
        elif type(id) == ObjectId:
            query = {'_id': id}
        else:
            return []

        pessoa = database['Pessoas'].find_one(query)
        pessoa['devedor'] = self.get_saldo_devedor(id=pessoa['_id'], database=database, atrasado=atrasados)
        pessoa['devedor'] = pessoa['devedor']['total_devedor'] + pessoa['devedor']['juro'] + pessoa['devedor']['multa']
        Uteis().fecha_conexao()
        return pessoa

    def get_nome(self, id):
        pessoa = self.get_pessoa(id)
        if 'Nome' in pessoa:
            return pessoa['Nome']
        return []

    @staticmethod
    def get_emitente():
        database = Uteis().conexao
        query = {'_t.2': u'Emitente'}
        emitente = database['Pessoas'].find_one(query)
        emitente['id'] = str(emitente['_id'])
        Uteis().fecha_conexao()
        return emitente

    def get_clientes(self, atrasados=False):
        database = Uteis().conexao
        query = {'Cliente': {u'$exists': True}}
        collection = database['Pessoas']

        # Limitando a quantidade buscada para evitar erro
        clientes_count = collection.count()
        limit = 100
        page = ceil(clientes_count / limit)
        p = 0

        # Resetando conexão
        Uteis().fecha_conexao()
        clients_list = []
        while p < page:
            dados = []
            try:
                database = Uteis().conexao
                collection = database['Pessoas']
                clientes = collection.find(query, skip=(p * limit), limit=limit)
                for x in clientes:
                    x['id'] = str(x['_id'])
                    x['devedor'] = self.get_saldo_devedor(x['_id'], database=database, atrasado=atrasados)
                    x['devedor'] = x['devedor']['total_devedor'] + x['devedor']['juro'] + x['devedor']['multa']
                    dados.append(x)
            except:
                print("Entrei foi nesse aki")
            finally:
                p += 1
                Uteis().fecha_conexao()
                clients_list.extend(dados)
        return clients_list

    def get_nome_emitente(self):
        emitente = self.get_emitente()
        return emitente['Nome']

    def get_cnpj_emitente(self):
        emitente = self.get_emitente()
        return emitente['Cnpj']

    @staticmethod
    def get_saldo_devedor(id, database=None, atrasado=False):
        from Financeiro.models import Financeiro
        if type(id) == str and len(id) == 24:
            id = ObjectId(id)
        elif type(id) == ObjectId:
            pass
        else:
            return False

        if database is None:
            database = Uteis().conexao

        total_devedor = {'total_devedor': 0, 'juro': 0, 'multa': 0}

        query = {
            'Situacao._t': u'Pendente',
            'PessoaReferencia': id,
            'Ativo': True
        }
        if atrasado:
            data = datetime.now().strftime('%Y-%m-%d')
            query['Vencimento'] = {
                u"$lt": datetime.strptime(data + ' ' + '00:00:00.000', '%Y-%m-%d %H:%M:%S.%f')
            }
        cursor = database['Recebimentos'].find(query)
        try:
            for doc in cursor:
                total_devedor['total_devedor'] = total_devedor['total_devedor'] + doc['Historico'][0]['Valor']
                if 'Juro' in doc:
                    total_devedor['juro'] += Financeiro().calcular_juros(
                        valor=doc['Historico'][0]['Valor'],
                        vencimento=doc['Vencimento'],
                        tipo=doc['Juro']['Codigo'],
                        percentual=doc['Juro']['Percentual'],
                        dias_carencia=doc['Juro']['DiasCarencia']
                    )
                elif 'Multa' in doc:
                    total_devedor['multa'] += Financeiro().calcular_juros(
                        valor=doc['Historico'][0]['Valor'],
                        vencimento=doc['Vencimento'],
                        tipo=3,
                        percentual=doc['Multa']['Percentual'],
                        dias_carencia=doc['Multa']['DiasCarencia']
                    )
                print(doc['Historico'][0]['Valor'])
        finally:
            Uteis().fecha_conexao()
        return total_devedor

    def get_saldo_devedor_extenso(self, id):
        if type(id) == str and len(id) == 24:
            id = ObjectId(id)
        elif type(id) == ObjectId:
            pass
        else:
            return False
        saldo_devedor = self.get_saldo_devedor(id, database=None)
        extenso = Uteis().num_to_currency(
            (
                    saldo_devedor['total_devedor'] +
                    saldo_devedor['juro'] +
                    saldo_devedor['multa']
            )
        )
        return extenso

    @staticmethod
    def formatar_telefone(telefone):
        import re
        filtro = re.compile('([0-9]+)')
        telefone = filtro.findall(telefone)
        telefone = ''.join(telefone)
        if len(telefone) == 8:
            telefone = '%s-%s' % (telefone[0:3], telefone[4:7])
        elif len(telefone) == 10:
            telefone = '(%s) %s-%s' % (telefone[0:2], telefone[2:6], telefone[6:10])
        elif len(telefone) == 11:
            telefone = '(%s) %s %s-%s' % (telefone[0:2], telefone[2:3], telefone[3:7], telefone[7:11])
        return telefone

    @staticmethod
    def formatar_documento(documento):
        if len(documento) == 11:
            documento = '%s.%s.%s-%s' % (documento[0:3], documento[3:6], documento[6:9], documento[9:11])
        elif len(documento) == 14:
            documento = '%s.%s.%s/%s-%s' % (documento[0:2],
                                            documento[2:5],
                                            documento[5:8],
                                            documento[8:12],
                                            documento[12:14])
        return documento
