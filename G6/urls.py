from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    url('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    url('',
        include(('Movimentacoes.urls', 'movimentacoes'),
                namespace='movimentacoes')),
    url('pessoas/',
        include(('Pessoas.urls', 'pessoas'),
                namespace='pessoas')),
    url('estoque/',
        include(('Estoque.urls', 'estoque'),
                namespace='estoque')),
    url('orcamento/',
        include(('Orcamento.urls', 'orcamento'),
                namespace='orcamento')),
    url('financeiro/',
        include(('Financeiro.urls', 'financeiro'),
                namespace='financeiro')),
    url('relatorios/',
        include(('Relatorios.urls', 'relatorios'),
                namespace='relatorios')),
    url('sngpc/',
        include(('Sngpc.urls', 'sngpc'),
                namespace='sngpc')),
    url('restaurante/',
        include(('Restaurante.urls', 'restaurante'),
                namespace='restaurante')),
]
