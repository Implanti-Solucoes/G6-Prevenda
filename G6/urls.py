from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url('admin/', admin.site.urls),
    url('movimentacoes/', include(('Movimentacoes.urls', 'movimentacoes'), namespace='movimentacoes')),
    url('financeiro/', include(('Financeiro.urls', 'financeiro'), namespace='financeiro')),
]
