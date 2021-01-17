"""devops_kubernetes URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from devops_kubernetes.k8s import self_login_request

urlpatterns = [
    path('', self_login_request(TemplateView.as_view(template_name="dashboard/index.html")), name='index'),
    path('dashboard/', include('dashboard.urls')),
    path('kube/', include('kube.urls')),
    path('load_balancer/', include('load_balancer.urls')),
    path('storage/', include('storage.urls')),
    path('workload/', include('workload.urls')),
]
