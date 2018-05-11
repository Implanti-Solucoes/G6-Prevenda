from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^(?P<id>[0-9]+)/$', views.impressoid, name='impressao'),
    url(r'^$', views.impresso, name='listagem'),
]