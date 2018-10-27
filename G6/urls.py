from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url('', include(('Movimentacoes.urls', 'movimentacoes'), namespace='movimentacoes')),
    url('admin/', admin.site.urls),
    url('pessoas/', include(('Pessoas.urls', 'pessoas'), namespace='pessoas')),
    url('estoque/', include(('Estoque.urls', 'estoque'), namespace='estoque')),
    url('orcamento/', include(('Orcamento.urls', 'orcamento'), namespace='orcamento')),
    url('financeiro/', include(('Financeiro.urls', 'financeiro'), namespace='financeiro')),
    url('relatorios/', include(('Relatorios.urls', 'relatorios'), namespace='relatorios')),
]
