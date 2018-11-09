import datetime
from django.conf.urls import url
from django.shortcuts import render, redirect
from Movimentacoes.models import Movimentacoes
from core.models import Uteis


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

        context = {
            'total_geral': total_geral,
            'produtos': produtos,
            'inicial': inicial,
            'final': final
        }
        return render(request, 'relatorios/sintetico_produtos.html', context)
    else:
        return redirect('relatorios:index')


def operacoes_por_pessoa(request):
    # Relatorio fiscal de movimentação por cliente
    if request.method == 'POST':
        context = {}

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
        movimentacoes.set_query_situacao_codigo(12, 1)
        movimentacoes.set_query_convertida(False)
        movimentacoes.set_sort_emissao('asc')
        dados = movimentacoes.execute_all()

        if len(dados) > 0:
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
        # Declarando variaveis Uteis
        vendas = {}

        # Recebendo filtros
        inicial = request.POST['inical']
        year, month, day = map(int, inicial.split('-'))
        inicial = datetime.datetime(year, month, day, 00, 00, 00)

        final = request.POST['final']
        year, month, day = map(int, final.split('-'))
        final = datetime.datetime(year, month, day, 23, 59, 59)

        mostra_vendas = request.POST.getlist('vendas')
        vendedor = request.POST['vendedor']

        movimentacoes = Movimentacoes()
        movimentacoes.set_query_t('PreVenda')
        movimentacoes.set_query_periodo(inicial, final)
        if vendedor != '':
            movimentacoes.set_query_vendedor_id(vendedor)
        movimentacoes.set_query_situacao_codigo(12, 1)
        movimentacoes.set_query_convertida('False')
        movimentacoes.set_limit(0)
        cursor = movimentacoes.execute_all()

        # Gerando totais das vendas
        uteis = Uteis()
        cursor = uteis.totais(cursor)

        for venda in cursor['vendas']:
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

                # Verificando se é pra exibir as vendas
                if mostra_vendas != []:
                    # Coletando vendas para exibição
                    vendas[vendedor_id]['vendas'].append(
                        {
                            'numero': venda['Numero'],
                            'data': venda['DataHoraEmissao'],
                            'comissao': venda['comissao'],
                            'desconto': venda['desconto'],
                            'bruto': venda['bruto'],
                            'liquido': venda['liquido']
                        }
                    )

                # Gerando totais de vendendor
                vendas[vendedor_id]['bruto'] = vendas[vendedor_id]['bruto'] + venda['bruto']
                vendas[vendedor_id]['liquido'] = vendas[vendedor_id]['liquido'] + venda['liquido']
                vendas[vendedor_id]['desconto'] = vendas[vendedor_id]['desconto'] + venda['desconto']
                vendas[vendedor_id]['comissao'] = vendas[vendedor_id]['comissao'] + venda['comissao']

        context = {
            'comissao': cursor['comissao'],
            'liquido': cursor['liquido'],
            'desconto': cursor['desconto'],
            'bruto': cursor['bruto'],
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
        movimentacoes.set_query_situacao_codigo(12, 1)
        movimentacoes.set_query_convertida('False')
        movimentacoes.set_limit(0)
        cursor = movimentacoes.execute_all()

        # Gerando totais das vendas
        uteis = Uteis()
        cursor = uteis.totais(cursor)

        # Tratando dados e separação por usuarios
        for venda in cursor['vendas']:
            usuario = venda['Historicos'][0]['NomeUsuario']

            # Separando usuarios
            if usuario not in vendas:
                vendas[usuario] = {}
                vendas[usuario]['bruto'] = 0
                vendas[usuario]['desconto'] = 0
                vendas[usuario]['liquido'] = 0
                vendas[usuario]['vendas'] = []

            # Verificando se é pra exibir vendas
            if mostra_vendas != []:
                # Coletando vendas para exibição
                vendas[usuario]['vendas'].append(
                    {
                        "numero": venda["Numero"],
                        "data": venda["DataHoraEmissao"],
                        "desconto": venda['desconto'],
                        "bruto": venda['bruto'],
                        "liquido": venda['liquido']
                    }
                )

            # Gerando totais de usuario
            vendas[usuario]['bruto'] = vendas[usuario]['bruto'] + venda['bruto']
            vendas[usuario]['liquido'] = vendas[usuario]['liquido'] + venda['liquido']
            vendas[usuario]['desconto'] = vendas[usuario]['desconto'] + venda['desconto']

        context = {
            'liquido': cursor['liquido'],
            'desconto': cursor['desconto'],
            'bruto': cursor['bruto'],
            'vendas': vendas,
            'inicial': inicial,
            'final': final
        }
        return render(request, 'relatorios/prevendas_por_usuario.html', context)
    else:
        return redirect('relatorios:index')