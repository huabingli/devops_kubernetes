from django.urls import path
from django.views.generic import TemplateView


from dashboard.views import LogIn, IndexViewApi

urlpatterns = [
    path('login/', LogIn.as_view(), name='login'),
    path('index_api/', IndexViewApi.as_view(), name='index_api')
    #    path('admin/', admin.site.urls),
]
