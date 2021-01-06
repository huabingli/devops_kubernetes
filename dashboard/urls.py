from django.urls import path
from django.views.generic import TemplateView


from dashboard.views import LogIn, IndexViewApi, logout, NamespaceApi

urlpatterns = [
    path('login/', LogIn.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    path('index_api/', IndexViewApi.as_view(), name='index_api'),
    path('namespace_api/', NamespaceApi.as_view(), name='namespace_api')
]
