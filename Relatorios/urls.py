from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^sintetico_produtos/$', views.sintetico_produtos, name='sintetico_produtos'),
    url(r'^operacoes_por_pessoa/$', views.operacoes_por_pessoa, name='operacoes_por_pessoa'),
    url(r'^prevendas_por_vendedor/$', views.prevendas_por_vendedor, name='prevendas_por_vendedor'),
    url(r'^prevendas_por_usuario/$', views.prevendas_por_usuario, name='prevendas_por_usuario'),
    url(r'^mcmm/$', views.mcmm, name='mcmm'),
]