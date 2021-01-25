from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s import self_login_request
from workload import views
urlpatterns = [
    path('deployment/', self_login_request(
        TemplateView.as_view(template_name='workload/deployment.html')), name='deployment'),
    path('deployment_create/',
         self_login_request(TemplateView.as_view(template_name='workload/deployment_create.html')),
         name='deployment_create'),
    path(
        'deployment_details/',
        self_login_request(views.DeploymentDetailsView.as_view()),
        name='deployment_details'
         ),
    path(
        'replicaset_api',
        views.ReplicasetApiView.as_view(),
        name='replicaset_api'
    ),
    path('daemonsets/', self_login_request(
        TemplateView.as_view(template_name='workload/daemonsets.html')), name='daemonsets'),
    path('pods/', self_login_request(TemplateView.as_view(template_name='workload/pods.html')), name='pods'),
    path('pods_log/', self_login_request(views.PodsLogView.as_view()), name='pods_log'),
    path('statefulset/', self_login_request(TemplateView.as_view(template_name='workload/statefulset.html')),
         name='statefulset'),
    path('deployment_api/', views.DeploymentApiView.as_view(), name='deployment_api'),
    path('daemonsets_api/', views.DaemonSetsApiView.as_view(), name='daemonsets_api'),
    path('pods_api/', views.PodsApiView.as_view(), name='pods_api'),
    path('statefulset_api/', views.StatefulSetApiView.as_view(), name='statefulset_api'),
    path('terminal/', views.TerminalView.as_view(), name='terminal')
]
