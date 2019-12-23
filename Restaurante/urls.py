from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^mesa/(?P<mesa>[0-9]+)/$', views.mesa_conta, name='mesa'),
    url(r'^conta/(?P<conta>[0-9]+)/$', views.mesa_conta, name='conta'),
    url(r'^mesa_add_item/(?P<mesa>[0-9]+)/(?P<item>[a-zA-Z0-9]+)/$',
        views.get_add_item_mesa, name='add_item_mesa'),
    url(r'^conta_add_item/(?P<conta>[0-9]+)/(?P<item>[a-zA-Z0-9]+)/$',
        views.get_add_item_mesa, name='add_item_mesa'),
    url(r'^add_item/$', views.set_add_item_mesa, name='add_item_post'),
    url(r'^fechar_conta/$', views.fechar_conta,
        name='fechar_conta'),
    url(r'^comprovante/(?P<id>[0-9]+)/$', views.comprovante,
        name='comprovante'),
    url(r'^lista_mesas_fechadas/$', views.lista_mesas_fechadas,
        name='lista_mesas_fechadas')
]
