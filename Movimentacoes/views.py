import datetime
from django.shortcuts import render
from .models import Movimentacoes
from Financeiro.models import Financeiro, Contratos
from core.models import Uteis, Configuracoes
from django.contrib.auth.decorators import login_required


@login_required(redirect_field_name='next')
def listagem_movimentacoes(request):
    movimentacao = Movimentacoes()
    movimentacao.set_sort_emissao(type='desc')
    item = movimentacao.execute_all()
    items = []

    for x in item:
        contrato = Contratos.objects.all().filter(id_g6=x['id'])
        if len(contrato) == 1:
            x['PagamentoRecebimento'] = contrato

        if "Documento" not in x['Pessoa']:
            x['naotemdocumento'] = 1
        items.append(x)
    context = {'items': movimentacao.informacoes_controle(items), }
    for x in Configuracoes.objects.all().filter(usuario_id=request.user.id):
        context[x.registro] = x.valor
    return render(request, 'movimentacoes/listagem.html', context)


@login_required(redirect_field_name='next')
def impressao1(request, id):
    movimentacao = Movimentacoes()
    uteis = Uteis()
    movimentacao.set_query_id(id)
    cursor = [movimentacao.execute_one()]
    cursor = movimentacao.informacoes_controle(cursor)[0]
    cursor = uteis.total_venda(cursor)
    if 'Documento' in cursor['Pessoa']:
        if len(cursor['Pessoa']['Documento']) == 14:
            cursor['Pessoa']['Tipo'] = 'CPF'
        else:
            cursor['Pessoa']['Tipo'] = 'CNPJ'

    context = {'Numero': str(cursor['Numero']), 'venda': cursor}
    return render(request, 'movimentacoes/impresso.html', context)


@login_required(redirect_field_name='next')
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
    cursor = Uteis().total_venda(cursor)

    context = {
        'items': cursor,
        'contas': contas,
        'centros_custos': centros_custos,
        'planos_conta': planos_conta
    }

    if 'Vendedor' in cursor:
        context['Vendedor'] = {
            'Nome': cursor['Vendedor']['Nome']
        }

    return render(request, 'movimentacoes/gerar_financeiro.html', context)
