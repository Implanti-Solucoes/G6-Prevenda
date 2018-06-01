from django.shortcuts import render
from bson import ObjectId
from .models import Movimentacoes

def listagem_prevenda(request):
    movimentacoes = Movimentacoes()
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_projection_numero()
    movimentacoes.set_projection_emissao()
    movimentacoes.set_projection_pessoa_nome()
    item = movimentacoes.execute_all()
    context = {"items": item}
    return render(request, 'pre_venda/listagem.html', context)

def impresso_prevenda(request, id):
    telefone = ""
    tipo = ""
    documento = ""
    items = []

    movimentacoes = Movimentacoes()

    movimentacoes.set_query_id(ObjectId(id))
    movimentacoes.set_query_t('PreVenda')
    movimentacoes.set_projection_numero()
    movimentacoes.set_projection_pessoa()
    movimentacoes.set_projection_itens()
    movimentacoes.set_projection_empresa()
    cursor = movimentacoes.execute_one()

    if "TelefonePrincipal" in cursor["Pessoa"]:
        telefone = cursor["Pessoa"]["TelefonePrincipal"]

    if cursor["Pessoa"]["_t"] == "FisicaHistorico":
        tipo = "CPF: "
        documento = cursor["Pessoa"]["Documento"]
    elif cursor["Pessoa"]["_t"] == "EmpresaHistorico":
        tipo = "CNPJ: "
        documento = cursor["Pessoa"]["Documento"]


    cliente ={"Nome": cursor["Pessoa"]["Nome"],
              "Logradouro": cursor["Pessoa"]["EnderecoPrincipal"]["Logradouro"],
              "Numero":cursor["Pessoa"]["EnderecoPrincipal"]["Numero"],
              "Bairro":cursor["Pessoa"]["EnderecoPrincipal"]["Bairro"],
              "Cep":cursor["Pessoa"]["EnderecoPrincipal"]["Cep"],
              "Municipio":cursor["Pessoa"]["EnderecoPrincipal"]["Municipio"]["Nome"],
              "Uf":cursor["Pessoa"]["EnderecoPrincipal"]["Municipio"]["Uf"]["Sigla"],
              "Telefone": telefone,
              "Tipo":tipo,
              "Documento":documento
    }
    Empresa ={"Nome": cursor["Empresa"]["Nome"],
              "Logradouro": cursor["Empresa"]["EnderecoPrincipal"]["Logradouro"],
              "Numero": cursor["Empresa"]["EnderecoPrincipal"]["Numero"],
              "Bairro": cursor["Empresa"]["EnderecoPrincipal"]["Bairro"],
              "Cep": cursor["Empresa"]["EnderecoPrincipal"]["Cep"],
              "Municipio": cursor["Empresa"]["EnderecoPrincipal"]["Municipio"]["Nome"],
              "Uf": cursor["Empresa"]["EnderecoPrincipal"]["Municipio"]["Uf"]["Sigla"],
              "Telefone": cursor["Empresa"]["TelefonePrincipal"],
              "Tipo": "CNPJ: ",
              "Documento": cursor["Empresa"]["Documento"]
    }
    Total_Produtos = 0
    Total_Desconto = 0

    for item in cursor["ItensBase"]:
        items.extend([{"Codigo":item['ProdutoServico']['CodigoInterno'],
                       "Descricao": item['ProdutoServico']['Descricao'],
                       "Unidade": item['ProdutoServico']["UnidadeMedida"]["Sigla"],
                       "Qtd": item['Quantidade'],
                       "Desconto": item['DescontoDigitado'] + item['DescontoProporcional'],
                       "Preco": item['PrecoUnitario'],
                       "Total": item['Quantidade'] * item['PrecoUnitario']}])
        Total_Produtos = Total_Produtos + (item['Quantidade'] * item['PrecoUnitario'])
        Total_Desconto = Total_Desconto + item['DescontoDigitado'] + item['DescontoProporcional']
    Total = Total_Produtos - Total_Desconto

    context = {"Numero": str(cursor['Numero']),
               "Items": items,
               "Cliente":cliente,
               "Empresa": Empresa,
               "Total_Produtos": Total_Produtos,
               "Total_Desconto": Total_Desconto,
               "Total": Total
               }
    return render(request, 'pre_venda/impresso.html', context)

def relatorios(request):
    movimentacoes = Movimentacoes()
    relatorios = {
        1: 'Sintetico de Produtos Pré-Venda',
        2: 'Operações por Pessoa',
        3: 'Vendas por forma de pagamento',
        4: 'Pré-Vendas no periodo',
    }
    clientes = movimentacoes.get_clientes()
    print(clientes)
    return render(request, 'relatorios/index.html', {'relatorios':relatorios, 'clientes':clientes})

def produtos_sintetico(request):
    pass