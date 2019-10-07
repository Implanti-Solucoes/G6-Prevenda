from django import template
from Estoque.models import Products
register = template.Library()


@register.filter
def formata_cpf_cnpj(value):
    if len(value) == 11:
        value = '%s.%s.%s-%s' % (
            value[0:3],
            value[3:6],
            value[6:9],
            value[9:11])
    elif len(value) == 14:
        value = '%s.%s.%s/%s-%s' % (
            value[0:2],
            value[2:5],
            value[5:8],
            value[8:12],
            value[12:14])
    return value
