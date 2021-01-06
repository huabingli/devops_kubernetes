from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s_login import self_login_request

urlpatterns = [
    path('nodes', self_login_request(TemplateView.as_view(template_name="kube/nodes.html")), name='nodes'),
    path('namespaces', self_login_request(TemplateView.as_view(template_name="kube/namespaces.html")), name='namespaces'),

]