import socket
import sys
from lxml import objectify
from pymongo import MongoClient

f = open(r'C:\DigiSat\SuiteG6\Sistema\ConfiguracaoClient.xml', 'r')
data = f.read()
f.close()
data = data.replace('<?xml version="1.0" encoding="utf-8"?>\n', '')
data = data.replace('ï»¿', '')
xml = objectify.fromstring(data)
host = str(xml.Ip) if hasattr(xml, 'Ip') else '127.0.0.1'
try:
    socket.inet_aton(host)
except socket.error:
    try:
        host = socket.gethostbyname(host)
    except:
        print("Unable to get Hostname and IP")
        host = '127.0.0.1'

client = MongoClient(
    host=host, username='root', password='|cSFu@5rFv#h8*=',
    authSource='admin', port=12220, serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000, authMechanism='SCRAM-SHA-1'
)
database = client["DigisatServer"]
collection = database["ItensMesaConta"]
query = {}
query["Situacao"] = 2

sort = [ (u"NumeroMesa", 1), (u"NumeroMesaConta", 1), (u"DataHora", 1) ]

cursor = collection.find(query, sort = sort, limit = 250)
try:
    for doc in cursor:
        print(doc)
finally:
    client.close()
