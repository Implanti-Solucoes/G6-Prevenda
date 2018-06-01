from bson import ObjectId
from django.shortcuts import render
from datetime import datetime
from core.models import Uteis
from .models import Pessoas, Parcelas



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
            parcelas = Parcelas()
            parcelas.set_query_situacao(u'Quitada')
            parcelas.set_query_id(ObjectId(id))
            cursor = parcelas.execute_one()
            print(cursor)
            clienteid = str(cursor['PessoaReferencia'])

            if clienteid in recibos:
                for item in cursor['Historico']:
                    if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                        valor_pago = item['Valor']
                        recibos[clienteid]['Total'] = recibos[clienteid]['Total'] + valor_pago

                        recibos[clienteid]['Parcelas'].append({'Valor_Pago': valor_pago,
                                                               'Documento': cursor['Documento'],
                                                               'Parcela': cursor['Ordem'],
                                                               'Data_Quitacao': cursor['DataQuitacao']})

            else:
                recibos[clienteid] = {}
                recibos[clienteid]['Parcelas'] = []
                recibos[clienteid]['Total'] = 0
                recibos[clienteid]['Total_extenso'] = ''


                cliente = pessoas.get_nome(cursor['PessoaReferencia'])
                saldo_devedor = pessoas.get_saldo_devedor(cursor['PessoaReferencia'])
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
            recibos[recibo]['Total_extenso'] = uteis.num_to_currency(('%.2f' % recibos[recibo]['Total']).replace('.', ''))

        context = {'Data': datetime.now(), 'Emitente': Emitente, 'Recibos': recibos}
        return render(request, 'recibo/impresso.html', context)

def listagem(request):
    pessoas = Pessoas()
    parcelas = Parcelas()
    parcelas.set_query_situacao(u'Quitada')
    parcelas.set_sort_data_quitacao()
    parcelas.set_sort_vencimento()
    cursor = parcelas.execute_all()
    Recebimentos = []

    for Recebimento in cursor:
        Recebimento['PessoaNome'] = pessoas.get_nome(Recebimento['PessoaReferencia'])
        for item in Recebimento['Historico']:
            if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
                Recebimento['valor_pago'] = item['Valor']

        Recebimentos.append(Recebimento)

    return render(request, 'recibo/listagem.html', {'Recebimentos': Recebimentos})
