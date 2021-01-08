from django.urls import path
from django.views.generic import TemplateView


from dashboard.views import LogIn, IndexViewApi, logout

urlpatterns = [
    path('login/', LogIn.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    path('index_api/', IndexViewApi.as_view(), name='index_api'),
]
