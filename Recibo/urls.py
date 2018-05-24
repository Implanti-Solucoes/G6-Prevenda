from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^(?P<id>[A-Za-z0-9]+)/$', views.impresso, name='impressao'),
    url(r'^$', views.listagem, name='listagem')
]