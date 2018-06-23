import datetime

from django.shortcuts import render, redirect
from .models import Movimentacoes
from Financeiro.models import Financeiro


def listagem_prevenda(request):
    movimentacoes = Movimentacoes()
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_projection_numero()
    movimentacoes.set_projection_emissao()
    movimentacoes.set_projection_pessoa_nome()
    movimentacoes.set_projection_situacao()
    movimentacoes.set_sort_emissao()
    item = movimentacoes.execute_all()
    context = {'items': item}
    return render(request, 'pre_venda/listagem.html', context)


def impresso_prevenda(request, id):
    telefone = ''
    tipo = ''
    documento = ''
    items = []

    movimentacoes = Movimentacoes()

    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_projection_numero()
    movimentacoes.set_projection_pessoa()
    movimentacoes.set_projection_itens()
    movimentacoes.set_projection_empresa()
    cursor = movimentacoes.execute_one()

    if 'TelefonePrincipal' in cursor['Pessoa']:
        telefone = cursor['Pessoa']['TelefonePrincipal']

    if cursor['Pessoa']['_t'] == 'FisicaHistorico':
        tipo = 'CPF: '
        documento = cursor['Pessoa']['Documento']
    elif cursor['Pessoa']['_t'] == 'EmpresaHistorico':
        tipo = 'CNPJ: '
        documento = cursor['Pessoa']['Documento']

    cliente = {'Nome': cursor['Pessoa']['Nome'],
               'Logradouro': cursor['Pessoa']['EnderecoPrincipal']['Logradouro'],
               'Numero': cursor['Pessoa']['EnderecoPrincipal']['Numero'],
               'Bairro': cursor['Pessoa']['EnderecoPrincipal']['Bairro'],
               'Cep': cursor['Pessoa']['EnderecoPrincipal']['Cep'],
               'Municipio': cursor['Pessoa']['EnderecoPrincipal']['Municipio']['Nome'],
               'Uf': cursor['Pessoa']['EnderecoPrincipal']['Municipio']['Uf']['Sigla'],
               'Telefone': telefone,
               'Tipo': tipo,
               'Documento': documento
               }
    Empresa = {'Nome': cursor['Empresa']['Nome'],
               'Logradouro': cursor['Empresa']['EnderecoPrincipal']['Logradouro'],
               'Numero': cursor['Empresa']['EnderecoPrincipal']['Numero'],
               'Bairro': cursor['Empresa']['EnderecoPrincipal']['Bairro'],
               'Cep': cursor['Empresa']['EnderecoPrincipal']['Cep'],
               'Municipio': cursor['Empresa']['EnderecoPrincipal']['Municipio']['Nome'],
               'Uf': cursor['Empresa']['EnderecoPrincipal']['Municipio']['Uf']['Sigla'],
               'Telefone': cursor['Empresa']['TelefonePrincipal'],
               'Tipo': 'CNPJ: ',
               'Documento': cursor['Empresa']['Documento']
               }

    Total_Produtos = 0
    Total_Desconto = 0

    for item in cursor['ItensBase']:
        items.extend([{'Codigo': item['ProdutoServico']['CodigoInterno'],
                       'Descricao': item['ProdutoServico']['Descricao'],
                       'Unidade': item['ProdutoServico']['UnidadeMedida']['Sigla'],
                       'Qtd': item['Quantidade'],
                       'Desconto': item['DescontoDigitado'] + item['DescontoProporcional'],
                       'Preco': item['PrecoUnitario'],
                       'Total': item['Quantidade'] * item['PrecoUnitario']}])
        Total_Produtos = Total_Produtos + (item['Quantidade'] * item['PrecoUnitario'])
        Total_Desconto = Total_Desconto + item['DescontoDigitado'] + item['DescontoProporcional']
    Total = Total_Produtos - Total_Desconto

    context = {'Numero': str(cursor['Numero']),
               'Items': items,
               'Cliente': cliente,
               'Empresa': Empresa,
               'Total_Produtos': Total_Produtos,
               'Total_Desconto': Total_Desconto,
               'Total': Total
               }
    return render(request, 'pre_venda/impresso.html', context)

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

    return render(request, 'pre_venda/gerar_financeiro.html', context)

def relatorios(request):
    movimentacoes = Movimentacoes()
    if request.method != 'POST':
        relatorios = {
            1: 'Operações por pessoa',
            #2: 'Vendas por Forma de Pagamento',
            #3: 'Pre-Vendas no período',
            4: 'Sinteticos de produtos',
        }
        clientes = movimentacoes.get_clientes()
        context = {}
        context['clientes'] = clientes
        context['relatorios'] = relatorios

        return render(request, 'relatorios/form.html', context)
    else:
        relatorio = int(request.POST['relatorio'])
        if relatorio == 1:
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
            return render(request, 'relatorios/pessoa_impresso.html', context)
        elif relatorio == 4:
            produtos = {}

            cliente = request.POST['cliente']
            inicial = request.POST['inical']
            year, month, day = map(int, inicial.split('-'))
            inicial = datetime.datetime(year, month, day, 00, 00, 00)

            final = request.POST['final']
            year, month, day = map(int, final.split('-'))
            final = datetime.datetime(year, month, day, 23, 59, 59)

            if len(cliente) == 24:
                movimentacoes.set_query_pessoa_id(cliente)

            movimentacoes.set_query_t('PreVenda')
            movimentacoes.set_query_periodo(inicial, final)
            movimentacoes.set_projection_itens()
            cursor = movimentacoes.execute_all()

            for x in cursor:
                for y in x['ItensBase']:
                    id = str(y['ProdutoServico']['ProdutoServicoReferencia'])
                    if id in produtos:
                        produtos[id]['Qtd'] = produtos[id]['Qtd'] + y['Quantidade']
                        produtos[id]['Total'] = produtos[id]['Total'] + (y['Quantidade'] * y['PrecoUnitario'])
                    else:
                        produtos[id] = {}
                        produtos[id]['Descricao'] = y['ProdutoServico']['Descricao']
                        produtos[id]['Qtd'] = y['Quantidade']
                        produtos[id]['Total'] = y['Quantidade'] * y['PrecoUnitario']

            return render(request, 'relatorios/pagamento_impresso.html', {'produtos': produtos})