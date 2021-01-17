from django.views.generic import View
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator

from kubernetes import client

from devops_kubernetes import k8s


# Create your views here.
class DeploymentApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
                name = dp.metadata.name
                namespace = dp.metadata.namespace
                replicas = dp.spec.replicas
                available_replicas = (0 if dp.status.available_replicas is None else dp.status.available_replicas)
                labels = dp.metadata.labels
                selector = dp.spec.selector.match_labels
                if len(dp.spec.template.spec.containers) > 1:
                    images = ""
                    n = 1
                    for c in dp.spec.template.spec.containers:
                        status = ("运行中" if dp.status.conditions[0].status == "True" else "异常")
                        image = c.image
                        images += "[%s]: %s / %s" % (n, image, status)
                        images += "<br>"
                        n += 1
                else:
                    status = (
                        "运行中" if dp.status.conditions[0].status == "True" else "异常")
                    image = dp.spec.template.spec.containers[0].image
                    images = "%s / %s" % (image, status)

                create_time = k8s.dt_format(dp.metadata.creation_timestamp)

                dp = {"name": name, "namespace": namespace, "replicas": replicas,
                      "available_replicas": available_replicas, "labels": labels, "selector": selector,
                      "images": images, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(dp)
                else:
                    data.append(dp)
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

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_deployment(name=name, namespace=namespace)
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
        name = data.get('name', None)
        namespace = data.get('namespace', None)
        image = data.get('image', None)
        replicas = int(data.get('replicas', None))
        print(data)
        try:
            labels = dict()
            for p in data.get('labels', None).split(','):
                c = p.split('=')
                if not len(c) == 2:
                    raise IndexError('标签格式错误')
                k, v = c[0], c[1]
                labels.update(k=v)
        except IndexError:
            code, msg = 1, '标签格式错误！'
            result = {'code': code, 'msg': msg}
            return JsonResponse(result)

        resources = data.get('resources', None)
        health_liveness = data.get('health[liveness]', None)
        health_readiness = data.get('health[readiness]', None)
        if resources == '1c2g':
            cpu, memory = 1, 2
        elif request == '2c4g':
            cpu, memory = 2, 4
        elif request == '':
            cpu, memory = 4, 8
        else:
            cpu, memory = 0.5, 1
        requests_cpu = cpu - cpu * 0.2
        requests_memory = memory - memory * 0.2
        resources = client.V1ResourceRequirements(
            limits={'cpu': cpu, 'memory': memory},
            requests={'cpu': requests_cpu, 'memory': requests_memory}
        )

        if health_liveness == 'on':
            livenss_probe = client.V1Probe(http_get='/', timeout_seconds=30, initial_delay_seconds=30)
        else:
            livenss_probe = ''

        if health_readiness == 'on':
            readiness_probe = client.V1Probe(http_get='/', timeout_seconds=30, initial_delay_seconds=30)
        else:
            readiness_probe = ''

        code, msg = 0, '删除成功！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class DaemonSetsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for ds in apps_api.list_namespaced_daemon_set(namespace).items:
                name = ds.metadata.name
                namespace = ds.metadata.namespace
                desired_number = ds.status.desired_number_scheduled
                available_number = ds.status.number_available
                labels = ds.metadata.labels
                selector = ds.spec.selector.match_labels
                containers = {}
                for c in ds.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = k8s.dt_format(ds.metadata.creation_timestamp)

                ds = {"name": name, "namespace": namespace, "labels": labels, "desired_number": desired_number,
                      "available_number": available_number,
                      "selector": selector, "containers": containers, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(ds)
                else:
                    data.append(ds)
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

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_daemon_set(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class PodsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for po in core_api.list_namespaced_pod(namespace).items:
                name = po.metadata.name
                namespace = po.metadata.namespace
                labels = po.metadata.labels
                pod_ip = po.status.pod_ip

                containers = []  # [{},{},{}]
                status = "None"
                # 只为None说明Pod没有创建（不能调度或者正在下载镜像）
                if po.status.container_statuses is None:
                    status = po.status.conditions[-1].reason
                else:
                    for c in po.status.container_statuses:
                        c_name = c.name
                        c_image = c.image

                        # 获取重启次数
                        restart_count = c.restart_count

                        # 获取容器状态
                        c_status = "None"
                        if c.ready is True:
                            c_status = "Running"
                        elif c.ready is False:
                            if c.state.waiting is not None:
                                c_status = c.state.waiting.reason
                            elif c.state.terminated is not None:
                                c_status = c.state.terminated.reason
                            elif c.state.last_state.terminated is not None:
                                c_status = c.last_state.terminated.reason

                        c = {'c_name': c_name, 'c_image': c_image, 'restart_count': restart_count, 'c_status': c_status}
                        containers.append(c)

                create_time = create_time = k8s.dt_format(po.metadata.creation_timestamp)
                po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                      "labels": labels, "containers": containers, "status": status,
                      "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(po)
                else:
                    data.append(po)
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

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.CoreV1Api()
        try:
            apps_api.delete_namespaced_pod(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class StatefulSetApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        namespace = self.request.GET.get('namespace')
        search_key = self.request.GET.get('search_key', None)
        data = list()
        try:
            for sts in apps_api.list_namespaced_stateful_set(namespace).items:
                name = sts.metadata.name
                namespace = sts.metadata.namespace
                labels = sts.metadata.labels
                selector = sts.spec.selector.match_labels
                replicas = sts.spec.replicas
                ready_replicas = ("0" if sts.status.ready_replicas is None else sts.status.ready_replicas)
                # current_replicas = sts.status.current_replicas
                service_name = sts.spec.service_name
                containers = {}
                for c in sts.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = k8s.dt_format(sts.metadata.creation_timestamp)

                ds = {"name": name, "namespace": namespace, "labels": labels, "replicas": replicas,
                      "ready_replicas": ready_replicas, "service_name": service_name,
                      "selector": selector, "containers": containers, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(ds)
                else:
                    data.append(ds)
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

    def delete(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name')
        namespace = request_data.get('namespace')
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_stateful_set(name=name, namespace=namespace)
            code, msg = 0, '删除成功！'
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有删除权限！'
            else:
                msg = '删除失败！'
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
