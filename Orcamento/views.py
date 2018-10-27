import datetime

from django.shortcuts import render
from Pessoas.models import PessoasMongo
from Estoque.models import Products
from core.models import Configuracoes


def create_form(request):
    emitente = PessoasMongo().get_emitente()
    clientes = PessoasMongo().get_clientes()
    produtos = Products().list()
    emitente['Cnpj'] = '%s.%s.%s/%s-%s' % (
        emitente['Cnpj'][0:2],
        emitente['Cnpj'][2:5],
        emitente['Cnpj'][5:8],
        emitente['Cnpj'][8:12],
        emitente['Cnpj'][12:14]
    )

    context = {
        'emitente': emitente,
        'clientes': clientes,
        'produtos': produtos,
    }
    return render(request, 'orcamento/create.html', context)


def xml_consulta(request):
    id = request.GET['id']
    if type(id) == str and len(id) == 24:
        pass
    else:
        print(id)
    context = {'ok': Products().get_full_product(id=id)}
    return render(request, 'orcamento/xml_consulta.xml', context, content_type="text/xml; charset=utf-8")


def create(request):
    cliente = request.POST['cliente']
    veiculo = request.POST['veiculo']
    placa = request.POST['placa']
    garantia = request.POST['garantia']
    pagamento = request.POST['pagamento']

    produtos = request.POST.getlist('id[]')
    quantidades = request.POST.getlist('qtd[]')
    descontos = request.POST.getlist('desconto[]')
    precos = request.POST.getlist('preco_unitario[]')

    if len(produtos) == len(quantidades):
        pass

    if len(produtos) == len(descontos):
        pass

    if len(produtos) == len(precos):
        pass

    if PessoasMongo().get_pessoa(cliente):
        pass

    cliente = PessoasMongo().get_pessoa(cliente)
    ultimo_numero = Configuracoes().ultimo_numero()
    ultimo_numero = ultimo_numero['Contador']+1

    insert_dict = {
        '_t': [
            'Movimentacao',
            'DocumentoAuxiliar',
            'DocumentoAuxiliarPrevisao',
            'Orcamento'
        ],
        'InformacoesPesquisa': cliente['InformacoesPesquisa'],
        'Versao': '736961.14:18:47.2681489',
        'Ativo': True,
        'Numero': ultimo_numero,
        'DataHoraEmissao': datetime.datetime.now(),
    }
    insert_dict['InformacoesPesquisa'].append(ultimo_numero)

