from django.shortcuts import render
from Pessoas.models import PessoasMongo
from Financeiro.models import Contratos


def listagem(request):
    template_name = 'pessoas/index.html'
    clientes = PessoasMongo().get_clientes()
    clientes1 = []
    for cliente in clientes:
        contratos = Contratos.objects.all()
        cliente['cont_can'] = len(contratos.filter(id_g6_cliente=str(cliente['_id']), excluido=True))
        cliente['cont_ati'] = len(contratos.filter(id_g6_cliente=str(cliente['_id']), excluido=False))
        clientes1.append(cliente)
    context = {'clientes': clientes1}
    return render(request, template_name, context)

