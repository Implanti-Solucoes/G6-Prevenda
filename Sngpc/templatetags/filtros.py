from django import template
from Estoque.models import Products
register = template.Library()


@register.filter
def busca_produto(value):
    db = Products
    produto = db.get_produto_servico(ms=value)
    if len(produto) == 1:
        return produto[0]['Descricao']
