from django.shortcuts import render
from .models import ItensMesaContaMongo, CardapiosMongo


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
        if 0 != item['NumeroMesaConta'] not in data:
            item['Totalizacao'] = item['ValorUnitario'] * item['Quantidade']
            data[item['NumeroMesaConta']] = item
        if 0 != item['NumeroMesa'] not in data:
            item['Totalizacao'] = item['ValorUnitario'] * item['Quantidade']
            data[item['NumeroMesa']] = item
        if 0 != item['NumeroMesaConta'] in data:
            data[item['NumeroMesaConta']]['Totalizacao'] += \
                item['ValorUnitario'] * item['Quantidade']
        if 0 != item['NumeroMesa'] in data:
            data[item['NumeroMesa']]['Totalizacao'] += \
                item['ValorUnitario'] * item['Quantidade']
    context['data'] = data
    return render(request, template_name, context)


def mesa_conta(request, conta=False, mesa=False):
    template_name = 'restaurante/mesa_conta.html'
    context = {}
    db_cardapio = CardapiosMongo()
    db_cardapio.aggregate_produto_servico_referencia()
    db_cardapio.group_itens_cardapio()
    context['cardapios'] = db_cardapio.execute_all()
    print(context['cardapios'])
    db_mesas = ItensMesaContaMongo()
    if conta is not False:
        db_mesas.set_query_numero_mesa_conta(int(conta))
    else:
        db_mesas.set_query_numero_mesa(int(mesa))
    db_mesas.set_query_situacao(2)
    db_mesas.set_aggregate_garcom()
    context['mesa_conta'] = db_mesas.execute_all()
    return render(request, template_name, context)
