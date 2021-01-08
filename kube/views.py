from django.views.generic import View
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator

from kubernetes import client

from devops_kubernetes.k8s_login import self_login_request, load_auth, paging_data, memory_convert


# Create your views here.
class NamespaceApiView(View):
    @method_decorator(self_login_request)
    def get(self, request):
        load_auth(request=self.request)
        core_api = client.CoreV1Api()
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for ns in core_api.list_namespace().items:
                name = ns.metadata.name
                labels = ns.metadata.labels
                create_time = ns.metadata.creation_timestamp
                namespace = {"name": name, "labels": labels, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(namespace)
                else:
                    data.append(namespace)
            code, msg = 0, '数据返回成功！'
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
            data = paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        load_auth(request=self.request)
        core_api = client.CoreV1Api()
        try:
            core_api.delete_namespace(name)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class NodesApiView(View):
    @method_decorator(self_login_request)
    def get(self, request):
        load_auth(request=self.request)
        core_api = client.CoreV1Api()
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for node in core_api.list_node_with_http_info()[0].items:
                name = node.metadata.name
                labels = node.metadata.labels
                status = node.status.conditions[-1].status
                scheduler = ("是" if node.spec.unschedulable is None else "否")
                cpu = node.status.capacity['cpu']
                memory = memory_convert(node.status.capacity['memory'])
                kebelet_version = node.status.node_info.kubelet_version
                cri_version = node.status.node_info.container_runtime_version
                create_time = node.metadata.creation_timestamp
                node = {"name": name, "labels": labels, "status": status,
                        "scheduler": scheduler, "cpu": cpu, "memory": memory,
                        "kebelet_version": kebelet_version, "cri_version": cri_version,
                        "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(node)
                else:
                    data.append(node)
            code, msg = 0, '数据返回成功！'
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
            data = paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        code, msg = 1, '哈哈被骗了吧，Nodes：{}不支持删除！'.format(name)
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class PersistentVolunmeApiView(View):
    @method_decorator(self_login_request)
    def get(self, request):
        load_auth(request=self.request)
        core_api = client.CoreV1Api()
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for pv in core_api.list_persistent_volume().items:
                name = pv.metadata.name
                capacity = pv.spec.capacity["storage"]
                access_modes = pv.spec.access_modes
                reclaim_policy = pv.spec.persistent_volume_reclaim_policy
                status = pv.status.phase
                if pv.spec.claim_ref is not None:
                    pvc_ns = pv.spec.claim_ref.namespace
                    pvc_name = pv.spec.claim_ref.name
                    pvc = "%s / %s" % (pvc_ns, pvc_name)
                else:
                    pvc = "未绑定"
                storage_class = pv.spec.storage_class_name
                create_time = pv.metadata.creation_timestamp
                pv = dict(
                    name=name, capacity=capacity, access_modes=access_modes, reclaim_policy=reclaim_policy,
                    status=status, pvc=pvc, storage_class=storage_class, create_time=create_time
                )
                if search_key:
                    if search_key in name:
                        data.append(pv)
                else:
                    data.append(pv)
            code, msg = 0, '数据返回成功！'
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
            data = paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        load_auth(request=self.request)
        core_api = client.CoreV1Api()
        try:
            core_api.delete_persistent_volume(name)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
