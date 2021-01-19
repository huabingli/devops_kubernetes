from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s import self_login_request

from kube.views import NamespaceApiView, NodesApiView, PersistentVolunmeApiView, NodeDetailsApiView

urlpatterns = [
    path('nodes/', self_login_request(TemplateView.as_view(template_name="kube/nodes.html")), name='nodes'),
    path('node_details/', NodeDetailsApiView.as_view(), name='node_details'),
    path('namespaces/', self_login_request(
        TemplateView.as_view(template_name="kube/namespaces.html")), name='namespaces'
    ),
    path('persistentvolunmes/', self_login_request(
        TemplateView.as_view(template_name='kube/persistentvolumes.html')), name='persistentvolunmes'
         ),
    path('persistentvolunmes_create', self_login_request(
        TemplateView.as_view(template_name='kube/persistentvolumes_create.html')), name='persistentvolunmes_create'
         ),
    path('namespace_api/', NamespaceApiView.as_view(), name='namespace_api'),
    path('nodes_api/', NodesApiView.as_view(), name='nodes_api'),
    path('persistentvolunmes_api/', PersistentVolunmeApiView.as_view(), name='persistentvolunmes_api')
]
