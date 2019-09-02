# Requires pymongo 3.6.0+
import bson
from bson import ObjectId
from pymongo import MongoClient
import clr
clr.AddReference(
    R'D:\ConversorG6\DigisatServer.Domain.Main.dll'
)
from DigisatServer.Domain.Main.Aggregates.CadastrosAgg.ChavesPaf import *
class_referencia = ChavePafProdutoEmpresaLayout
class_referencia1 = ChavePaf(ChavePafProdutoEmpresaLayout)
print(class_referencia)