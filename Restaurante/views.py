import datetime
from bson import ObjectId
import math

from django.core import exceptions
from django.shortcuts import render, redirect
from .models import ItensMesaContaMongo, CardapiosMongo, MesasConta
from Pessoas.models import PessoasMongo
from Estoque.models import Products
from core.models import Configuracoes, Uteis
from django.contrib.auth.decorators import login_required, user_passes_test


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.index'))
def index(request):
    template_name = 'restaurante/index.html'
    context = {}
    db_mesas = ItensMesaContaMongo()
    db_mesas.set_query_situacao(2)
    db_mesas.set_sort_numero_mesa()
    db_mesas.set_sort_numero_mesa_conta()
    db_mesas.set_sort_data_hora()
    data = {}
    for item in db_mesas.execute_all():
        if item['Cancelado'] is False:
            if 0 != item['NumeroMesaConta'] in data:
                data[item['NumeroMesaConta']]['Totalizacao'] += \
                    item['ValorUnitario'] * item['Quantidade']

            if 0 != item['NumeroMesa'] in data:
                data[item['NumeroMesa']]['Totalizacao'] += \
                    item['ValorUnitario'] * item['Quantidade']

        item['Totalizacao'] = item['ValorUnitario'] * item['Quantidade'] \
            if item['Cancelado'] is False else 0

        if 0 != item['NumeroMesaConta'] not in data:
            data[item['NumeroMesaConta']] = item

        if 0 != item['NumeroMesa'] not in data:
            data[item['NumeroMesa']] = item

    context['data'] = data
    return render(request, template_name, context)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.mesa_conta'))
def mesa_conta(request, conta=False, mesa=False):
    template_name = 'restaurante/mesa_conta.html'
    context = {}

    # Carregando Cardapios
    db_cardapio = CardapiosMongo()
    db_cardapio.aggregate_produto_servico_referencia()
    db_cardapio.group_itens_cardapio()
    context['cardapios'] = db_cardapio.execute_all()

    # Carregando mesas para exibir os itens
    db_mesas = ItensMesaContaMongo()
    if conta is not False:
        db_mesas.set_query_numero_mesa_conta(int(conta))
    else:
        db_mesas.set_query_numero_mesa(int(mesa))
    db_mesas.set_query_situacao(2)
    db_mesas.set_aggregate_garcom()
    context['mesa_conta'] = db_mesas.execute_all()
    context['total'] = 0
    x = 0
    for item in context['mesa_conta']:
        total_item = item['ValorUnitario'] * item['Quantidade']
        if item['Cancelado'] is False:
            context['total'] += total_item
        context['mesa_conta'][x]['total'] = total_item
        context['mesa_conta'][x]['Observacoes'] = ', '.join(
            item['Observacoes'])
        x += 1
    pessoas_db = PessoasMongo()
    pessoas_db.set_query_vendedor()
    pessoas_db.set_query_ativo()
    context['vendedores'] = pessoas_db.execute_all()
    return render(request, template_name, context)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.add_item'))
def get_add_item_mesa(request, item, conta=False, mesa=False):
    template_name = 'restaurante/form_itens_faltantes.html'
    context = {}

    estoque_db = Products()
    estoque_db.set_query_id(item)
    estoque_db.set_aggregate_produtos_servicos()
    estoque_db.set_collection('2')
    produto = estoque_db.execute_all()
    if len(produto) == 1:
        context['produto'] = produto[0]
    else:
        print("Erro na busca do produto")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)

    pessoas_db = PessoasMongo()
    pessoas_db.set_query_vendedor()
    pessoas_db.set_query_ativo()
    context['vendedores'] = pessoas_db.execute_all()
    if len(context['vendedores']) < 1:
        context['vendedores'] = False
    context['conta'] = conta
    context['mesa'] = mesa
    return render(request, template_name, context)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.add_item'))
