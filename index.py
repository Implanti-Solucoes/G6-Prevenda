# Requires pymongo 3.6.0+
from bson.int64 import Int64
from bson.regex import Regex
from pymongo import MongoClient

client = MongoClient(
    host='10.0.0.200',
    username='root',
    password='|cSFu@5rFv#h8*=',
    authSource='DigisatServer',
    port=12220)
database = client["DigisatServer"]
collection = database["Movimentacoes"]
collection1 = database["ProdutosServicosEmpresa"]
collection2 = database["OperacoesFiscais"]
numero = input('Digite o numero do documento\n')
tipo = input('Digite 1 para dav e 2 para NFe\n')
query = {}
if tipo == '2':
    query = {
        u"$and": [
            {
                u"_t": Regex(u".*NotaFiscalEletronicaSaida.*", "i")
            },
            {
                u"_t": Regex(u".*NotaFiscalEletronica.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoFiscalEletronico.*", "i")
            },
            {
                u"_t": Regex(u".*NotaFiscal.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoFiscal.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoAuxiliar.*", "i")
            },
            {
                u"_t": Regex(u".*Movimentacao.*", "i")
            },
            {
                u"Numero": Int64(numero)
            },
            {
                u"Situacao.Codigo": {u"$ne": 2}
            }
        ]
    }
elif tipo == '1':
    query = {
        u"$and": [
            {
                u"_t": Regex(u".*Movimentacao.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoAuxiliar.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoAuxiliarPrevisao.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoAuxiliarVendaBase.*", "i")
            },
            {
                u"_t": Regex(u".*DocumentoAuxiliarVenda.*", "i")
            },
            {
                u"Numero": Int64(numero)
            },
            {
                u"Situacao.Codigo": {u"$ne": 2}
            }
        ]
    }
if tipo == '2' or tipo == '1':
    cursor = collection.find(query)
    try:
        for doc in cursor:
            x = 0
            print(doc['_id'])
            uf = doc['Pessoa']['EnderecoPrincipal']['Municipio']['Uf']['Sigla']
            classificacao = doc['Pessoa']['Classificacao']['_t']
            for item in doc['ItensBase']:
                pipeline = [
                    {
                        u"$match": {
                            u"_id": doc['ItensBase'][x]['ProdutoServicoEmpresaReferencia']
                        }
                    },
                    {
                        u"$lookup": {
                            u"from": u"TributacoesEstadual",
                            u"localField": u"TributacaoEstadualReferencia",
                            u"foreignField": u"_id",
                            u"as": u"TributacoesEstadual"
                        }
                    }
                ]

                cursor1 = collection1.aggregate(
                    pipeline,
                    allowDiskUse=False
                )
                for doc1 in cursor1:
                    achei = 0
                    for t in doc1['TributacoesEstadual'][0]['UfsTributacao']:
                        if t['Uf']['Sigla'].lower() == doc['Pessoa']['EnderecoPrincipal']['Municipio']['Uf']['Sigla'].lower():
                            achei = 1
                            if classificacao in t:
                                doc['ItensBase'][x]['Percentual'] = t[classificacao]
                                doc['ItensBase'][x]['OperacaoFiscal'] = collection2.find_one({'_id': t[classificacao]['OperacaoFiscalReferencia'], 'Ativo': True})
                                print(doc['Pessoa']['EnderecoPrincipal']['Municipio']['Uf']['Sigla'])
                            else:
                                print("Não tem tributação para {}".format(doc['ItensBase'][x]['ProdutoServico']['Descricao']))
                    if achei == 0:
                        print("Não tem tributação para {}".format(
                            doc['ItensBase'][x]['ProdutoServico'][
                                'Descricao']))
                x += 1
            collection.update(
                {'_id': doc['_id']},
                {'$set': doc}
            )
    finally:
        client.close()
