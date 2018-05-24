from pymongo import MongoClient

class Uteis():
    def __init__(self):
        print('ok')

    def Conexao(self):
        client = MongoClient('localhost', username='revenda', password='r3v3nd@', authSource='DigisatServer', port=12220)
        database = client['DigisatServer']
        return database

    def splitNumberOnPotency(self, stg):
        # número dividido em partes de 3 dígitos invertidos
        new = []
        num = 3
        for start in (range(len(stg), 0, -num)):
            if (start - num < 0):
                new.append(stg[0:start])
            else:
                new.append(stg[start - num:start])
        return new

    def numToStr(self, num):
        ###esta função escreve o número em letras
        ###todas as palavras
        unidades = {
            '0': '',
            '1': 'um',
            '2': 'dois',
            '3': 'três',
            '4': 'quatro',
            '5': 'cinco',
            '6': 'seis',
            '7': 'sete',
            '8': 'oito',
            '9': 'nove'
        }
        dez = {
            '10': 'dez',
            '11': 'onze',
            '12': 'doze',
            '13': 'treze',
            '14': 'quatorze',
            '15': 'quinze',
            '16': 'dezesseis',
            '17': 'dezesete',
            '18': 'dezoito',
            '19': 'dezenove'
        }
        dezenas = {
            '2': 'vinte',
            '3': 'trinta',
            '4': 'quarenta',
            '5': 'cinquenta',
            '6': 'sessenta',
            '7': 'setenta',
            '8': 'oitenta',
            '9': 'noventa'
        }
        centenas = {
            '1': 'cento',
            '2': 'duzentos',
            '3': 'trezentos',
            '4': 'quatrocentos',
            '5': 'quinhentos',
            '6': 'seiscentos',
            '7': 'setecentos',
            '8': 'oitocentos',
            '9': 'novecentos'
        }
        pot_singular = [
            '',
            'mil',
            'milhão',
            'bilhão',
            'trilhão',
            'quatrilhão'
        ]
        pot_plural = [
            '',
            'mil',
            'milhões',
            'bilhões',
            'trilhões',
            'quatrilhões'
        ]
        strNum = str(num)
        intNum = int(num)
        stg = ''
        ###zero precisa de regra especial
        if (intNum == 0):
            stg = 'zero'
        else:
            ###cada três números têm as mesmas regras
            nums = self.splitNumberOnPotency(strNum)
            stgs = []
            for idx, threeDigits in enumerate(nums):
                threeStg = ''
                # cem precisa de regra especial para isso
                if (threeDigits == '100'):
                    threeStg = 'cem'
                else:
                    ###primeiro, escrevemos dois primeiros dígitos
                    decimalStg = ''
                    decimal = int(threeDigits[-2:])
                    if (decimal == 0):
                        decimalStg = ''
                    elif (decimal <= 9):
                        decimalStg = unidades[str(decimal)]
                    elif (decimal >= 10 and decimal <= 19):
                        decimalStg = dez[str(decimal)]
                    else:
                        firstDigit = str(decimal)[:1]
                        secondDigit = str(decimal)[-1:]
                        decimalStg = dezenas[firstDigit]
                        if (int(secondDigit) == 0):
                            pass
                        else:
                            decimalStg += ' e '
                            decimalStg += unidades[str(decimal)[-1:]]
                    ###então, se houver três dígitos, podemos anexá-lo
                    if (int(threeDigits) > 99):
                        threeStg = str(centenas[threeDigits[0]])
                        if (not decimal == 0):
                            threeStg += ' e ' + decimalStg
                    else:
                        threeStg = decimalStg
                ###agora vamos localizá-lo na potência adequada
                if (int(threeDigits) > 1):
                    stgs.append(threeStg + ' ' + pot_plural[idx])
                elif (int(threeDigits) == 1):
                    stgs.append(threeStg + ' ' + pot_singular[idx])
                elif (int(threeDigits) == 0):
                    pass
            ###Agora junte todos os números de três dígitos
            if (stgs):
                first = True
                moreThenOnePotency = True if len(stgs) > 1 else False
                for strThreeDigit in stgs:
                    if (first):
                        first = False
                        ###tirar um espaço extra e
                        if (strThreeDigit[-1] == ' '):
                            strThreeDigit = strThreeDigit[:-1]
                        ### alguns verbos necessários
                        if (int(strNum[-3:]) <= 100 and moreThenOnePotency):
                            stg += 'e '
                        stg += strThreeDigit
                    else:
                        # regra para o resto dos casos
                        stg = strThreeDigit + ' ' + stg
        return stg

    def numToCurrency(self, num):
        ###partes de centésimos e inteiros divididos
        stg = ''
        num = str(num)
        cent = int(num[-2:])
        if (len(num) > 2):
            inteiro = int(num[:-2])
        else:
            inteiro = 0
        ### criar centavos
        temCentavo = True
        if (cent == 0):
            temCentavo = False
        elif (cent == 1):
            stg = '%s centavo' % (self.numToStr(cent))
        else:
            stg = '%s centavos' % (self.numToStr(cent))
        ###criar string inteira e anexar centavos
        if (inteiro == 0):
            pass
        else:
            if (temCentavo):
                stg = ' e ' + stg
            if (inteiro == 1):
                stg = '%s real%s' % (self.numToStr(inteiro), stg)
            else:
                if (str(inteiro)[:-7:-1] == '000000'):
                    stg = '%s de reais%s' % (self.numToStr(inteiro), stg)
                else:
                    stg = '%s reais%s' % (self.numToStr(inteiro), stg)
        return (stg)