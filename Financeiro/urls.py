from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^recebidas/$', views.recebidas, name='recebidas'),
    url(r'^pendentes/$', views.pendentes, name='pendentes'),
    url(r'^recibo/$', views.recibo, name='recibo'),
    url(r'^prevenda/$', views.gerar_financeiro, name='gerar_financeiro'),
]