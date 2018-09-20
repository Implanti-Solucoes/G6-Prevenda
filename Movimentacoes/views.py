import datetime

from django.shortcuts import render
from .models import Movimentacoes
from Financeiro.models import Financeiro
from core.models import Uteis


def listagem_prevenda(request):
    movimentacoes = Movimentacoes()
    movimentacoes.set_query_t('PreVenda', 'or')
    movimentacoes.set_query_t('NotaFiscalServico', 'or')
    movimentacoes.set_query_t('DocumentoAuxiliarVendaOrdemServico', 'or')
    movimentacoes.set_query_convertida('False')
    movimentacoes.set_sort_emissao()
    item = movimentacoes.execute_all()
    items = []

    for x in item:
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


def contrato_manutencao_futura(request, id):
    movimentacoes = Movimentacoes()
    uteis = Uteis()

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('DocumentoAuxiliarVendaOrdemServico')
    cursor = movimentacoes.execute_one()

    if 'DocumentoAuxiliarVendaOrdemServico' in cursor['_t']:
        cursor['tipo'] = 'DocumentoAuxiliarVendaOrdemServico'

    cursor = uteis.total_venda(cursor)
    cursor['Empresa']['TelefonePrincipal'] = uteis.formatar_telefone(telefone=cursor['Empresa']['TelefonePrincipal'])
    if cursor['Empresa']['Celulares']:
        x = 0
        for celular in cursor['Empresa']['Celulares']:
            cursor['Empresa']['Celulares'][x] = uteis.formatar_telefone(telefone=celular)
            x = x + 1

    datas = [cursor['DataHoraEmissao'] + datetime.timedelta(+12),
             cursor['DataHoraEmissao'] + datetime.timedelta(+24),
             cursor['DataHoraEmissao'] + datetime.timedelta(+36)]

    x = 0
    y = 0
    for item in cursor['ItensBase']:
        cursor['ItensBase'][x]['t'] = cursor['ItensBase'][x]['_t']
        if cursor['ItensBase'][x]['t'] == 'ItemDocumentoAuxiliarSaidaServico':
            y = y + 1
        x = x+1

    if y > 1:
        cursor['Servico01'] = 1

    cursor['liquido_extenso'] = uteis.num_to_currency(('%.2f' % cursor['liquido']).replace('.', ''))
    context = {'Numero': str(cursor['Numero']), 'venda': cursor, 'datas': datas}
    return render(request, 'movimentacoes/contrato_manutencao_futura.html', context)


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
        cursor['Total'] = cursor['Total'] + (item['Quantidade'] * item['PrecoUnitario']) - item['DescontoDigitado'] - \
                          item['DescontoProporcional']

    context = {'items': cursor, 'contas': contas, 'centros_custos': centros_custos, 'planos_conta': planos_conta}

    if 'Vendedor' in cursor:
        context['Vendedor'] = {
            'Nome': cursor['Vendedor']['Nome']
        }

    return render(request, 'movimentacoes/gerar_financeiro.html', context)
