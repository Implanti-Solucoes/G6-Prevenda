from datetime import datetime
from bson import ObjectId
from Pessoas.models import PessoasMongo
from core.models import Uteis, Configuracoes
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
        self.sort = []

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
        self.query['Vencimento'] = {
            u"$gte": inicial.replace(tzinfo=FixedOffset(-180, "-0300")),
            u"$lt": final.replace(tzinfo=FixedOffset(-180, "-0300"))
        }

    def set_query_emissao_periodo(self, inicial, final):
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

    @staticmethod
    def remove_repetidos(lista):
        l = []
        for i in lista:
            if i not in l:
                l.append(i)
        l.sort()
        return l

    def gerar_parcela(self, titulo, informacoes_pesquisa, pessoa,
                      emitente, documento, num, conta, centro_custo,
                      planos_contas, valor_parcela, vencimento, entrada=False):

        cursor = PessoasMongo()
        cursor.set_query_id(pessoa)
        pessoa = cursor.execute_all()
        if len(pessoa) > 0:
            pessoa = pessoa[0]

        cursor = PessoasMongo()
        cursor.set_query_id(emitente)
        emitente = cursor.execute_all()
        if len(emitente) > 0:
            emitente = emitente[0]

        if '_id' not in emitente or '_id' not in pessoa:
            print("ID do cliente ou emitente não foi encontrado")
            return False

        # Conta
        if type(conta) == str and len(conta) == 24:
            conta = ObjectId(conta)
        elif type(conta) == ObjectId:
            pass
        else:
            print("ID da Conta repassado invalido")
            return False

        valor_parcela = round(valor_parcela, 2)
        if valor_parcela <= 0:
            return False

        # Configurando informações de pesquisa com base no movimento
        pesquisa = []
        pesquisa.extend(informacoes_pesquisa)
        pesquisa.extend(pessoa['InformacoesPesquisa'])
        pesquisa.append(str(num))
        pesquisa.append(str(documento))
        pesquisa.append(str(titulo))
        pesquisa = self.remove_repetidos(pesquisa)

        z = []
        for x in pesquisa:
            z.append(str(x))
        pesquisa = z
        del z

        # Configurando modelo
        modelo = {
            '_t': ['ParcelaRecebimento', 'ParcelaRecebimentoManual'],
            'InformacoesPesquisa': pesquisa,
            'Versao': '736794.19:26:22.9976483',
            'Ativo': True,
            'Ordem': num,
            'Descricao': titulo + " " + str(documento) + " " + str(num),
            'Documento': str(documento),
            'PessoaReferencia': pessoa['_id'],
            'Vencimento': vencimento if type(vencimento) == datetime else datetime.strptime(vencimento, '%Y-%m-%d'),
            'Historico': [
                {
                    '_t': 'HistoricoAguardando',
                    'Valor': valor_parcela,
                    'EspeciePagamento': {
                        '_t': 'EspeciePagamentoECF',
                        'Codigo': 1,
                        'Descricao': 'Dinheiro',
                        'EspecieRecebimento': {
                            '_t': 'Dinheiro'
                        }
                    },
                    'PlanoContaCodigoUnico': planos_contas,
                    'CentroCustoCodigoUnico': centro_custo,
                    'ContaReferencia': conta,
                    'EmpresaReferencia': emitente['_id'],
                    'NomeUsuario': 'Usuário Administrador',
                    'Data': vencimento if type(vencimento) == datetime else datetime.strptime(vencimento, '%Y-%m-%d'),
                    'ChequeReferencia': ObjectId('000000000000000000000000')
                },
                {
                    '_t': 'HistoricoPendente',
                    'Valor': valor_parcela,
                    'EspeciePagamento': {
                        '_t': 'EspeciePagamentoECF',
                        'Codigo': 1,
                        'Descricao': 'Dinheiro',
                        'EspecieRecebimento': {
                            '_t': 'Dinheiro'
                        }
                    },
                    'PlanoContaCodigoUnico': planos_contas,
                    'CentroCustoCodigoUnico': centro_custo,
                    'ContaReferencia': conta,
                    'EmpresaReferencia': emitente['_id'],
                    'NomeUsuario': 'Usuário Administrador',
                    'Data': vencimento if type(vencimento) == datetime else datetime.strptime(vencimento, '%Y-%m-%d'),
                    'ChequeReferencia': ObjectId('000000000000000000000000')
                }
            ],
            'Situacao': {},
            'ContaReferencia': conta,
            'EmpresaReferencia': emitente['_id'],
            'NomeUsuario': 'Usuário Administrador',
            'DataQuitacao': '0001-01-01T00:00:00.000+0000',
            'AcrescimoInformado': 0.0,
            'DescontoInformado': 0.0,
        }

        # Verificando configurações para aplicar juros e multa
        config = Configuracoes().configuracoes()
        if 'Financeiro' in config:
            # Carregando das configurações as variaveis
            tipo = config['Financeiro']['TipoCalculoJuro']['Valor']
            carencia = config['Financeiro']['DiasCarenciaJuroMulta']['Valor']
            perce_ju = config['Financeiro']['PercentualJuro']['Valor']
            perce_mu = config['Financeiro']['PercentualMulta']['Valor']

            # Inserindo na parcela os juros
            modelo['Juro'] = {
                "_t": 'JuroSimples' if tipo == 1 else 'JuroComposto',
                "Codigo": 1,
                "Descricao": 'Simples' if tipo == 1 else 'Composto',
                "Percentual": perce_ju,
                "DiasCarencia": carencia
            }

            # Inserindo na parcela a multa
            modelo['Multa'] = {
                'Percentual': perce_mu,
                'DiasCarencia': carencia
            }

        # Verificando se é entrada ou não
        if entrada:
            modelo['Situacao'] = {
                '_t': 'Quitada',
                'Codigo': 3
            }
            modelo['DataQuitacao'] = vencimento if type(vencimento) == datetime else datetime.strptime(vencimento,
                                                                                                  '%Y-%m-%d')
            modelo['Historico'].append({
                '_t': 'HistoricoQuitado',
                'Valor': valor_parcela,
                'EspeciePagamento': {
                    '_t': 'EspeciePagamentoECF',
                    'Codigo': 1,
                    'Descricao': 'Dinheiro',
                    'EspecieRecebimento': {
                        '_t': 'Dinheiro'
                    }
                },
                'PlanoContaCodigoUnico': planos_contas,
                'CentroCustoCodigoUnico': centro_custo,
                'ContaReferencia': conta,
                'EmpresaReferencia': emitente['_id'],
                'NomeUsuario': 'Usuário Administrador',
                'Data': vencimento if type(vencimento) == datetime else datetime.strptime(vencimento, '%Y-%m-%d'),
                'ChequeReferencia': ObjectId('000000000000000000000000'),
                'Desconto': 0.0,
                'Acrescimo': 0.0,
                'DataQuitacao': vencimento if type(vencimento) == datetime else datetime.strptime(vencimento,
                                                                                                  '%Y-%m-%d')
            })
            lancamento_movimento = self.lancamento_movimento_conta(
                doc=documento,
                parc=num,
                centro_custo=centro_custo,
                conta=conta,
                emitente=emitente['_id'],
                pessoa=pessoa['_id'],
                plano_contas=planos_contas,
                valor=valor_parcela
            )
            if not lancamento_movimento:
                print("Lancamento da movimentação da conta falhou")
                return False

            alterar_saldo = self.alterar_saldo_conta(
                conta=conta,
                operacao='+',
                valor=valor_parcela
            )
            if not alterar_saldo:
                print("Alterar Saldo Falhou")
                return False

            # Criando Conexão
            try:
                database = Uteis().conexao
                id = None
                while id is None:
                    id = database['Recebimentos'].insert(modelo)
                Uteis().fecha_conexao()
                return id
            except Exception as e:
                print(e)
        else:
            modelo['Situacao'] = {
                '_t': 'Pendente',
                'Codigo': 1
            }

            # Criando Conexão
            try:
                database = Uteis().conexao
                id = None

                while id is None:
                    id = database['Recebimentos'].insert(modelo)
                Uteis().fecha_conexao()
                return id
            except Exception as e:
                print(e)

    def lancamento_movimento_conta(self, doc, parc, valor, emitente, pessoa, conta, plano_contas, centro_custo):
        # Cliente
        cursor = PessoasMongo()
        cursor.set_query_id(pessoa)
        pessoa = cursor.execute_all()
        if len(pessoa) > 0:
            pessoa = pessoa[0]

        # Emitente
        cursor = PessoasMongo()
        cursor.set_query_id(emitente)
        emitente = cursor.execute_all()
        if len(emitente) > 0:
            emitente = emitente[0]

        if '_id' not in emitente or '_id' not in pessoa:
            print("ID do cliente ou emitente não foi encontrado")
            return False

        # Conta
        if type(conta) == str and len(conta) == 24:
            conta = ObjectId(conta)
        elif type(conta) == ObjectId:
            pass
        else:
            print("ID da Conta repassado invalido")
            return False

        valor = round(valor, 2)
        if valor <= 0:
            print("Valor do lançamento não é valido")
            return False

        modelo = {
            '_t': [
                'MovimentoConta',
                'LancamentoRecebimento'
            ],
            'InformacoesPesquisa': [
                'recebimento',
                'do',
                'documento:',
                'doc:',
                str(doc),
                str(parc),
                'ordem:'
            ],
            'Versao': '737006.10:43:35.2628518',
            'Ativo': True,
            'Historico': 'Recebimento de Doc.: {} Ordem: {}'.format(doc, parc), 'Codigo': 2,
            'Descricao': 'Recebimento do documento: Doc.: {} Ordem: {}'.format(doc, parc),
            'Documento': 'Doc.: {} Ordem: {}'.format(doc, parc),
            'CreditoDebito': {
                '_t': 'Credito',
                'Codigo': 1,
                'Descricao': 'Crédito',
                'Valor': valor,
                'ValorEditavel': valor
            },
            'ContaReferencia': conta,
            'PlanoContaCodigo': plano_contas,
            'CentroCustoCodigo': centro_custo,
            'DataHoraCompetencia': datetime.now(),
            'EmpresaReferencia': emitente['_id'],
            'PessoaReferencia': pessoa['_id'],
            'Especie': 'Dinheiro',
        }

        # Criando Conexão
        try:
            modelo['InformacoesPesquisa'] = self.remove_repetidos(modelo['InformacoesPesquisa'])
            database = Uteis().conexao
            id = None
            while id is None:
                id = database['MovimentosConta'].insert(modelo)
            Uteis().fecha_conexao()
            return True
        except Exception as e:
            print(e)

    @staticmethod
    def alterar_saldo_conta(operacao, valor, conta):
        if type(conta) == str and len(conta) == 24:
            conta = ObjectId(conta)
        elif type(conta) == ObjectId:
            pass
        else:
            print("ID da Conta repassado invalido")
            return False

        valor_parcela = round(valor, 2)
        if valor_parcela <= 0:
            return False

        database = Uteis().conexao
        cursor = database['SaldosConta'].find_one({'ContaReferencia': conta})
        if operacao == '+':
            cursor['Valor'] = cursor['Valor'] + valor
        elif operacao == '-':
            cursor['Valor'] = cursor['Valor'] - valor
        database['SaldosConta'].update({'_id': cursor['_id']}, cursor)
        Uteis().fecha_conexao()
        return True

    @staticmethod
    def calcular_juros(valor, vencimento, tipo, percentual, dias_carencia):
        # Verificando configurações para aplicar juros e multa
        config = Configuracoes().configuracoes()
        if 'Financeiro' in config:
            dias = int((datetime.now() - vencimento).days)-1
            juros = 0
            if dias > 0:
                if tipo == 1:
                    juros = valor * (percentual/30) * dias / 100
                elif tipo == 2:
                    juros = ((((1+(percentual/100))**(1/30))**dias)-1)*valor
            if (dias-dias_carencia) > 0 and tipo == 3:
                juros = valor * percentual / 100
            return juros


class Contratos(models.Model):
    tipo = models.IntegerField()
    id_g6 = models.CharField('id da movimentacao', max_length=24)
    id_g6_cliente = models.CharField('id do cliente', max_length=24)
    excluido = models.BooleanField()
    motivo = models.CharField('Motivo do cancelamento', max_length=250)
    desconto = models.FloatField('Desconto', default=0.00)


class Parcelas(models.Model):
    contrato = models.ForeignKey(Contratos, on_delete=models.CASCADE, related_name='parcelas')
    id_g6 = models.CharField('id da parcela', max_length=24)
    valor = models.FloatField('Valor Parcela')