def set_add_item_mesa(request):
    mesa = False
    conta = False
    vendedor = False
    quantidade = 1
    observacoes = []

    if 'mesa' in request.POST:
        mesa = request.POST['mesa']
    elif 'conta' in request.POST:
        conta = request.POST['conta']
    else:
        print("Não foi enviado mesa/conta")
        return redirect('restaurante:index')

    # Validando se o item foi encontrado
    if 'item' not in request.POST:
        print("Não foi enviado produto")
        return redirect('restaurante:index')
    item = request.POST['item']
    estoque_db = Products()
    estoque_db.set_query_id(item)
    estoque_db.set_aggregate_produtos_servicos()
    estoque_db.set_aggregate_precos()
    estoque_db.set_aggregate_quantidades()
    estoque_db.set_collection('2')
    item = estoque_db.execute_all()
    if len(item) != 1:
        print("Erro na busca do produto")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)
    item = item[0]

    if 'quantidade' not in request.POST:
        print("A quantidade não foi informada")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)

    quantidade = float(request.POST['quantidade'].replace(',', '.'))
    if quantidade <= 0:
        print("A quantidade tem que ser maior que 0")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)

    configuracoes_db = Configuracoes()
    config = configuracoes_db.configuracoes()
    if config['Saida']['PermitirEstoqueNegativo'] is False:
        quantidade_disponivel = 0
        for x in item['Estoques']:
            quantidade_disponivel += x['Quantidade']
        if quantidade > quantidade_disponivel:
            print("A quantidade tem que ser menor que {0}".format(
                quantidade_disponivel)
            )
            if conta is not False:
                return redirect('restaurante:conta', conta)
            if mesa is not False:
                return redirect('restaurante:mesa', mesa)

    if 'vendedor' in request.POST and request.POST['vendedor'] != '0':
        pessoas_db = PessoasMongo()
        pessoas_db.set_query_id(request.POST['vendedor'])
        pessoas_db.set_query_vendedor()
        pessoas_db.set_query_ativo()
        vendedor = pessoas_db.execute_all()
        if len(vendedor) != 1:
            print("Vendedor informado invalido")
            if conta is not False:
                return redirect('restaurante:conta', conta)
            if mesa is not False:
                return redirect('restaurante:mesa', mesa)
        else:
            vendedor = vendedor[0]
    if len(request.POST.getlist('observacoes[]')) > 0:
        observacoes = request.POST.getlist('observacoes[]')

    pessoas_db = PessoasMongo()
    pessoas_db.set_query_emitente()
    pessoas_db.set_query_ativo()
    emitente = pessoas_db.execute_all()
    if len(emitente) == 1:
        emitente = emitente[0]
    else:
        print("Erro na busca do emitente")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)

    template_db = {
        "_id": ObjectId(),
        "_t": "ItemMesaConta",
        "InformacoesPesquisa": [

        ],
        "ProdutoServicoEmpresaReferencia": item['_id'],
        "NumeroMesaConta": int(conta),
        "NumeroMesa": int(mesa),
        "GarcomReferencia": vendedor['_id'] if vendedor is not False else
        ObjectId("000000000000000000000000"),
        "PercentualComissao": vendedor['Vendedor']['PercentualComissao'] if
        vendedor is not False else 0.0,
        "Quantidade": quantidade,
        "Observacoes": observacoes,
        "Impresso": False,
        "Cancelado": False,
        "DataHora": datetime.datetime.now(),
        "NumeroMesaContaOrigem": 0,
        "Descricao": item['ProdutosServicos'][0]['Descricao'],
        "Codigo": item['ProdutosServicos'][0]['CodigoInterno'],
        "Unidade": item['ProdutosServicos'][0]['UnidadeMedida']['Sigla'],
        "ValorUnitario": item['Precos'][0]['Venda']['Valor'],
        "ImpressoraReferencia": item['ImpressoraReferencia'],
        "EmpresaReferencia": emitente['_id'],
        "Situacao": 2,
        "Cer": 0,
        "Coo": 0,
        "NumeroSequencialEcf": 0,
        "ContaEmitida": False
    }
    uteis = Uteis()
    database = uteis.conexao
    database['ItensMesaConta'].insert(template_db)
    Uteis().fecha_conexao()
    if conta is not False:
        return redirect('restaurante:conta', conta)
    if mesa is not False:
        return redirect('restaurante:mesa', mesa)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.fechar_conta'))
