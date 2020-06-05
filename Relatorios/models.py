from django.db import models


class McmmForNextMonth(models.Model):
    razao_social = models.CharField('Razão Social', max_length=100)
    registro_anp = models.CharField('Registro ANP', max_length=40)
    tipo_instacao = models.SmallIntegerField('Tipo de Instalação')
    capacidade_kg = models.FloatField('Capacidade de Armazenamento em KG')
    distribuidora = models.CharField('Distribuidora', max_length=100)
    longradouro = models.CharField('Longradouro', max_length=100)
    numero = models.IntegerField('Numero')
    bairro = models.CharField('Bairro', max_length=50)
    cidade = models.CharField('Cidade', max_length=50)
    estado = models.CharField('Estado', max_length=50)
    cnpj = models.CharField('Estado', max_length=14)
