from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^tabela/$', views.tabela_list, name='tabelas'),
    url(r'^tabela/create/$', views.tabela_create, name='tabela_create'),
    url(r'^tabela/create/salve$', views.tabela_create_post, name='tabela_create_post'),
    url(r'^tabela/edit/(?P<id>[a-zA-Z0-9]+)/$', views.tabela_edit, name='tabela_edit'),
    url(r'^tabela/post/$', views.tabela_edit_post, name='tabela_edit_post'),
]