from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.listagem_movimentacoes, name='listagem_movimentacoes'),
    url(r'^gerar_financeiro/(?P<id>[a-zA-Z0-9]+)$', views.gerar_financeiro, name='gerar_financeiro'),
    url(r'^impresso1/(?P<id>[a-zA-Z0-9]+)/$', views.impressao1, name='impressao1'),
]