from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^mesa/(?P<mesa>[0-9]+)/$', views.mesa_conta, name='mesa'),
    url(r'^conta/(?P<conta>[0-9]+)/$', views.mesa_conta, name='conta'),
]
