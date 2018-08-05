import datetime

from django.shortcuts import render
from .models import Movimentacoes
from Financeiro.models import Financeiro


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
    return render(request, 'movimentacoes/impresso.html', context)

def impresso_dav_80(request, id):
    movimentacoes = Movimentacoes()
    movimentacoes.set_query_id(id)
    movimentacoes.set_query_t('DocumentoAuxiliarVenda')
    cursor = movimentacoes.execute_one()

    return render(request, 'movimentacoes/impresso_dav_80mm.html', {'item':cursor})

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