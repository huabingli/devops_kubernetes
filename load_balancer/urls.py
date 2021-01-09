from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s import self_login_request

from load_balancer import views
urlpatterns = [
    path('services/',
         self_login_request(TemplateView.as_view(template_name='loadbalancer/service.html')),
         name='services'),
    path('services_api/', views.ServicesApiView.as_view(), name='services_api'),
    path('ingress/',
         self_login_request(TemplateView.as_view(template_name='loadbalancer/ingress.html')),
         name='ingress'),
    path('ingress_api', views.IngressApiView.as_view(), name='ingress_api')
]