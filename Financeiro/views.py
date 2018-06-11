from bson import ObjectId
from django.shortcuts import render
from datetime import datetime, timedelta

from Movimentacoes.models import Movimentacoes
from core.models import Uteis
from .models import Pessoas, Financeiro

def gerar_financeiro(request):
    movimentacoes = Movimentacoes()
    financeiro = Financeiro()

    id = request.POST['id']
    conta = request.POST['conta']
    centro_custo = request.POST['centro_custo']
    planos_contas = request.POST['planos_contas']
    parcelas = int(request.POST['parcelas'])

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_query_situacao_codigo(1)
    cursor = movimentacoes.execute_one()

    if 'InformacoesPesquisa' in cursor:
        cursor['Total'] = 0
        for item in cursor['ItensBase']:
            cursor['Total'] = cursor['Total'] + (item['Quantidade'] * item['PrecoUnitario']) - item[
                'DescontoDigitado'] - item['DescontoProporcional']

        InformacoesPesquisa = []
        InformacoesPesquisa.extend(cursor['InformacoesPesquisa'])
        x = 0
        extrutura = {}
        data = datetime.now()
        valor_parcela = cursor['Total'] / parcelas
        valor_parcela = "%.2f" % valor_parcela
        dados = financeiro.get_codigo_unico_centros_custos(centro_custo)
        #print(dados['CodigoUnico'])
        while x < parcelas:

            extrutura[x] = {
                "_t": ["ParcelaRecebimento", "ParcelaRecebimentoManual"],
                "InformacoesPesquisa": InformacoesPesquisa,
                "Versao": "736794.19:26:22.9976483",
                "Ativo": True,
                "Ordem": x+1,
                "Descricao": "PRE-VENDA " + str(cursor['Numero']) + ' - ' + str(x+1),
                "Documento": str(cursor['Numero']),
                "PessoaReferencia": cursor['Pessoa']['PessoaReferencia'],
                "Vencimento": data + timedelta(+(30 * (x+1))),
                "Historico": [
                    {
                        "_t": "HistoricoPendente",
                        "Valor": float(valor_parcela),
                        "EspeciePagamento": {
                            "_t": "EspeciePagamentoECF",
                            "Codigo": 1,
                            "Descricao": "Dinheiro",
                            "EspecieRecebimento" : {
                                "_t": "Dinheiro"
                            }
                        },
                        "PlanoContaCodigoUnico": "1",
                        "CentroCustoCodigoUnico": "1",
                        "ContaReferencia": ObjectId("5ace8b8c2454da0648670332"),
                        "EmpresaReferencia": ObjectId("5ace85402454da14f4f5a0d4"),
                        "NomeUsuario": "Usuário Administrador",
                        "Data": data,
                        "ChequeReferencia" : ObjectId("000000000000000000000000")
                    }
                ],
                "Situacao" : {
                    "_t" : "Pendente",
                    "Codigo" : 1
                },
                "ContaReferencia": ObjectId("5ace8b8c2454da0648670332"),
                "EmpresaReferencia": ObjectId("5ace85402454da14f4f5a0d4"),
                "NomeUsuario": "Usuário Administrador",
                "DataQuitacao": "0001-01-01T00:00:00.000+0000",
                "AcrescimoInformado": 0.0,
                "DescontoInformado": 0.0,
            }
            x = x+1
    return render(request, 'recibo/impresso.html', {})

def impresso(request):
    if request.method == 'POST':
        ids = request.POST.getlist('parcela')
        uteis = Uteis()
        pessoas = Pessoas()

        cnpj = pessoas.get_cnpj_emitente()
        nome_emitente = pessoas.get_nome_emitente()

        cnpj = "%s.%s.%s/%s-%s" % (cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])
        Emitente = {'Cnpj': cnpj, 'Nome':nome_emitente}
        recibos = {}

        for id in ids:
            financeiro = Financeiro()
            financeiro.set_query_situacao(u'Quitada')
            financeiro.set_query_id(ObjectId(id))
            cursor = financeiro.execute_one()
            print(cursor)
            clienteid = str(cursor['PessoaReferencia'])

            if clienteid in recibos:
                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['financeiro'].append({'Valor_Pago': valor_pago,
                                                               'Documento': cursor['Documento'],
                                                               'Parcela': cursor['Ordem'],
                                                               'Data_Quitacao': cursor['DataQuitacao']})

            else:
                recibos[clienteid] = {}
                recibos[clienteid]['financeiro'] = []
                recibos[clienteid]['Total'] = 0
                recibos[clienteid]['Total_extenso'] = ''


                cliente = pessoas.get_nome(cursor['PessoaReferencia'])
                saldo_devedor = pessoas.get_saldo_devedor(cursor['PessoaReferencia'])
                recibos[clienteid]['Cliente'] = {'Nome': cliente, 'Total_devedor': saldo_devedor}

                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['financeiro'].append({'Valor_Pago': valor_pago,
                                                               'Documento': cursor['Documento'],
                                                               'Parcela': cursor['Ordem'],
                                                               'Data_Quitacao': cursor['DataQuitacao']})

        for recibo in recibos:
            recibos[recibo]['Total_extenso'] = uteis.num_to_currency(('%.2f' % recibos[recibo]['Total']).replace('.', ''))

        context = {'Data': datetime.now(), 'Emitente': Emitente, 'Recibos': recibos}
        return render(request, 'recibo/impresso.html', context)

def listagem(request):
    pessoas = Pessoas()
    financeiro = Financeiro()
    financeiro.set_query_situacao(u'Quitada')
    financeiro.set_sort_data_quitacao()
    financeiro.set_sort_vencimento()
    cursor = financeiro.execute_all()
    Recebimentos = []

    for Recebimento in cursor:
        Recebimento['PessoaNome'] = pessoas.get_nome(Recebimento['PessoaReferencia'])
        for item in Recebimento['Historico']:
            if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                Recebimento['valor_pago'] = item['Valor']

        Recebimentos.append(Recebimento)

    return render(request, 'recibo/listagem.html', {'Recebimentos': Recebimentos})