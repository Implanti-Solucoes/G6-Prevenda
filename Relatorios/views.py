import datetime
import os

from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import render, redirect
from Pessoas.models import PessoasMongo
from Movimentacoes.models import Movimentacoes
from core.models import Uteis


def index(request):
    movimentacoes = Movimentacoes()
    if request.method != 'POST':
        pessoas = PessoasMongo()
        pessoas.set_query_client()
        clientes = pessoas.execute_all()

        pessoas = PessoasMongo()
        pessoas.set_query_vendedor()
        vendedores = pessoas.execute_all()
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


def listagem_produtos_personalizado1(request):
    context = {'data': []}
    uteis = Uteis()
    database = uteis.conexao

    pipeline = [
        {
            u"$lookup": {
                u"from": u"ProdutosServicosEmpresa",
                u"localField": u"_id",
                u"foreignField": u"ProdutoServicoReferencia",
                u"as": u"ProdutosServicosEmpresa"
            }
        },
        {
            u"$lookup": {
                u"from": u"Estoques",
                u"localField": u"ProdutosServicosEmpresa.0.EstoqueReferencia",
                u"foreignField": u"_id",
                u"as": u"Estoques"
            }
        },
        {
            u"$lookup": {
                u"from": u"SubGrupos",
                u"localField": u"SubGrupoReferencia",
                u"foreignField": u"_id",
                u"as": u"SubGrupoReferencia"
            }
        },
        {
            u"$lookup": {
                u"from": u"Precos",
                u"localField": u"ProdutosServicosEmpresa.0.PrecoReferencia",
                u"foreignField": u"_id",
                u"as": u"Precos"
            }
        },
        {
            u"$lookup": {
                u"from": u"TributacoesEstadual",
                u"localField": u"ProdutosServicosEmpresa.0.TributacaoEstadualReferencia",
                u"foreignField": u"_id",
                u"as": u"TributacoesEstadual"
            }
        },
        {
            u"$lookup": {
                u"from": u"TributacoesFederal",
                u"localField": u"ProdutosServicosEmpresa.0.TributacaoFederalReferencia",
                u"foreignField": u"_id",
                u"as": u"TributacoesFederal"
            }
        },
        {
            u"$lookup": {
                u"from": u"TributacoesIPI",
                u"localField": u"TributacoesFederal.0.TributacaoIpiReferencia",
                u"foreignField": u"_id",
                u"as": u"TributacoesIPI"
            }
        },
        {
            u"$lookup": {
                u"from": u"TributacoesPISCOFINS",
                u"localField": u"TributacoesFederal.0.TributacaoPisCofinsReferencia",
                u"foreignField": u"_id",
                u"as": u"TributacoesPISCOFINS"
            }
        },
        {
            u"$lookup": {
                u"from": u"RelacoesProdutoFornecedor",
                u"localField": u"ProdutosServicosEmpresa.0._id",
                u"foreignField": u"ProdutoServicoEmpresaReferencia",
                u"as": u"RelacoesProdutoFornecedor"
            }
        }
    ]
    collection = database["ProdutosServicos"]
    Pessoas = database["Pessoas"]
    cursor = collection.aggregate(
        pipeline,
        allowDiskUse=False
    )
    from openpyxl import Workbook
    import tempfile
    diretor = tempfile.gettempdir()
    arquivo_excel = Workbook()
    planilha1 = arquivo_excel.active
    planilha1.title = "Produtos"
    planilha1['A1'] = 'Código'
    planilha1['B1'] = 'Cód. Barras'
    planilha1['C1'] = 'Fornecedor'
    planilha1['D1'] = 'Descrição'
    planilha1['E1'] = 'Grupo'
    planilha1['F1'] = 'Subgrupo'
    planilha1['G1'] = 'Quantidade'
    planilha1['H1'] = 'Preço Venda'
    planilha1['I1'] = 'Preço Custo'
    planilha1['J1'] = 'Tributação Estadual'
    planilha1['K1'] = 'CST IPI de Compra'
    planilha1['L1'] = 'CST IPI de Venda'
    planilha1['M1'] = 'CST PIS de Compra'
    planilha1['N1'] = 'CST PIS de Venda'
    planilha1['O1'] = 'CST CONFINS de Compra'
    planilha1['P1'] = 'CST CONFINS de Venda'
    planilha1['Q1'] = 'Última Compra'
    planilha1['R1'] = 'Última Venda'
    planilha1['S1'] = 'NCM'
    planilha1['T1'] = 'CEST'
    planilha1['U1'] = 'Ativo'
    try:
        cont = 1
        for x in cursor:
            cont += 1
            planilha1['A'+str(cont)] = x['CodigoInterno']
            planilha1['B'+str(cont)] = x['CodigoBarras'] if 'CodigoBarras' in x else ''

            fornecedores = ''
            for fornecedor in x['RelacoesProdutoFornecedor']:
                cursor = Pessoas.find_one({"_id": fornecedor['FornecedorReferencia']}, projection={"Nome": 1.0})
                fornecedores += cursor['Nome'] + "; "
            planilha1['C' + str(cont)] = fornecedores

            planilha1['D'+str(cont)] = x['Descricao']
            if len(x['SubGrupoReferencia']) > 0:
                planilha1['E'+str(cont)] = x['SubGrupoReferencia'][0]['GrupoDescricao']
                planilha1['F'+str(cont)] = x['SubGrupoReferencia'][0]['Descricao']
            else:
                planilha1['E'+str(cont)] = ''
                planilha1['F'+str(cont)] = ''

            planilha1['G'+str(cont)] = x['Estoques'][0]['Quantidades'][0]['Quantidade'] if len(x['Estoques'][0]['Quantidades']) > 0 else 0
            planilha1['H'+str(cont)] = x['Precos'][0]['Venda']['Valor']
            planilha1['I'+str(cont)] = x['Precos'][0]['Custo']['Valor']
            planilha1['J'+str(cont)] = x['TributacoesEstadual'][0]['Descricao']
            planilha1['K'+str(cont)] = '{} - {}'.format(
                x['TributacoesIPI'][0]['IpiEntrada']['CstIPI']['Codigo'],
                x['TributacoesIPI'][0]['IpiEntrada']['CstIPI']['Descricao']
            )
            planilha1['L'+str(cont)] = '{} - {}'.format(
                x['TributacoesIPI'][0]['IpiSaida']['CstIPI']['Codigo'],
                x['TributacoesIPI'][0]['IpiSaida']['CstIPI']['Descricao']
            )
            planilha1['M'+str(cont)] = '{} - {}'.format(
                x['TributacoesPISCOFINS'][0]['PISEntrada']['CstPISCOFINS']['Codigo'],
                x['TributacoesPISCOFINS'][0]['PISEntrada']['CstPISCOFINS']['Descricao']
            )
            planilha1['N'+str(cont)] = '{} - {}'.format(
                x['TributacoesPISCOFINS'][0]['PISSaida']['CstPISCOFINS']['Codigo'],
                x['TributacoesPISCOFINS'][0]['PISSaida']['CstPISCOFINS']['Descricao']
            )
            planilha1['O'+str(cont)] = '{} - {}'.format(
                x['TributacoesPISCOFINS'][0]['COFINSEntrada']['CstPISCOFINS']['Codigo'],
                x['TributacoesPISCOFINS'][0]['COFINSEntrada']['CstPISCOFINS']['Descricao']
            )
            planilha1['P'+str(cont)] = '{} - {}'.format(
                x['TributacoesPISCOFINS'][0]['COFINSSaida']['CstPISCOFINS']['Codigo'],
                x['TributacoesPISCOFINS'][0]['COFINSSaida']['CstPISCOFINS']['Descricao']
            )
            planilha1['Q'+str(cont)] = x['Estoques'][0]['DataUltimaCompra']
            planilha1['R'+str(cont)] = x['Estoques'][0]['DataUltimaVenda']
            planilha1['S'+str(cont)] = x['ProdutosServicosEmpresa'][0]['NcmNbs']['Codigo']
            if 'CodigoEspecificadorSubstituicaoTributaria' in x['ProdutosServicosEmpresa'][0]:
                planilha1['T'+str(cont)] = x['ProdutosServicosEmpresa'][0]['CodigoEspecificadorSubstituicaoTributaria']
            else:
                planilha1['T' + str(cont)] = ''
            planilha1['U'+str(cont)] = x['Ativo']
    finally:
        uteis.fecha_conexao()
    arquivo_excel.save(os.path.join(diretor, "relatorio.xlsx"))
    with open(os.path.join(diretor, "relatorio.xlsx"), "rb") as excel:
        data = excel.read()
    response = HttpResponse(data,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=relatorio.xlsx'
    os.remove(os.path.join(diretor, "relatorio.xlsx"))
    return response

