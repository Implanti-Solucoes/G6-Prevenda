from bson import ObjectId
from django.shortcuts import render
from datetime import datetime
from core.uteis import Uteis
from core.pessoas import Pessoas

uteis = Uteis()
pessoas = Pessoas()

def impresso(request, id):
    query = {'Situacao._t': u'Quitada', '_id': ObjectId(id)}
    database = uteis.Conexao()
    cursor = database['Recebimentos'].find_one(query)

    cnpj = pessoas.CnpjEmitente()
    nome_emitente = pessoas.NomeEmitente()
    cliente = pessoas.NomeCliente(cursor['PessoaReferencia'])
    saldo_devedor = pessoas.SaldoDevedor(cursor['PessoaReferencia'])

    for item in cursor['Historico']:
        if 'HistoricoQuitado' in item['_t'] or 'HistoricoQuitadoParcial' in item['_t']:
            valor_pago = item['Valor']
            valor_extenso = uteis.numToCurrency(str(item['Valor']).replace('.', ''))

    cnpj = "%s.%s.%s/%s-%s" % (cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])
    context = {'Cliente': cliente,
            'Valor_pago': valor_pago,
            'Valor_extenso': valor_extenso,
            'Total_devedor': saldo_devedor,
            'Documento': cursor['Documento'],
            'Parcela': cursor['Ordem'],
            'Recebimento': cursor['DataQuitacao'],
            'Data': datetime.now(),
            'Emitente': {'Nome': nome_emitente, 'Cnpj': cnpj}}
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