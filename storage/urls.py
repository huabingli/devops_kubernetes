from django.urls import path, include
from django.views.generic import TemplateView

from devops_kubernetes.k8s_login import self_login_request

urlpatterns = [
    path('secrets', self_login_request(TemplateView.as_view(template_name="storage/secrets.html")), name='secrets'),

]