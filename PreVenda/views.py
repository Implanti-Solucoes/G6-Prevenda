from django.shortcuts import render
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('localhost', username='revenda', password='r3v3nd@', authSource='DigisatServer', port=12220)
database = client["DigisatServer"]
collection = database["Movimentacoes"]

def listagem(request):
    #Filtro de campos
    query = {}

    # Campos selecionados
    projection = {}
    projection["Numero"] = 1.0
    projection["DataHoraEmissao"] = 1.0
    projection["Pessoa.Nome"] = 1.0
    sort = [(u"DataHoraEmissao", -1)]
    item = []
    cursor = collection.find(query, projection=projection, sort = sort).limit(500)
    for doc in cursor:
        doc['id'] = str(doc['_id'])
        item.append(doc)
    context = {"items": item}
    return render(request, 'PreVenda/listagem.html', context)

def impresso(request, id):
    #Filtro de campos
    query = {"_id": ObjectId(id)}

    #Campos selecionados
    projection = {}
    projection["Numero"] = 1.0
    projection["ItensBase"] = 1.0
    projection["Pessoa"] = 1.0
    projection["Empresa"] = 1.0

    items = []
    cursor = collection.find_one(query, projection=projection)
    if "TelefonePrincipal" in cursor["Pessoa"]:
        telefone = cursor["Pessoa"]["TelefonePrincipal"]
    else:
        telefone = ""

    if cursor["Pessoa"]["_t"] == "FisicaHistorico":
        tipo = "CPF: "
        documento = cursor["Pessoa"]["Documento"]
    elif cursor["Pessoa"]["_t"] == "EmpresaHistorico":
        tipo = "CNPJ: "
        documento = cursor["Pessoa"]["Documento"]
    else:
        tipo = ""
        documento = ""


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
    return render(request, 'PreVenda/impresso.html', context)

