from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^prevenda/$', views.gerar_financeiro, name='gerar_financeiro'),
    url(r'^comprovante_de_debito/(?P<id>[a-zA-Z0-9]+)/$', views.comprovante_de_debito_por_movimentacao,
        name='comprovante_de_debito_por_movimentacao'),
    url(r'^contratos/(?P<id>[a-zA-Z0-9]+)/(?P<cancelado>[0-2]+)/$', views.listagem_contratos, name='listagem_contratos'),
    url(r'^parcelas/(?P<id>[a-zA-Z0-9]+)/$', views.listagem_parcelas_cliente, name='listagem_parcelas_cliente'),
    url(r'^renegociao/$', views.renegociacao, name='renegociacao'),
    url(r'^renegociacao_lancamento/$', views.renegociacao_lancamento, name='renegociacao_lancamento'),
    url(r'^cartas_gerador/$', views.cartas_gerador, name='cartas_gerador'),
    url(r'^cancelar_contrato/(?P<id_contrato>[0-9]+)$', views.cancelar_contrato, name='cancelar_contrato'),
]
