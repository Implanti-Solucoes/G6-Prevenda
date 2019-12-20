from django import template
from django.template.defaultfilters import stringfilter
from Estoque.models import Products
from datetime import datetime

register = template.Library()


@register.filter
@stringfilter
def busca_produto(value):
    db = Products
    produto = db.get_produto_servico(ms=value)
    if len(produto) == 1:
        return produto[0]['Descricao']
    return "Não encontrado"


@register.filter
@stringfilter
def busca_produto_anvisa(value, ms_dict):
    if value in ms_dict:
        return ms_dict[value]
    return "Não encontrado"


@register.filter
@stringfilter
def busca_produto_anvisa_valida(value, ms_dict):
    if value not in ms_dict:
        return 'class="bg-danger"'
    return ""


@register.filter
@stringfilter
def valida_data_start(date_document: str, date_file: str):
    date_document_a1 = datetime.strptime(date_document, "%Y-%m-%d").date()
    date_file_a1 = datetime.strptime(str(date_file), "%Y-%m-%d").date()
    if date_document_a1 < date_file_a1:
        return ' bg-danger'
    return ''


@register.filter
@stringfilter
def valida_data_end(date_document: str, date_file: str):
    date_document_a1 = datetime.strptime(date_document, "%Y-%m-%d").date()
    date_file_a1 = datetime.strptime(str(date_file), "%Y-%m-%d").date()
    if date_document_a1 > date_file_a1:
        return ' bg-danger'
    return ''


@register.filter
@stringfilter
def valida_ms(ms: str):
    if len(ms) != 13:
        return ' class="bg-danger"'
    return ''


@register.filter
@stringfilter
def valida_notificao(notificacao: str, tipo_receituario_medicamento: int):
    notificacao = notificacao.replace(' ', '')
    if tipo_receituario_medicamento == 2 and notificacao == '' or \
            tipo_receituario_medicamento == 3 and notificacao == '' or \
            tipo_receituario_medicamento == 4 and notificacao == '':
        return ' bg-danger'
    return ''


@register.filter
@stringfilter
def valida_conselho(conselho: str, uso: int):
    conselho = conselho.lower()
    if conselho == 'crmv' and uso == 1:
        return ' bg-danger'
    return ''
