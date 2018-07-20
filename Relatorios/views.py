import datetime

from django.conf.urls import url
from django.shortcuts import render, redirect
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
                    produtos[id]['PrecoUnitario'] = produtos[id]['PrecoUnitario'] + y['PrecoUnitario']
                    produtos[id]['Total'] = produtos[id]['Total']+int(1)

                else:
                    produtos[id] = {}
                    produtos[id]['Codigo'] = y['ProdutoServico']['CodigoInterno']
                    produtos[id]['Descricao'] = y['ProdutoServico']['Descricao']
                    produtos[id]['Quantidade'] = y['Quantidade']
                    produtos[id]['PrecoUnitario'] = y['PrecoUnitario']
                    produtos[id]['Total'] = int(1)

        for produto in produtos:
            produtos[produto]['Medio'] = round(round(produtos[produto]['PrecoUnitario'], 2) / round(produtos[produto]['Total'], 2),2)
            produtos[produto]['Total'] = round(round(produtos[produto]['Medio'], 2) * round(produtos[produto]['Quantidade'], 2), 2)

            total_geral = total_geral + produtos[produto]['Total']

        context = {}
        context['total_geral'] = total_geral
        context['produtos'] = produtos
        context['inicial'] = inicial
        context['final'] = final
        return render(request, 'relatorios/sintetico_produtos.html', context)
    else:
        return redirect('relatorios:index')


def operacoes_por_pessoa(request):
    # Relatorio fiscal de movimentação por cliente
    if request.method == 'POST':
        movimentacoes = Movimentacoes()
        cliente = request.POST['cliente']
        fiscal = request.POST.getlist('fiscal')

        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        if fiscal != []:
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
                venda['ItensBase'][x]['Total'] = total_item
                total = total + (item['PrecoUnitario'] * item['Quantidade'])
                x = x + 1

            total_geral = total_geral + total
            total = ('%.2f' % total).replace('.', ',')
            venda['Total'] = total
            vendas.append(venda)

        cliente = vendas[0]['Pessoa']['Nome']
        context = {}
        context['dados'] = vendas
        context['inicial'] = inicial
        context['final'] = final
        context['cliente'] = cliente
        context['total_geral'] = total_geral
        return render(request, 'relatorios/operacoes_por_pessoa.html', context)
    else:
        return redirect('relatorios:index')

