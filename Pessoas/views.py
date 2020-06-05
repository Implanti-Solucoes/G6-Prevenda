from django.shortcuts import render
from Pessoas.models import PessoasMongo
from Financeiro.models import Contratos
from core.models import Configuracoes


def listagem(request):
    template_name = 'pessoas/index.html'
    cursor = PessoasMongo()
    cursor.set_query_client()
    cursor.set_query_ativo()
    clientes = cursor.execute_all()
    clientes1 = []
    for cliente in clientes:
        contratos = Contratos.objects.all()
        cliente['cont_can'] = len(contratos.filter(id_g6_cliente=str(cliente['_id']), excluido=True))
        cliente['cont_ati'] = len(contratos.filter(id_g6_cliente=str(cliente['_id']), excluido=False))
        clientes1.append(cliente)
    context = {'clientes': clientes1}
    for x in Configuracoes.objects.all().filter(usuario_id=request.user.id):
        context[x.registro] = x.valor
    return render(request, template_name, context)

