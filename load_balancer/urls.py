from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s_login import self_login_request
urlpatterns = [
    # path('node', self_login_request(TemplateView.as_view(template_name="dashboard/index.html")), name='index'),
]