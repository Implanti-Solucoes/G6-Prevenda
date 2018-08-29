from bson import ObjectId
from django.shortcuts import render, redirect
from .models import Products
from .models import Tabela_Preco
from Financeiro.models import Pessoas

def tabela_list(request):
    # Estanciando classes necessarias
    tabelas_class = Tabela_Preco()

    # Consultando todas as tabelas
    tabelas = tabelas_class.list()
    return render(request, 'TabelaPreco/index.html', {'tabelas': tabelas})

def tabela_create(request):
    return render(request, 'TabelaPreco/create.html', {})

def tabela_create_post(request):
    # Estanciando classes necessarias
    tabelas_class = Tabela_Preco()

    # Recebendo valores
    situacao = request.POST.getlist('situacao')
    descricao = request.POST.getlist('descricao')[0]
    tipo = int(request.POST.getlist('tipo')[0])
    porcent = int(request.POST.getlist('porcent')[0])
    base = int(request.POST.getlist('base')[0])

    if not situacao:
        situacao = 0
    else:
        situacao = 1

    # Passando valores para metodo de criação
    retorno = tabelas_class.create(situacao, descricao, tipo, porcent, base)

    # Verificando se foi criado ou não
    if retorno:
        return redirect('estoque:tabelas')
    else:
        return render(request, 'TabelaPreco/create.html', {})

def tabela_edit(request, id):
    # Estanciando classes necessarias
    tabelas_class = Tabela_Preco()
    produtos_class = Products()

    # Consultando tabela de preço no banco
    tabelas = tabelas_class.get(id)

    # Caso não tenha encontrado nem uma tabela, redirecione para listagem, verificação de segurança
    if not tabelas:
        return redirect('estoque:tabelas')

    produtos = produtos_class.list()
    produtos1 = []

    x = 0  # Contador para coloca os valores em 'produtos'
    for produto in produtos:
        if produto['ProdutoServico'][0]['Ativo']:
            valor = 0  # Validação se tem valor personalizador na tabela de preco

            # Varrendo tabela de preço para verifica preços personalizados
            for item in tabelas['Itens']:
                # Verificando se existe preço personalizado na tabela de preço
                if item['PrecoReferencia'] == produto['Precos'][0]['_id']:
                    valor = item['Preco']

            # Não foi encontrado preço personalizado
            if valor == 0:
                # Verificando se a tabela dar Acrescimo ou Desconto
                if tabelas['Operacao']['_t'] == 'Acrescimo':
                    # Verificando qual base de calculo deve ser usado no calculo
                    if tabelas['Operacao']['BaseCalculoTabelaPreco'] == 0:
                        # Aplicando Acrescimo em cima do preço de venda
                        produto['Precos'][0]['Venda']['CValor'] = produto['Precos'][0]['Venda']['Valor'] + (
                                produto['Precos'][0]['Venda']['Valor'] * tabelas['Operacao']['Percentual'] / 100)

                    elif tabelas['Operacao']['BaseCalculoTabelaPreco'] == 1:
                        # Aplicando Acrescimo em cima do preço de custo
                        produto['Precos'][0]['Venda']['CValor'] = produto['Precos'][0]['Custo']['Valor'] + (
                                produto['Precos'][0]['Custo']['Valor'] * tabelas['Operacao']['Percentual'] / 100)

                elif tabelas['Operacao']['_t'] == 'Desconto':
                    if tabelas['Operacao']['BaseCalculoTabelaPreco'] == 0:
                        # Aplicando Desconto em cima do preço de venda
                        produto['Precos'][0]['Venda']['CValor'] = produto['Precos'][0]['Venda']['Valor'] - (
                                produto['Precos'][0]['Venda']['Valor'] * tabelas['Operacao']['Percentual'] / 100)

                    elif tabelas['Operacao']['BaseCalculoTabelaPreco'] == 1:
                        # Aplicando Desconto em cima do preço de custo
                        produto['Precos'][0]['Venda']['CValor'] = produto['Precos'][0]['Custo']['Valor'] - (
                                produto['Precos'][0]['Custo']['Valor'] * tabelas['Operacao']['Percentual'] / 100)

            if valor > 0:
                produto['Precos'][0]['Venda']['PValor'] = valor

            produtos1.append(produto)
        x = x + 1

    # Criando variavel context
    contex = {
        'tabelas': tabelas,
        'produtos': produtos1,
    }
    return render(request, 'TabelaPreco/edit.html', contex)

def tabela_edit_post(request):
    from core.models import Uteis

    # Estanciando classes necessarias
    produtos_class = Products()
    pessoas_class = Pessoas()
    tabelas_class = Tabela_Preco()
    uteis = Uteis()

    # Recebendo valores
    id = request.POST['id']
    id_prod = request.POST.getlist('id_prod[]')
    price = request.POST.getlist('price[]')

    # Chamando metodos necessarios
    emitente = pessoas_class.get_emitente()
    tabelas = tabelas_class.get(id)
    database = uteis.conexao

    # Declarando variaveis uteis
    produtos = []
    tabelas['Itens'] = []
    x = 0

    # Percorrendo produtos para verificar se estão corretos
    for id in id_prod:
        if price[x] != '' and type(id_prod[x]) == str and len(id_prod[x]) == 24:
            preco = produtos_class.get_precos(id)
            tabelas['Itens'].append({
                'PrecoReferencia': ObjectId(id_prod[x]),
                'Preco': float(price[x].replace(',', '.')),
                'EmpresaReferencia': emitente['_id'],
                'Hash': preco[0]['Venda']['Hash']
            })
        x = x+1
    del tabelas['id']
    database['TabelasPreco'].replace_one({'_id': tabelas['_id']}, tabelas)
    uteis.fecha_conexao()
    return redirect('estoque:tabelas')
