from django.urls import path, include

from dashboard.views import LogIn

urlpatterns = [
    path('login/', LogIn.as_view(), name='login')
    #    path('admin/', admin.site.urls),
]