def fechar_conta(request):
    mesa = 0
    conta = 0
    id_zero = ObjectId("000000000000000000000000")
    if 'mesa' in request.POST:
        mesa = int(request.POST['mesa'])
    elif 'conta' in request.POST:
        conta = int(request.POST['conta'])
    else:
        print("Não foi enviado mesa/conta")
        return redirect('restaurante:index')

    if 'dinheiro' not in request.POST and 'cartao_credito' not in request.POST \
            and 'cartao_debito' not in request.POST and 'outros' in \
            request.POST:
        print("Não foi enviado nem uma forma de pagamento")
        return redirect('restaurante:index')

    observacao = ''
    if 'observacao' in request.POST:
        observacao = request.POST['observacao']

    dinheiro = float(request.POST['dinheiro'].replace('.', '')
                     .replace(',', '.'))
    cartao_credito = float(request.POST['cartao_credito'].replace('.', '')
                           .replace(',', '.'))
    cartao_debito = float(request.POST['cartao_debito'].replace('.', '')
                          .replace(',', '.'))
    outros = float(request.POST['outros'].replace('.', '')
                   .replace(',', '.'))

    total_pago = dinheiro + cartao_credito + cartao_debito + outros

    # Carregando mesa
    db_mesas = ItensMesaContaMongo()
    db_mesas.set_query_situacao(2)
    db_mesas.set_query_numero_mesa_conta(conta)
    db_mesas.set_query_numero_mesa(mesa)
    mesas_result = db_mesas.execute_all()
    total = 0
    for item in mesas_result:
        if item['Cancelado'] is False:
            total += item['ValorUnitario'] * item['Quantidade']

    if total_pago < float("%.2f" % total):
        print("Não foi enviado o valor total mesa/conta")
        if conta is not False:
            return redirect('restaurante:conta', conta)
        if mesa is not False:
            return redirect('restaurante:mesa', mesa)

    mesa_record = MesasConta.objects.create(
        mesa=mesa,
        conta=conta,
        total=float("%.2f" % total),
        dinheiro=float("%.2f" % dinheiro),
        cartao_credito=float("%.2f" % cartao_credito),
        cartao_debito=float("%.2f" % cartao_debito),
        outros=float("%.2f" % outros)
    )

    for mesa in mesas_result:
        vendedor = False
        comissao = 0
        total_prod = mesa['ValorUnitario'] * mesa['Quantidade']
        if id_zero != mesa['GarcomReferencia']:
            pessoas_db = PessoasMongo()
            pessoas_db.set_query_id(mesa['GarcomReferencia'])
            pessoas_db.set_query_vendedor()
            pessoas_db.set_query_ativo()
            vendedor = pessoas_db.execute_all()
            if len(vendedor) != 1:
                print("Vendedor informado invalido")
                if conta is not False:
                    return redirect('restaurante:conta', conta)
                if mesa is not False:
                    return redirect('restaurante:mesa', mesa)
            else:
                vendedor = vendedor[0]
                comissao = mesa['PercentualComissao'] * total_prod / 100
        item = mesa_record.itens.create(
            id_g6=str(mesa['ProdutoServicoEmpresaReferencia']),
            produto=mesa['Descricao'],
            cancelado=mesa['Cancelado'],
            id_garcom=vendedor['_id']
            if vendedor is not False else '',
            garcom_nome=vendedor['Nome']
            if vendedor is not False else '',
            percent_comissao=mesa['PercentualComissao']
            if vendedor is not False else 0,
            unidade_medida=mesa['Unidade'],
            comissao=comissao,
            quantidade=mesa['Quantidade'],
            unitario=mesa['ValorUnitario'],
            total=float("%.2f" % total_prod)
        )
        db_mesas.fechar_mesa(mesa['_id'])
    return redirect('restaurante:comprovante', mesa_record.id)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.fechar_conta'))
def comprovante(request, id):
    template_name = 'restaurante/comprovante.html'
    context = {}
    pessoas_db = PessoasMongo()
    pessoas_db.set_query_emitente()
    pessoas_db.set_query_ativo()

    emitente = pessoas_db.execute_all()
    context['emitente'] = emitente[0]
    context['id'] = str(id).rjust(5, '0')
    context['comprovante'] = MesasConta.objects.all().filter(id=id)[0]
    context['total_servico'] = context['comprovante'].total * 10 / 100
    context['total_conta_10'] = context['comprovante'].total + \
                                context['total_servico']
    context['total_conta'] = context['comprovante'].total
    context['comprovante_itens'] = ItensMesaContaMongo.objects.all().filter(
        mesa_conta=id
    )
    return render(request, template_name, context)


@login_required(redirect_field_name='next')
@user_passes_test(lambda u: u.has_perm('restaurante.lista_mesas_fechadas'))
def lista_mesas_fechadas(request):
    template_name = 'restaurante/lista_mesas_fechadas.html'

    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    products_visible = request.GET.get('products')
    if products_visible is None:
        products_visible = 1

    if date_start is not None and date_end is not None:
        try:
            year, month, day = map(int, date_start.split('-'))
            date_start = datetime.datetime(year, month, day, 00, 00, 00)

            year, month, day = map(int, date_end.split('-'))
            date_end = datetime.datetime(year, month, day, 23, 59, 59)
            mesas = MesasConta.objects.filter(
                created_at__gte=date_start,
                created_at__lte=date_end
            )
        except ValueError:
            mesas = MesasConta.objects.filter(
                created_at__gte=datetime.date.today())
    else:
        mesas = MesasConta.objects.filter(created_at__gte=datetime.date.today())
    totais = {
        'cartao_debito': 0,
        'cartao_credito': 0,
        'dinheiro': 0,
        'outros': 0,
        'total': 0
    }
    for x in mesas:
        totais['cartao_debito'] += x.cartao_debito
        totais['cartao_credito'] += x.cartao_credito
        totais['dinheiro'] += x.dinheiro
        totais['outros'] += x.outros
        totais['total'] += x.total
    context = {
        'mesas': mesas,
        'totais': totais,
        'products_visible': products_visible,
        'date_start': date_start,
        'date_end': date_end
    }
    return render(request, template_name, context)
