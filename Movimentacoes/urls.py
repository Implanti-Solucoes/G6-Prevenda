from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^prevenda/(?P<id>[a-zA-Z0-9]+)/$', views.impresso_prevenda, name='impressao_prevenda'),
    url(r'^prevenda/$', views.listagem_prevenda, name='listagem_prevenda'),
    url(r'^relatorios/$', views.relatorios, name='relatorios'),
]