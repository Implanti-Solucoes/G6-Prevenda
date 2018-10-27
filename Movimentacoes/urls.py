from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.listagem_prevenda, name='listagem_prevenda'),
    url(r'^gerar_financeiro/(?P<id>[a-zA-Z0-9]+)$', views.gerar_financeiro, name='gerar_financeiro'),
    url(r'^impresso/(?P<id>[a-zA-Z0-9]+)/$', views.impresso_prevenda, name='impressao_prevenda'),
]