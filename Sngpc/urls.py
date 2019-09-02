from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^listagem/(?P<file>[a-zA-Z0-9]+)/$', views.listagem, name='listagem'),
]
