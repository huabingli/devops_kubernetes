from django.views.generic import View
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator

from kubernetes import client

from devops_kubernetes import k8s


# Create your views here.
class PersistentVolumeClaimsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for pvc in core_api.list_namespaced_persistent_volume_claim(namespace=namespace).items:
                name = pvc.metadata.name
                namespace = pvc.metadata.namespace
                labels = pvc.metadata.labels
                storage_class_name = pvc.spec.storage_class_name
                access_modes = pvc.spec.access_modes
                capacity = (pvc.status.capacity if pvc.status.capacity is None else pvc.status.capacity["storage"])
                volume_name = pvc.spec.volume_name
                status = pvc.status.phase
                create_time = k8s.dt_format(pvc.metadata.creation_timestamp)

                pvc = {"name": name, "namespace": namespace, "lables": labels,
                       "storage_class_name": storage_class_name, "access_modes": access_modes, "capacity": capacity,
                       "volume_name": volume_name, "status": status, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(pvc)
                else:
                    data.append(pvc)
            code, msg = 0, '数据返回成功！'
        except client.exceptions.ApiValueError as e:
            code, msg = 1, '{}'.format(e)
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有访问权限！，默认使用default空间'
            else:
                msg = '获取数据失败！'
        count = len(data)
        page = self.request.GET.get('page', None)
        limit = self.request.GET.get('limit', None)
        if limit and page:
            data = k8s.paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    @method_decorator(k8s.self_login_request)
    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.CoreV1Api()
        try:
            apps_api.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class ConfigMapsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for cm in core_api.list_namespaced_config_map(namespace=namespace).items:
                name = cm.metadata.name
                namespace = cm.metadata.namespace
                data_length = (len(cm.data) if cm.data is not None else "0")
                create_time = k8s.dt_format(cm.metadata.creation_timestamp)

                cm = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(cm)
                else:
                    data.append(cm)
            code, msg = 0, '数据返回成功！'
        except client.exceptions.ApiValueError as e:
            code, msg = 1, '{}'.format(e)
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有访问权限！，默认使用default空间'
            else:
                msg = '获取数据失败！'
        count = len(data)
        page = self.request.GET.get('page', None)
        limit = self.request.GET.get('limit', None)
        if limit and page:
            data = k8s.paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    @method_decorator(k8s.self_login_request)
    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.CoreV1Api()
        try:
            apps_api.delete_namespaced_config_map(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class SecretsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for secret in core_api.list_namespaced_secret(namespace=namespace).items:
                name = secret.metadata.name
                namespace = secret.metadata.namespace
                data_length = (len(secret.data) if secret.data is not None else "空")
                create_time = k8s.dt_format(secret.metadata.creation_timestamp)

                se = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(se)
                else:
                    data.append(se)
            code, msg = 0, '数据返回成功！'
        except client.exceptions.ApiValueError as e:
            code, msg = 1, '{}'.format(e)
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有访问权限！，默认使用default空间'
            else:
                msg = '获取数据失败！'
        count = len(data)
        page = self.request.GET.get('page', None)
        limit = self.request.GET.get('limit', None)
        if limit and page:
            data = k8s.paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    @method_decorator(k8s.self_login_request)
    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.CoreV1Api()
        try:
            apps_api.delete_namespaced_secret(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
