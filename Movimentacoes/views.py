import datetime

from django.shortcuts import render
from .models import Movimentacoes
from Financeiro.models import Financeiro
from core.models import Uteis

def listagem_prevenda(request):
    movimentacoes = Movimentacoes()
    movimentacoes.set_query_t('PreVenda', 'or')
    movimentacoes.set_query_t('DocumentoAuxiliarVenda', 'or')
    movimentacoes.set_query_convertida('False')
    movimentacoes.set_sort_emissao()
    item = movimentacoes.execute_all()
    items = []

    for x in item:
        if 'PreVenda' in x['t']:
            x['prevenda'] = 1
        else:
            x['dav'] = 1
        items.append(x)

    context = {'items': items}
    return render(request, 'movimentacoes/listagem.html', context)

def impresso_prevenda(request, id):
    items = []

    movimentacoes = Movimentacoes()
    uteis = Uteis

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_projection_numero()
    movimentacoes.set_projection_pessoa()
    movimentacoes.set_projection_itens()
    movimentacoes.set_projection_empresa()
    cursor = movimentacoes.execute_one()

    if cursor['Pessoa']['_t'] == 'FisicaHistorico':
        cursor['Pessoa']['tipo'] = 'CPF'
    elif cursor['Pessoa']['_t'] == 'EmpresaHistorico':
        cursor['Pessoa']['tipo'] = 'CNPJ'

    cursor = uteis.total_venda(cursor)

    context = {'Numero': str(cursor['Numero']), 'venda': cursor}
    return render(request, 'movimentacoes/impresso.html', context)

def impresso_dav_80(request, id):
    movimentacoes = Movimentacoes()
    uteis = Uteis()

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('DocumentoAuxiliarVenda')
    cursor = movimentacoes.execute_one()
    cursor = uteis.total_venda(cursor)
    return render(request, 'movimentacoes/impresso_dav_80mm.html', {'vendas':cursor})

def gerar_financeiro(request, id):
    movimentacoes = Movimentacoes()
    financeiro = Financeiro()
    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_query_situacao_codigo(1)
    cursor = movimentacoes.execute_one()

    contas = financeiro.get_contas
    centros_custos = financeiro.get_centros_custos
    planos_conta = financeiro.get_planos_conta


    cursor['Total'] = 0
    for item in cursor['ItensBase']:
        cursor['Total'] = cursor['Total'] + (item['Quantidade'] * item['PrecoUnitario']) - item['DescontoDigitado'] - item['DescontoProporcional']

    context = {'items': cursor, 'contas': contas, 'centros_custos': centros_custos, 'planos_conta': planos_conta}

    if 'Vendedor' in cursor:
        context['Vendedor'] = {
            'Nome': cursor['Vendedor']['Nome']
        }

    return render(request, 'movimentacoes/gerar_financeiro.html', context)