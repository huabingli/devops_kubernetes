from django.urls import path
from django.views.generic import TemplateView

from devops_kubernetes.k8s import self_login_request

from storage import views

urlpatterns = [
    path('secrets/', self_login_request(TemplateView.as_view(template_name="storage/secrets.html")), name='secret'),
    path('secrets_api/', views.SecretsApiView.as_view(), name='secrets_api'),
    path('persistentvolumeclaims_api/', views.PersistentVolumeClaimsApiView.as_view(),
         name='persistentvolumeclaims_api'),
    path('persistentvolumeclaims/',
         self_login_request(TemplateView.as_view(template_name='storage/persistentvolumeclaims.html')),
         name='persistentvolumeclaims'),
    path(
        'configmaps/',
        self_login_request(TemplateView.as_view(template_name='storage/configmaps.html')),
        name='configmaps'
    ),
    path('configmaps_api/', views.ConfigMapsApiView.as_view(), name='configmaps_api')



]