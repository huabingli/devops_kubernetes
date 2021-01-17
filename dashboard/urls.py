from django.urls import path
from django.views.generic import TemplateView


from dashboard.views import LogIn, IndexViewApi, logout, ExportResourceViewApi, ace_editor

urlpatterns = [
    path('login/', LogIn.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    path('index_api/', IndexViewApi.as_view(), name='index_api'),
    path('ace_editor/', ace_editor, name='ace_editor'),
    path('exportresource_api/', ExportResourceViewApi.as_view(), name='exportresource_api')
]
