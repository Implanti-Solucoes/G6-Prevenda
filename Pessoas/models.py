# Create your models here.
from datetime import datetime

from core.models import Uteis
from bson import ObjectId, Regex


class PessoasMongo:
    def __init__(self):
        self.__query = {}
        self.__projection = {}
        self.__sort = []
        self.__limit = 250
        self.__aggregate_recebimentos_query = {}
        self.__lookup_recebimentos: bool = False

    @staticmethod
    def get_saldo_devedor(clients_list: dict):
        from Financeiro.models import Financeiro
        clients_list_return = []
        for cliente in clients_list:
            cliente['devedor'] = {
                'devedor': 0.0,
                'juro': 0.0,
                'multa': 0.0,
                'total_devedor': 0.0
            }

            if 'Parcelas' not in cliente:
                return cliente

            if len(cliente['Parcelas']) > 0:
                for parcela in cliente['Parcelas']:
                    cliente['devedor']['devedor'] += parcela['Historico'][0]['Valor']
                    if 'Juro' in parcela:
                        cliente['devedor']['juro'] += Financeiro().calcular_juros(
                            valor=parcela['Historico'][0]['Valor'],
                            vencimento=parcela['Vencimento'],
                            tipo=parcela['Juro']['Codigo'],
                            percentual=parcela['Juro']['Percentual'],
                            dias_carencia=parcela['Juro']['DiasCarencia']
                        )
                    elif 'Multa' in parcela:
                        cliente['devedor']['multa'] += Financeiro().calcular_juros(
                            valor=parcela['Historico'][0]['Valor'],
                            vencimento=parcela['Vencimento'],
                            tipo=3,
                            percentual=parcela['Multa']['Percentual'],
                            dias_carencia=parcela['Multa']['DiasCarencia']
                        )

                cliente['devedor']['total_devedor'] = \
                    cliente['devedor']['devedor'] + \
                    cliente['devedor']['multa'] + \
                    cliente['devedor']['juro']

                cliente['devedor']['extenso'] = \
                    Uteis().num_to_currency(cliente['devedor']['total_devedor'])
            clients_list_return.append(cliente)
        return clients_list_return

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

    def set_query_emitente(self, bloco_and: bool = False):
        if '$or' in self.__query or '$and' in self.__query and bloco_and is not False:
            return Warning('Digite o bloco como parametro')
        else:
            self.__query[u'_t'] = Regex(u".*Emitente.*", "i")

    def set_query_client(self, bloco_and: bool = False):
        if '$or' in self.__query or '$and' in self.__query and bloco_and is not False:
            return Warning('Digite o bloco como parametro')
        else:
            self.__query['Cliente'] = {u'$exists': True}

    def set_query_vendedor(self, bloco_and: bool = False):
        if '$or' in self.__query or '$and' in self.__query and bloco_and is not False:
            return Warning('Digite o bloco como parametro')
        else:
            self.__query['Vendedor'] = {u'$exists': True}

    def set_query_id(self, id):
        if type(id) == str and len(id) == 24:
            self.__query['_id'] = ObjectId(id)
        elif type(id) == ObjectId:
            self.__query['_id'] = id
        else:
            return False

    def set_query_ativo(self, ativo=True):
        if ativo is True or ativo is False:
            self.__query[u'Ativo'] = True
        else:
            Warning('Parametro passado é invalido')

    def set_query_name_range_start_with(self, letter_range_start, letter_range_end):
        query = {
            '$or': []
        }
        if '$or' in self.__query or '$and' in self.__query:
            return Warning('Adicione as letras usando a função set_query_name_start_with')

        if len(self.__query) > 0:
            for i in range(ord(str(letter_range_start)), ord(str(letter_range_end)) + 1):
                and_dict = {
                    u'$and': [
                        {'Nome': Regex(u'^{}.*'.format(chr(i)), 'i')}
                    ]
                }
                for key, value in self.__query.items():
                    and_dict['$and'][key] = value
                query['$or'].append(and_dict)
        else:
            for i in range(ord(str(letter_range_start)), ord(str(letter_range_end)) + 1):
                query['$or'].append({'Nome': Regex(u'^{}.*'.format(chr(i)), 'i')})
        self.__query = query

    def add_lookup_recebimentos(self):
        self.__lookup_recebimentos = True

    def add_match_vencimento_menor_que(self, data):
        self.__aggregate_recebimentos_query[u'Parcelas.Vencimento'] = {
            u'$lt': datetime.strptime(data + ' ' + '23:59:59.000', '%Y-%m-%d %H:%M:%S.%f')
        }

    def add_match_vencimento_menor_igual(self, data):
        self.__aggregate_recebimentos_query[u'Parcelas.Vencimento'] = {
            u'$lte': datetime.strptime(data + ' ' + '23:59:59.000', '%Y-%m-%d %H:%M:%S.%f')
        }

    def add_match_vencimento_maior_que(self, data):
        self.__aggregate_recebimentos_query[u'Parcelas.Vencimento'] = {
            u'$gt': datetime.strptime(data + ' ' + '23:59:59.000', '%Y-%m-%d %H:%M:%S.%f')
        }

    def add_match_vencimento_maior_igual(self, data):
        self.__aggregate_recebimentos_query[u'Parcelas.Vencimento'] = {
            u'$gte': datetime.strptime(data + ' ' + '23:59:59.000', '%Y-%m-%d %H:%M:%S.%f')
        }

    def add_match_situacao_t(self, situacao):
        self.__aggregate_recebimentos_query[u'Parcelas.Situacao._t'] = situacao

    def add_match_ativo(self, ativo=True):
        if ativo is True or ativo is False:
            self.__aggregate_recebimentos_query[u'Parcelas.Ativo'] = True
        else:
            Warning('Parametro passado é invalido')

    def execute_all(self):
        database = Uteis().conexao
        collection = database['Pessoas']
        dados = []
        try:
            if self.__lookup_recebimentos:
                pipeline = []
                if len(self.__query) > 0:
                    pipeline.append({u'$match': self.__query})

                if self.__lookup_recebimentos:
                    pipeline.append(
                        {
                            u'$lookup': {
                                u'from': u'Recebimentos',
                                u'localField': u'_id',
                                u'foreignField': u'PessoaReferencia',
                                u'as': u'Parcelas'
                            }
                        }
                    )

                if self.__lookup_recebimentos and len(self.__aggregate_recebimentos_query) > 0:
                    pipeline.append(
                        {
                            "$unwind": {
                                "path": "$Parcelas",
                                "includeArrayIndex": "arrayIndex",
                                "preserveNullAndEmptyArrays": False
                            }
                        },
                    )
                    pipeline.append({u'$match': self.__aggregate_recebimentos_query})
                    pipeline.append(
                        {
                            "$group": {
                                "_id": "$_id",
                                "_t": {
                                    "$first": "$_t"
                                },
                                "InformacoesPesquisa": {
                                    "$first": "$InformacoesPesquisa"
                                },
                                "Versao": {
                                    "$first": "$Versao"
                                },
                                "Nome": {
                                    "$first": "$Nome"
                                },
                                "Ativo": {
                                    "$first": "$Ativo"
                                },
                                "Imagem": {
                                    "$first": "$Imagem"
                                },
                                "DiaAcerto": {
                                    "$first": "$DiaAcerto"
                                },
                                "Carteira": {
                                    "$first": "$Carteira"
                                },
                                "Cliente": {
                                    "$first": "$Cliente"
                                },
                                "Fornecedor": {
                                    "$first": "$Fornecedor"
                                },
                                "Classificacao": {
                                    "$first": "$Classificacao"
                                },
                                "Municipio": {
                                    "$first": "$Municipio"
                                },
                                "Endereco": {
                                    "$first": "$Endereco"
                                },
                                "Profissao": {
                                    "$first": "$Profissao"
                                },
                                "Apelido": {
                                    "$first": "$Apelido"
                                },
                                "Rg": {
                                    "$first": "$Rg"
                                },
                                "PessoasAutorizadas": {
                                    "$first": "$PessoasAutorizadas"
                                },
                                "Observacao": {
                                    "$first": "$Observacao"
                                },
                                "NomeMae": {
                                    "$first": "$NomeMae"
                                },
                                "Genero": {
                                    "$first": "$Genero"
                                },
                                "DataNascimento": {
                                    "$first": "$DataNascimento"
                                },
                                "MesNascimento": {
                                    "$first": "$MesNascimento"
                                },
                                "NomeFantasia": {
                                    "$first": "$NomeFantasia"
                                },
                                "Cnpj": {
                                    "$first": "$Cnpj"
                                },
                                "Cpf": {
                                    "$first": "$Cpf"
                                },
                                "RegistroMunicipal": {
                                    "$first": "$RegistroMunicipal"
                                },
                                "RamoAtividade": {
                                    "$first": "$RamoAtividade"
                                },
                                "RegimeTributario": {
                                    "$first": "$RegimeTributario"
                                },
                                "CNAE": {
                                    "$first": "$CNAE"
                                },
                                "Sistema": {
                                    "$first": "$Sistema"
                                },
                                "PontoDeVenda": {
                                    "$first": "$PontoDeVenda"
                                },
                                "NumeroLicencaFuncionamento": {
                                    "$first": "$NumeroLicencaFuncionamento"
                                },
                                "NumeroAutorizacaoFuncionamento": {
                                    "$first": "$NumeroAutorizacaoFuncionamento"
                                },
                                "IncentivadorCultural": {
                                    "$first": "$IncentivadorCultural"
                                },
                                "RegimeEspecialTributacao": {
                                    "$first": "$RegimeEspecialTributacao"
                                },
                                "Parcelas": {
                                    "$push": "$Parcelas"
                                }
                            }
                        }
                    )
                cursor = collection.aggregate(
                    pipeline,
                    allowDiskUse=False
                )
                for doc in cursor:
                    doc['id'] = str(doc['_id'])
                    dados.append(doc)
            else:
                cursor = collection.find(self.__query)
                for doc in cursor:
                    doc['id'] = str(doc['_id'])
                    dados.append(doc)
        finally:
            Uteis().fecha_conexao()
        return dados
