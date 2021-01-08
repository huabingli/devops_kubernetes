from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s_login import self_login_request
from workload import views
urlpatterns = [
    path('deployment/', self_login_request(
        TemplateView.as_view(template_name='workload/deplyment.html')), name='deployment'),
    path('daemonsets/', self_login_request(
        TemplateView.as_view(template_name='workload/daemonsets.html')), name='daemonsets'),
    path('pods', self_login_request(TemplateView.as_view(template_name='workload/pods.html')), name='pods'),
    path('statefulset', self_login_request(TemplateView.as_view(template_name='workload/statefulset.html')),
         name='statefulset'),
    path('deployment_api/', views.DeploymentApiView.as_view(), name='deployment_api'),
    path('daemonsets_api/', views.DaemonSetsApiView.as_view(), name='daemonsets_api'),
    path('pods_api', views.PodsApiView.as_view(), name='pods_api'),
    path('statefulset_api', views.StatefulSetApiView.as_view(), name='statefulset_api')
]
