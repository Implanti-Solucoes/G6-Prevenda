import datetime

from django.shortcuts import render
from .models import Movimentacoes
from Financeiro.models import Financeiro, Contratos
from core.models import Uteis


def listagem_prevenda(request):
    movimentacao = Movimentacoes()
    movimentacao.set_query_t('PreVenda')
    movimentacao.set_sort_emissao(type='desc')
    item = movimentacao.execute_all()
    items = []

    for x in item:
        contrato = Contratos.objects.all().filter(id_g6=x['id'])
        if len(contrato) == 1:
            x['PagamentoRecebimento'] = 1
        if 'PreVenda' in x['t']:
            x['prevenda'] = 1
        elif 'NotaFiscalServico' in x['t']:
            x['NotaFiscalServico'] = 1
        elif 'DocumentoAuxiliarVendaOrdemServico' in x['t']:
            x['DocumentoAuxiliarVendaOrdemServico'] = 1
        items.append(x)

    context = {'items': items}
    return render(request, 'movimentacoes/listagem.html', context)


def impresso_prevenda(request, id):
    movimentacoes = Movimentacoes()
    uteis = Uteis

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda', 'or')
    movimentacoes.set_query_t('NotaFiscalServico', 'or')
    cursor = movimentacoes.execute_one()

    if 'NotaFiscalServico' in cursor['_t']:
        cursor['tipo'] = 'NotaFiscalServico'
    elif 'PreVenda' in cursor['_t']:
        cursor['tipo'] = 'PreVenda'

    cursor = uteis.total_venda(cursor)

    context = {'Numero': str(cursor['Numero']), 'venda': cursor}
    return render(request, 'movimentacoes/impresso.html', context)


def gerar_financeiro(request, id):
    movimentacao = Movimentacoes()
    movimentacao.set_query_id(id)
    movimentacao.set_query_t('PreVenda')
    movimentacao.set_query_situacao_codigo(1)
    movimentacao.set_sort_emissao()
    cursor = movimentacao.execute_one()
    contas = Financeiro().get_contas
    centros_custos = Financeiro().get_centros_custos
    planos_conta = Financeiro().get_planos_conta

    cursor['Total'] = 0
    for item in cursor['ItensBase']:
        cursor['Total'] = cursor['Total'] + (item['Quantidade'] * item['PrecoUnitario']) - item['DescontoDigitado'] - \
                          item['DescontoProporcional']

    context = {'items': cursor, 'contas': contas, 'centros_custos': centros_custos, 'planos_conta': planos_conta}

    if 'Vendedor' in cursor:
        context['Vendedor'] = {
            'Nome': cursor['Vendedor']['Nome']
        }

    return render(request, 'movimentacoes/gerar_financeiro.html', context)
