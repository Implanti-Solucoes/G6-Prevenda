from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.listagem, name='listagem'),
    url(r'^impresso/$', views.impresso, name='impressao'),
    url(r'^prevenda/$', views.gerar_financeiro, name='gerar_financeiro'),
]