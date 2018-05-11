from django.shortcuts import render
from pymongo import MongoClient
from datetime import timedelta

client = MongoClient('localhost', username='revenda', password='r3v3nd@', authSource='DigisatServer', port=12220)
database = client["DigisatServer"]
collection = database["Movimentacoes"]

def impresso(request):
    #Filtro de campos
    query = {}

    # Campos selecionados
    projection = {}
    projection["Numero"] = 1.0
    projection["DataHoraEmissao"] = 1.0
    projection["Pessoa.Nome"] = 1.0
    sort = [(u"Numero", -1)]
    item = []
    cursor = collection.find(query, projection=projection, sort = sort)
    for doc in cursor:
        item.append(doc)
        print(doc)

    context = {"items": item}
    return render(request, 'listagem.html', context)

def impressoid(request, id):
    #Filtro de campos
    query = {"Numero": int(id)}

    #Campos selecionados
    projection = {}
    projection["Numero"] = 1.0
    projection["ItensBase"] = 1.0
    projection["Pessoa"] = 1.0
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

    for item in cursor["ItensBase"]:
        items.extend([{"Codigo":item['ProdutoServico']['CodigoInterno'],
                       "Descricao": item['ProdutoServico']['Descricao'],
                       "Unidade": item['ProdutoServico']["UnidadeMedida"]["Sigla"],
                       "Qtd": item['Quantidade'],
                       "Preco": item['PrecoUnitario'],
                       "Total": item['Quantidade'] * item['PrecoUnitario']}])


        context = {"Numero": str(cursor['Numero']), "Items": items, "Cliente":cliente}
        return render(request, 'impresso.html', context)