def prevendas_por_vendedor(request):
    if request.method == 'POST':
        liquido = 0
        desconto = 0
        bruto = 0
        comissao = 0
        vendas = {}

        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        mostra_vendas = request.POST.getlist('vendas')
        print(vendedor = request.POST['vendedor'])

        movimentacoes = Movimentacoes()
        movimentacoes.set_query_t('PreVenda')
        movimentacoes.set_query_periodo(inicial, final)
        movimentacoes.set_limit(0)
        cursor = movimentacoes.execute_all()

        for venda in cursor:
            if 'Vendedor' in venda:
                vendedor_id = str(venda['Vendedor']['PessoaReferencia'])

                if vendedor_id not in vendas:
                    vendas[vendedor_id] = {}
                    vendas[vendedor_id]['nome'] = venda['Vendedor']['Nome']
                    vendas[vendedor_id]['comissao'] = 0
                    vendas[vendedor_id]['bruto'] = 0
                    vendas[vendedor_id]['liquido'] = 0
                    vendas[vendedor_id]['desconto'] = 0
                    vendas[vendedor_id]['vendas'] = []

                # Gerando totais para calculos de comissão e exibição
                total = 0
                desconto = 0
                for item in venda['ItensBase']:
                    total = total + (item['PrecoUnitario'] * item['Quantidade'])
                    desconto = item['DescontoDigitado'] + item['DescontoProporcional']

                # Calculando comissão
                if venda['Vendedor']['Vendedor']['Comissao']['_t'] == 'TotalVenda' and \
                        venda['Vendedor']['Vendedor']['BaseCalculoComissao'] == 0:
                    comissao_venda = total * venda['Vendedor']['Vendedor']['PercentualComissao'] / 100

                elif venda['Vendedor']['Vendedor']['Comissao']['_t'] == 'TotalVenda' and \
                        venda['Vendedor']['Vendedor']['BaseCalculoComissao'] == 1:
                    comissao_venda = (total - desconto) * venda['Vendedor']['Vendedor']['PercentualComissao'] / 100
                else:
                    comissao_venda = total * venda['Vendedor']['Vendedor']['PercentualComissao'] / 100

                if mostra_vendas != []:
                    vendas[vendedor_id]['vendas'].append(
                        {
                            "numero": venda["Numero"],
                            "data": venda["DataHoraEmissao"],
                            "comissao": comissao_venda,
                            "desconto": desconto,
                            "bruto": total,
                            "liquido": total - desconto
                        }
                    )

                vendas[vendedor_id]['bruto'] = vendas[vendedor_id]['bruto'] + total
                vendas[vendedor_id]['liquido'] = vendas[vendedor_id]['liquido'] + total - desconto
                vendas[vendedor_id]['desconto'] = vendas[vendedor_id]['desconto'] + desconto
                vendas[vendedor_id]['comissao'] = vendas[vendedor_id]['comissao'] + comissao_venda

                liquido = liquido + total - desconto
                total = total + desconto
                bruto = bruto + total
                comissao = comissao + comissao_venda

        context = {
            'comissao': comissao,
            'liquido': liquido,
            'desconto': desconto,
            'bruto': bruto,
            'vendas': vendas,
            'inicial': inicial,
            'final': final
        }
        return render(request, 'relatorios/prevendas_por_vendedor.html', context)
    else:
        return redirect('relatorios:index')

def prevendas_por_usuario(request):
    if request.method == 'POST':
        # Declaração de variaveis uteis
        liquido = 0
        desconto = 0
        bruto = 0
        vendas = {}

        # Recebendo dados post
        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        mostra_vendas = request.POST.getlist('vendas')

        # Setando filtros para busca no banco
        movimentacoes = Movimentacoes()
        movimentacoes.set_query_t('PreVenda')
        movimentacoes.set_query_periodo(inicial, final)
        movimentacoes.set_limit(0)
        cursor = movimentacoes.execute_all()

        # Tratando dados para gerar totais e separação por usuarios
        for venda in cursor:
            usuario = venda['Historicos'][0]['NomeUsuario']

            # Separando usuarios
            if usuario not in vendas:
                vendas[usuario] = {}
                vendas[usuario]['bruto'] = 0
                vendas[usuario]['desconto'] = 0
                vendas[usuario]['liquido'] = 0
                vendas[usuario]['vendas'] = []

            # Gerando totais para exibição
            total = 0
            desconto = 0
            for item in venda['ItensBase']:
                total = total + (item['PrecoUnitario'] * item['Quantidade'])
                desconto = item['DescontoDigitado'] + item['DescontoProporcional']

            if mostra_vendas != []:
                vendas[usuario]['vendas'].append(
                    {
                        "numero": venda["Numero"],
                        "data": venda["DataHoraEmissao"],
                        "desconto": desconto,
                        "bruto": total,
                        "liquido": total - desconto
                    }
                )

            vendas[usuario]['bruto'] = vendas[usuario]['bruto'] + total
            vendas[usuario]['liquido'] = vendas[usuario]['liquido'] + total - desconto
            vendas[usuario]['desconto'] = vendas[usuario]['desconto'] + desconto

            liquido = liquido + total - desconto
            total = total + desconto
            bruto = bruto + total

        context = {
            'liquido': liquido,
            'desconto': desconto,
            'bruto': bruto,
            'vendas': vendas,
            'inicial': inicial,
            'final': final
        }
        return render(request, 'relatorios/prevendas_por_usuario.html', context)
    else:
        return redirect('relatorios:index')