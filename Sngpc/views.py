from Movimentacoes.models import Movimentacoes
from django.shortcuts import render
from lxml import objectify
import hashlib
import glob
import os
import requests
from selectolax.parser import HTMLParser

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
    dir = 'C:\\DigiSat\\SuiteG6\\Sistema\\Sngpc\\'
    ms = []
    ms_dict = {}
    session = requests.session()
    for item in glob.glob(os.path.join(dir, '*.xml')):
        if file == str(hashlib.md5(open(item, 'rb').read()).hexdigest()):
            rawdata = open(item, 'r').read()
            file = objectify.fromstring(str(rawdata).encode('utf-8'))
            for entrada in file.corpo.medicamentos.entradaMedicamentos:
                for medicamento in entrada.medicamentoEntrada:
                    if str(medicamento.registroMSMedicamento) not in ms:
                        ms.append(str(medicamento.registroMSMedicamento))

            for saida in file.corpo.medicamentos.saidaMedicamentoVendaAoConsumidor:
                try:
                    for medicamento in saida.medicamentoVenda:
                        if str(medicamento.registroMSMedicamento) not in ms:
                            ms.append(str(medicamento.registroMSMedicamento))
                except AttributeError:
                    pass
            for x in ms:
                if len(x) == 13:
                    headers = {
                        'Connection': 'keep-alive',
                        'Cache-Control': 'max-age=0',
                        'Origin': 'http://sngpc.anvisa.gov.br',
                        'Upgrade-Insecure-Requests': '1',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36 OPR/65.0.3467.72',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                        'Referer': 'http://sngpc.anvisa.gov.br/ConsultaMedicamento/index.asp',
                        'Accept-Encoding': 'gzip, deflate',
                        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    }

                    data = {
                        'NU_REG': '{}.{}.{}.{}-{}'.format(
                            x[0:1], x[1:5], x[5:9], x[9:12], x[12:13]
                        )
                    }

                    response = session.post(
                        'http://sngpc.anvisa.gov.br/ConsultaMedicamento/index.asp',
                        headers=headers, data=data, verify=False)
                    response_data = HTMLParser(response.text).tags('td')
                    dados_ms = response_data[20].text(deep=True, separator='', strip=False)
                    dados_ms = dados_ms.replace('\n', '')
                    dados_ms = dados_ms.replace('	', '')
                    dados_ms = dados_ms.replace('  ', '')
                    dados_ms = dados_ms.replace(' Apresentação Comercial do Medicamento: ', '')
                    ms_dict[x] = dados_ms
            return render(request, template_name, {'file': file, 'ms_dict': ms_dict})
