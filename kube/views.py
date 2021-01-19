import json

from django.views.generic import View
from django.shortcuts import render
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator

from kubernetes import client

from devops_kubernetes import k8s, node_data


# Create your views here.
class NamespaceApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for ns in core_api.list_namespace().items:
                name = ns.metadata.name
                labels = ns.metadata.labels
                create_time = k8s.dt_format(ns.metadata.creation_timestamp)
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
            data = k8s.paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        k8s.load_auth(request=self.request)
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

    def post(self, request):
        name = request.POST.get('name', None)
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        body = client.V1Namespace(
            api_version='v1',
            kind='Namespace',
            metadata=client.V1ObjectMeta(
                name=name
            )
        )
        try:
            core_api.create_namespace(body=body)
            code, msg = 0, '创建{}成功！'.format(name)
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有创建权限！'
            elif e.status == 409:
                msg = '命名空间冲突'
            else:
                msg = '创建失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class NodeDetailsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()

        node_name = self.request.GET.get('node_name', None)
        n_r = node_data.node_resource(core_api, node_name)
        n_i = node_data.node_info(core_api, node_name)
        return render(request, 'kube/node_details.html', {'node_name': node_name, 'node_resouces': n_r, 'node_info': n_i})


class NodesApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
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
                memory = k8s.memory_convert(node.status.capacity['memory'])
                kebelet_version = node.status.node_info.kubelet_version
                cri_version = node.status.node_info.container_runtime_version
                create_time = k8s.dt_format(node.metadata.creation_timestamp)
                node = {"name": name, "labels": labels, "status": status,
                        "scheduler": scheduler, "cpu": cpu, "memory": memory,
                        "kebelet_version": kebelet_version, "cri_version": cri_version,
                        "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(node)
                else:
                    data.append(node)
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有访问权限！，默认使用default空间'
            else:
                msg = '获取数据失败！'
            result = {'code': code, 'msg': msg,}
        else:
            code, msg = 0, '数据返回成功！'
            count = len(data)
            page = self.request.GET.get('page', None)
            limit = self.request.GET.get('limit', None)
            if limit and page:
                data = k8s.paging_data(page=page, limit=limit, data=data)
            result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        code, msg = 1, '哈哈被骗了吧，Nodes：{}不支持删除！'.format(name)
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class PersistentVolunmeApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for pv in core_api.list_persistent_volume().items:
                name = pv.metadata.name
                capacity = pv.spec.capacity["storage"]
                access_modes = pv.spec.access_modes
                if access_modes[0] == 'ReadWriteMany':
                    access_modes = '多节点读写'
                elif access_modes[0] == 'ReadOnlyMany':
                    access_modes = '多节点只读'
                elif access_modes[0] == 'ReadWriteOnce':
                    access_modes = '单节点读写'
                reclaim_policy = pv.spec.persistent_volume_reclaim_policy
                if reclaim_policy == 'Retain':
                    reclaim_policy = '回收后保留'
                elif reclaim_policy == 'Delete':
                    reclaim_policy = '回收后删除'
                status = pv.status.phase
                if status == 'Available':
                    status = '可用'
                if pv.spec.claim_ref is not None:
                    pvc_ns = pv.spec.claim_ref.namespace
                    pvc_name = pv.spec.claim_ref.name
                    pvc = "%s / %s" % (pvc_ns, pvc_name)
                else:
                    pvc = "未绑定"
                storage_class = pv.spec.storage_class_name
                create_time = k8s.dt_format(pv.metadata.creation_timestamp)
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
            data = k8s.paging_data(page=page, limit=limit, data=data)
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        k8s.load_auth(request=self.request)
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

    def post(self, request):
        data = self.request.POST
        name = str.lower(data.get('name', None))
        capacity = data.get('capacity', None)
        access_mode = data.get('access_mode', None)
        storage_class = data.get('storage_class', None)
        if storage_class == 'nfs':
            storage_class_name = 'nfs-storageclass-provisioner'
        else:
            storage_class_name = None
        server_ip = data.get('server_ip', None)
        mount_path = str.lower(data.get('mount_path', name))
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        body = client.V1PersistentVolume(
            api_version='v1',
            kind='PersistentVolume',
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeSpec(
                capacity={'storage': capacity},
                access_modes=[access_mode],
                storage_class_name=storage_class_name,
                nfs=client.V1NFSVolumeSource(
                    server=server_ip,
                    path='/ifs/kubernetes/{}'.format(mount_path)
                )
            )
        )
        try:
            core_api.create_persistent_volume(body=body)
        except client.exceptions.ApiException as e:
            code = e.status
            if e.status == 403:
                msg = '没有创建权限！'
            elif e.status == 409:
                msg = 'PV名称冲突'
            elif e.status == 422:
                e = json.loads(e.body)
                msg = e.get('message')
            else:
                print(e)
                msg = '创建失败！'
        else:
            code, msg = 0, '创建{}成功！'.format(name)
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
