from Movimentacoes.models import Movimentacoes
from django.shortcuts import render
from lxml import objectify
import hashlib
import glob
import os


def index(request):
    # variaveis padrões
    template_name = 'sngpc/index.html'
    context = {
        'items': []
    }
    dir = 'C:\\DigiSat\\SuiteG6\\Sistema\\Sngpc\\'

    for item in glob.glob(os.path.join(dir, '*.xml')):
        dados = {
            'item': item.replace(dir, ''),
            'md5': hashlib.md5(open(item, 'rb').read()).hexdigest()
        }
        context['items'].append(dados)
    return render(request, template_name, context)


def listagem(request, file):
    # variaveis padrões
    template_name = 'sngpc/listagem.html'
    context = {
        'items': []
    }
    dir = 'C:\\DigiSat\\SuiteG6\\Sistema\\Sngpc\\'
    for item in glob.glob(os.path.join(dir, '*.xml')):
        if file == str(hashlib.md5(open(item, 'rb').read()).hexdigest()):
            rawdata = open(item, 'r').read()
            file = objectify.fromstring(str(rawdata).encode('utf-8'))
            return render(request, template_name, {'file': file})
