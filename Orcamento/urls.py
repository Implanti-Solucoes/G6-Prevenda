from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views
''''''
urlpatterns = [
    url(r'^$', views.create_form, name='index'),
    url(r'^novo', views.create_form, name='create_form'),
    url(r'^salvar', views.create, name='create'),
    url(r'^consulta/$', views.xml_consulta, name='consulta'),
]
