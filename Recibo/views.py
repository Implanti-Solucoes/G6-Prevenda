from typing import Dict

from bson import ObjectId
from django.shortcuts import render
from datetime import datetime
from core.uteis import Uteis
from core.pessoas import Pessoas

uteis = Uteis()
pessoas = Pessoas()

def impresso(request):
    if request.method == 'POST':
        ids = request.POST.getlist('parcela')

        cnpj = pessoas.CnpjEmitente()
        nome_emitente = pessoas.NomeEmitente()

        cnpj = "%s.%s.%s/%s-%s" % (cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])
        Emitente = {'Cnpj': cnpj, 'Nome':nome_emitente}
        recibos = {}

        for id in ids:
            query = {'Situacao._t': u'Quitada', '_id': ObjectId(id)}
            database = uteis.Conexao()
            cursor = database['Recebimentos'].find_one(query)
            clienteid = str(cursor['PessoaReferencia'])

            if clienteid in recibos:
                print('ok1')
                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['Parcelas'].append({'Valor_Pago': valor_pago,
                                                               'Documento': cursor['Documento'],
                                                               'Parcela': cursor['Ordem'],
                                                               'Data_Quitacao': cursor['DataQuitacao']})

            else:
                print(clienteid)
                recibos[clienteid] = {}
                recibos[clienteid]['Parcelas'] = []
                recibos[clienteid]['Total'] = 0
                recibos[clienteid]['Total_extenso'] = ''


                cliente = pessoas.NomeCliente(cursor['PessoaReferencia'])
                saldo_devedor = pessoas.SaldoDevedor(cursor['PessoaReferencia'])
                recibos[clienteid]['Cliente'] = {'Nome': cliente, 'Total_devedor': saldo_devedor}

                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['Parcelas'].append({'Valor_Pago': valor_pago,
                                                               'Documento': cursor['Documento'],
                                                               'Parcela': cursor['Ordem'],
                                                               'Data_Quitacao': cursor['DataQuitacao']})

        for recibo in recibos:
            recibos[recibo]['Total_extenso'] = uteis.numToCurrency(('%.2f' % recibos[recibo]['Total']).replace('.', ''))

        context = {'Data': datetime.now(), 'Emitente': Emitente, 'Recibos': recibos}
        return render(request, 'Recibo/impresso.html', context)

def listagem(request):
    database = uteis.Conexao()
    Recebimentos = []
    queryRecebimentos = {'Situacao._t': u'Quitada'}
    sort = [(u"Vencimento", -1), (u"DataQuitacao", -1)]

    cursor = database['Recebimentos'].find(queryRecebimentos, sort=sort).limit(500)
    for Recebimento in cursor:
        Recebimento['id'] = str(Recebimento['_id'])
        Recebimento['PessoaNome'] = pessoas.NomeCliente(Recebimento['PessoaReferencia'])
        for item in Recebimento['Historico']:
            if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                Recebimento['valor_pago'] = item['Valor']

        Recebimentos.append(Recebimento)

    return render(request, 'Recibo/listagem.html', {'Recebimentos': Recebimentos})
