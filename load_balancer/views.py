from django.views.generic import View
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator

from kubernetes import client

from devops_kubernetes import k8s


# Create your views here.
class ServicesApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                name = svc.metadata.name
                namespace = svc.metadata.namespace
                labels = svc.metadata.labels
                type = svc.spec.type
                cluster_ip = svc.spec.cluster_ip
                ports = []
                for p in svc.spec.ports:  # 不是序列，不能直接返回
                    port_name = p.name
                    port = p.port
                    target_port = p.target_port
                    protocol = p.protocol
                    node_port = ""
                    if type == "NodePort":
                        node_port = " <br> NodePort: %s" % p.node_port

                    port = {'port_name': port_name, 'port': port, 'protocol': protocol, 'target_port': target_port,
                            'node_port': node_port}
                    ports.append(port)

                selector = svc.spec.selector
                create_time = k8s.dt_format(svc.metadata.creation_timestamp)

                # 确认是否关联Pod
                endpoint = ""
                for ep in core_api.list_namespaced_endpoints(namespace=namespace).items:
                    if ep.metadata.name == name and ep.subsets is None:
                        endpoint = "未关联"
                    else:
                        endpoint = "已关联"

                svc = {"name": name, "namespace": namespace, "type": type,
                       "cluster_ip": cluster_ip, "ports": ports, "labels": labels,
                       "selector": selector, "endpoint": endpoint, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(svc)
                else:
                    data.append(svc)
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
            apps_api.delete_namespaced_service(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class IngressApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        networking_api = client.NetworkingV1beta1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                name = ing.metadata.name
                namespace = ing.metadata.namespace
                labels = ing.metadata.labels
                service = "None"
                http_hosts = "None"
                for h in ing.spec.rules:
                    host = h.host
                    path = ("/" if h.http.paths[0].path is None else h.http.paths[0].path)
                    service_name = h.http.paths[0].backend.service_name
                    service_port = h.http.paths[0].backend.service_port
                    http_hosts = {'host': host, 'path': path, 'service_name': service_name,
                                  'service_port': service_port}

                https_hosts = "None"
                if ing.spec.tls is None:
                    https_hosts = ing.spec.tls
                else:
                    for tls in ing.spec.tls:
                        host = tls.hosts[0]
                        secret_name = tls.secret_name
                        https_hosts = {'host': host, 'secret_name': secret_name}

                create_time = k8s.dt_format(ing.metadata.creation_timestamp)

                ing = {"name": name, "namespace": namespace, "labels": labels, "http_hosts": http_hosts,
                       "https_hosts": https_hosts, "service": service, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(ing)
                else:
                    data.append(ing)
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
        networking_api = client.NetworkingV1beta1Api()
        try:
            networking_api.delete_namespaced_ingress(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
