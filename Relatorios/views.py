import datetime

from django.conf.urls import url
from django.shortcuts import render
from Movimentacoes.models import Movimentacoes
from Financeiro.models import Financeiro

def index(request):
    movimentacoes = Movimentacoes()
    if request.method != 'POST':
        clientes = movimentacoes.get_clientes()
        vendedores = movimentacoes.get_vendedores()
        context = {
            'clientes': clientes,
            'vendedores': vendedores,
        }
        return render(request, 'relatorios/form.html', context)

def sintetico_produtos(request):
    if request.method == 'POST':
        movimentacoes = Movimentacoes()
        produtos = {}
        total_geral = 0

        cliente = request.POST['cliente']
        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        movimentacoes.set_query_t('PreVenda')
        movimentacoes.set_query_periodo(inicial, final)
        movimentacoes.set_projection_itens()
        cursor = movimentacoes.execute_all()

        for x in cursor:
            for y in x['ItensBase']:
                id = str(y['ProdutoServico']['ProdutoServicoReferencia'])

                if id in produtos:
                    produtos[id]['Quantidade'] = produtos[id]['Quantidade'] + y['Quantidade']
                    produtos[id]['Total'] = produtos[id]['Total'] + (y['Quantidade'] * y['PrecoUnitario'])
                else:
                    produtos[id] = {}
                    produtos[id]['Codigo'] = y['ProdutoServico']['CodigoInterno']
                    produtos[id]['Descricao'] = y['ProdutoServico']['Descricao']
                    produtos[id]['Quantidade'] = y['Quantidade']
                    produtos[id]['Total'] = y['Quantidade'] * y['PrecoUnitario']

            for produto in produtos:
                total_geral = total_geral + produtos[produto]['Total']
                produtos[produto]['Medio'] = produtos[produto]['Quantidade'] / produtos[produto]['Total']

            context={
                'total_geral':total_geral,
                'produtos': produtos,
                'inicial':inicial,
                'final':final
            }
        return render(request, 'relatorios/sintetico_produtos.html', context)

def operacoes_por_pessoa(request):
    if request.method == 'POST':
        movimentacoes = Movimentacoes()
        cliente = request.POST['cliente']
        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        movimentacoes.set_query_fiscal('Saida')
        movimentacoes.set_query_situacao_codigo(2)
        movimentacoes.set_query_periodo(inicial, final)
        movimentacoes.set_query_pessoa_id(cliente)
        movimentacoes.set_sort_emissao('asc')
        dados = movimentacoes.execute_all()

        vendas = []
        total_geral = 0

        for venda in dados:
            total = 0.0
            x = 0

            for item in venda['ItensBase']:
                total_item = item['PrecoUnitario'] * item['Quantidade']
                venda['ItensBase'][x]['Total'] = ('%.2f' % total_item).replace('.', ',')
                total = total + (item['PrecoUnitario'] * item['Quantidade'])
                venda['ItensBase'][x]['PrecoUnitario'] = ('%.2f' % venda['ItensBase'][x]['PrecoUnitario']).replace(
                    '.',
                    ',')
                venda['ItensBase'][x]['Quantidade'] = ('%.2f' % venda['ItensBase'][x]['Quantidade']).replace('.',
                                                                                                             ',')
                x = x + 1

            total_geral = total_geral + total
            total = ('%.2f' % total).replace('.', ',')
            venda['Total'] = total
            vendas.append(venda)

        total_geral = ('%.2f' % total_geral).replace('.', ',')
        cliente = vendas[0]['Pessoa']['Nome']
        context = {}
        context['dados'] = vendas
        context['inicial'] = inicial
        context['final'] = final
        context['cliente'] = cliente
        context['total_geral'] = total_geral
        return render(request, 'relatorios/operacoes_por_pessoa.html', context)

def prevendas_por_vendedor(request):
    if request.method == 'POST':
        movimentacoes = Movimentacoes()
        total_geral = 0
        vendas = []

        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        movimentacoes.set_query_t('PreVenda')
        movimentacoes.set_query_periodo(inicial, final)
        movimentacoes.set_projection_itens()
        cursor = movimentacoes.execute_all()

        for venda in cursor:
            if 'Vendedor' in venda:
                vendedor_id = str(venda['Vendedor']['PessoaReferencia'])

                if vendedor_id not in vendas:
                    vendas[vendedor_id] = []
                    vendas[vendedor_id]['comissao'] = 0
                    vendas[vendedor_id]['Nome'] = venda['Vendedor']['Nome']

                total = 0
                for item in venda['ItensBase']:
                    total = total + (item['PrecoUnitario'] * item['Quantidade'])

                vendas[vendedor_id].append(
                    {
                        "Numero": venda["Numero"],
                        "Data": venda["DataHoraEmissao"],
                        "Total": total
                    }
                )
                total_geral = total_geral + total

        context = {
            'total_geral': total_geral,
            'vendas': vendas,
            'inicial': inicial,
            'final': final
        }
        return render(request, 'relatorios/prevendas_por_vendedor.html', context)