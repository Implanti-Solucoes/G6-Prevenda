# Create your models here.
from core.models import Uteis
from bson import ObjectId
from django.db import models


class PessoasMongo:

    @staticmethod
    def get_pessoa(id):
        database = Uteis().conexao
        if type(id) == str and len(id) == 24:
            query = {'_id': ObjectId(id)}
        elif type(id) == ObjectId:
            query = {'_id': id}
        else:
            return []

        pessoa = database['Pessoas'].find_one(query)
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

    @staticmethod
    def get_clientes():
        database = Uteis().conexao
        query = {'Cliente': {u'$exists': True}}
        clientes = database['Pessoas'].find(query)
        clients_list = []
        for x in clientes:
            x['id'] = str(x['_id'])
            clients_list.append(x)

        Uteis().fecha_conexao()
        return clients_list

    def get_nome_emitente(self):
        emitente = self.get_emitente()
        return emitente['Nome']

    def get_cnpj_emitente(self):
        emitente = self.get_emitente()
        return emitente['Cnpj']

    @staticmethod
    def get_saldo_devedor(id):
        if type(id) == ObjectId:
            database = Uteis().conexao
            total_devedor = 0

            query = {'Situacao._t': {u"$ne": u"Quitada"}, 'PessoaReferencia': id}
            projection = {"Historico": 1.0}

            cursor = database["Recebimentos"].find(query, projection=projection)
            try:
                for doc in cursor:
                    total_devedor = total_devedor + doc['Historico'][0]['Valor']
            finally:
                Uteis().fecha_conexao()
            return total_devedor

    def get_saldo_devedor_extenso(self, id):
        if len(id) == 24:
            saldo_devedor = self.get_saldo_devedor(id)
            extenso = Uteis().num_to_currency(saldo_devedor)
            return extenso
