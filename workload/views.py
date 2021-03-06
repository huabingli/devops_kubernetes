import json

from django.views.generic import View
from django.http import JsonResponse, QueryDict
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_sameorigin


from kubernetes import client

from devops_kubernetes import k8s, node_data


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

    @method_decorator(k8s.self_login_request)
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

    @method_decorator(k8s.self_login_request)
    def post(self, request):
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        data = self.request.POST
        name = data.get('name', None)
        namespace = data.get('namespace', None)
        image = data.get('image', None)
        replicas = int(data.get('replicas', None))
        try:
            labels = dict()
            for p in data.get('labels', None).split(','):
                c = p.split('=')
                if not len(c) == 2:
                    raise IndexError('标签格式错误')
                k, v = c[0], c[1]
                labels[k] = v
        except IndexError:
            code, msg = 1, '标签格式错误！'
            result = {'code': code, 'msg': msg}
            return JsonResponse(result)

        resources = data.get('resources', None)
        # health_liveness = data.get('health[liveness]', None)
        # health_readiness = data.get('health[readiness]', None)
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
            limits={'cpu': cpu, 'memory': '{}Gi'.format(memory)},
            requests={'cpu': requests_cpu, 'memory': '{}Gi'.format(requests_memory)}
        )

        # if health_liveness == 'on':
        #     livenss_probe = client.V1Probe(http_get='/', timeout_seconds=30, initial_delay_seconds=30)
        # else:
        #     livenss_probe = ''
        #
        # if health_readiness == 'on':
        #     readiness_probe = client.V1Probe(http_get='/', timeout_seconds=30, initial_delay_seconds=30)
        # else:
        #     readiness_probe = ''

        body = client.V1Deployment(
            api_version='apps/v1',
            kind='Deployment',
            metadata=client.V1ObjectMeta(name=name, labels=labels),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector={'matchLabels': labels},
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name='web',
                            image=image,
                            env=[{'name': 'TEST', 'value': '123'}, {'name': 'DEV', 'value': '456'}],
                            ports=[client.V1ContainerPort(container_port=80)],
                            resources=resources
                        )]
                    )
                )
            )
        )
        try:
            apps_api.create_namespaced_deployment(namespace=namespace, body=body)
        except client.exceptions.ApiException as e:
            code = e.status
            if e.status == 403:
                msg = '没有创建权限！'
            elif e.status == 409:
                msg = 'Deployment已经存在！'
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

    @method_decorator(k8s.self_login_request)
    def put(self, request):
        request_data = QueryDict(self.request.body)
        name = request_data.get('name', None)
        namespace = request_data.get('namespace', None)
        replicas = request_data.get('replicas')
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        try:
            body = apps_api.read_namespaced_deployment(name=name, namespace=namespace)
            current_replicas = body.spec.replicas
            min_replicas = 0
            max_replicas = 10
            try:
                replicas = int(replicas)
            except ValueError:
                raise client.exceptions.ApiException(reason='输入格式错误，请输入数字！')
            msg = ''
            if current_replicas < replicas < max_replicas:
                msg = '扩容成功'
            elif current_replicas > replicas > min_replicas:
                msg = '缩容成功'
            elif replicas == current_replicas:
                msg = '副本数一致'
                raise client.exceptions.ApiException(reason=msg)
            elif replicas > max_replicas:
                msg = '副本数设置过大！请联系管理员操作'
                raise client.exceptions.ApiException(reason=msg)
            elif replicas == min_replicas:
                msg = '副本数不能设置为0！'
                raise client.exceptions.ApiException(reason=msg)
            body.spec.replicas = replicas
            apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
            code = 0
        except client.exceptions.ApiException as e:
            code = e.status
            if e.status == 403:
                msg = '没有创建权限！'
            elif e.status == 409:
                msg = 'Deployment已经存在！'
            elif e.status == 422:
                msg = f'reason:"{e.reason}"<br>message:{json.loads(e.body).get("message")}'
            else:
                print(e)
                msg = e.reason
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)


class DeploymentDetailsView(View):

    def get(self, request):
        namespace = self.request.GET.get('namespace', None)
        dp_name = self.request.GET.get('name', None)
        if not namespace or not dp_name:
            return redirect('deployment')
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        apps_api = client.AppsV1Api()
        networking_api = client.NetworkingV1beta1Api()

        dp_info = list()
        for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
            if dp_name == dp.metadata.name:
                name = dp.metadata.name
                namespace = dp.metadata.namespace
                replicas = dp.spec.replicas
                available_replicas = (
                    0 if dp.status.available_replicas is None else dp.status.available_replicas
                )
                labels = dp.metadata.labels
                selector = dp.spec.selector.match_labels

                # 通过deployment反向查询对应service
                service = list()
                svc_name = None
                for svc in core_api.list_namespaced_service(namespace=namespace).items:
                    if svc.spec.selector == selector:
                        svc_name = svc.metadata.name
                        svc_type = svc.spec.type
                        cluster_ip = svc.spec.cluster_ip
                        ports = svc.spec.ports

                        service.append({'type': svc_type, 'cluster_ip': cluster_ip, 'ports': ports})
                # service没有创建，ingress也没有
                ingress = {'rules': None, 'tls': None}
                for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                    for r in ing.spec.rules:
                        for b in r.http.paths:
                            if b.backend.service_name == svc_name:
                                ingress['rules'] = ing.spec.rules
                                ingress['tls'] = ing.spec.tls

                containers = list()
                for c in dp.spec.template.spec.containers:
                    c_name = c.name
                    image = c.image
                    liveness_probe = c.liveness_probe
                    readiness_probe = c.readiness_probe
                    resources = c.resources  # 在前端处理
                    env = c.env
                    ports = c.ports
                    volume_mounts = c.volume_mounts
                    args = c.args
                    command = c.command

                    container = {"name": c_name, "image": image, "liveness_probe": liveness_probe,
                                 "readiness_probe": readiness_probe,
                                 "resources": resources, "env": env, "ports": ports,
                                 "volume_mounts": volume_mounts, "args": args, "command": command}
                    containers.append(container)

                tolerations = dp.spec.template.spec.tolerations
                rolling_update = dp.spec.strategy.rolling_update
                volumes = []
                if dp.spec.template.spec.volumes is not None:
                    for v in dp.spec.template.spec.volumes:
                        volume = {}
                        if v.config_map is not None:
                            volume["config_map"] = v.config_map
                        elif v.secret is not None:
                            volume["secret"] = v.secret
                        elif v.empty_dir is not None:
                            volume["empty_dir"] = v.empty_dir
                        elif v.host_path is not None:
                            volume["host_path"] = v.host_path
                        elif v.config_map is not None:
                            volume["downward_api"] = v.downward_api
                        elif v.config_map is not None:
                            volume["glusterfs"] = v.glusterfs
                        elif v.cephfs is not None:
                            volume["cephfs"] = v.cephfs
                        elif v.rbd is not None:
                            volume["rbd"] = v.rbd
                        elif v.persistent_volume_claim is not None:
                            volume["persistent_volume_claim"] = v.persistent_volume_claim
                        else:
                            volume["unknown"] = "unknown"
                        volumes.append(volume)

                rs_number = dp.spec.revision_history_limit
                create_time = k8s.dt_format(dp.metadata.creation_timestamp)

                dp_info = {"name": name, "namespace": namespace, "replicas": replicas,
                           "available_replicas": available_replicas, "labels": labels,
                           "selector": selector, "containers": containers, "rs_number": rs_number,
                           "rolling_update": rolling_update, "create_time": create_time, "volumes": volumes,
                           "tolerations": tolerations, "service": service, "ingress": ingress}
        result = {'dp_name': dp_name, 'namespace': namespace, 'dp_info': dp_info}
        return render(request, 'workload/deployment_details.html', result)


class ReplicasetApiView(View):

    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        apps_api = client.AppsV1Api()
        dp_name = request.GET.get('name', None)
        namespace = request.GET.get('namespace', None)
        data = list()
        for rs in apps_api.list_namespaced_replica_set(namespace=namespace).items:
            current_dp_name = rs.metadata.owner_references[0].name
            rs_name = rs.metadata.name
            if dp_name == current_dp_name:
                namespace = rs.metadata.namespace
                replicas = rs.status.replicas
                available_replicas = rs.status.available_replicas
                ready_replicas = rs.status.ready_replicas
                revision = rs.metadata.annotations["deployment.kubernetes.io/revision"]
                create_time = k8s.dt_format(rs.metadata.creation_timestamp)

                containers = {}
                for c in rs.spec.template.spec.containers:
                    containers[c.name] = c.image

                rs = dict(
                    name=rs_name, namespace=namespace, replicas=replicas, available_replicas=available_replicas,
                    ready_replicas=ready_replicas, revision=revision, containers=containers, create_time=create_time
                )
                data.append(rs)
        count = len(data)
        result = dict(code=0, msg='', count=count, data=data)
        return JsonResponse(result)

    @method_decorator(k8s.self_login_request)
    def post(self, request):
        k8s.load_auth(request=self.request)
        apps_beta_api = client.ExtensionsV1beta1Api()
        dp_name = request.POST.get('dn_name', None)
        namespace = request.POST.get('namespace', None)
        reversion = request.POST.get('reversion', None)
        body = dict(name=dp_name, rollback_to=dict(reversion=reversion))
        try:
            apps_beta_api.create_namespaced_deployment_rollback(name=dp_name, namespace=namespace, body=body)
        except client.exceptions.ApiException as e:
            code = e.status
            if e.status == 403:
                msg = '没有回滚权限！'
            elif e.status == 422:
                e = json.loads(e.body)
                msg = e.get('message')
            else:
                msg = f'{e.reason}'
        else:
            code, msg = 0, '回滚成功'
        result = dict(code=code, msg=msg)
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

    @method_decorator(k8s.self_login_request)
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


class PodsLogView(View):
    decorators = [k8s.self_login_request, xframe_options_sameorigin]

    @method_decorator(decorators)
    def get(self, request):
        namespace = request.GET.get("namespace")
        pod_name = request.GET.get("pod_name")
        containers = request.GET.get("containers").split(',')  # 返回 nginx1,nginx2，转成一个列表方便前端处理
        connect = {'namespace': namespace, 'pod_name': pod_name, 'containers': containers}
        return render(self.request, 'workload/pods_log.html', connect)

    @method_decorator(k8s.self_login_request)
    def post(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        name = request.POST.get("name", None)
        namespace = request.POST.get("namespace", None)
        container = request.POST.get('container')
        try:
            log_text = core_api.read_namespaced_pod_log(name=name, namespace=namespace, container=container,
                                                        tail_lines=500)
        except client.exceptions.ApiException as e:
            code = e.status
            if e.status == 403:
                msg = '你没有查看日志权限'
            else:
                msg = f'获取日志失败<br>{e}'

            result = {'code': code, 'msg': msg}
        else:
            code = 0
            if len(log_text) == 0:
                msg = "没有日志！"
                log_text = "没有日志！"
            else:
                msg = "获取日志成功！"
            result = {'code': code, 'msg': msg, 'data': log_text}
        return JsonResponse(result)


class PodsApiView(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        namespace = self.request.GET.get('namespace', None)
        search_key = self.request.GET.get('search_key', None)
        node_name = self.request.GET.get('node_name', None)
        try:

            if namespace is not None:
                data = list()
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

                            c = {
                                'c_name': c_name, 'c_image': c_image,
                                'restart_count': restart_count, 'c_status': c_status
                            }
                            containers.append(c)

                    create_time = k8s.dt_format(po.metadata.creation_timestamp)
                    po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                          "labels": labels, "containers": containers, "status": status,
                          "create_time": create_time}
                    if search_key:
                        if search_key in name:
                            data.append(po)
                    else:
                        data.append(po)

            elif node_name is not None:
                data = node_data.node_pods(core_api, node_name)
            else:
                raise client.exceptions.ApiException
            code, msg = 0, '数据返回成功！'
        except client.exceptions.ApiValueError as e:
            code, msg = 1, '{}'.format(e)
            result = {'code': code, 'msg': msg}
        except client.exceptions.ApiException as e:
            code = 1
            if e.status == 403:
                msg = '没有访问权限！，默认使用default空间'
            else:
                msg = '获取数据失败！'
            result = {'code': code, 'msg': msg}
        else:
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

    @method_decorator(k8s.self_login_request)
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


class TerminalView(View):
    decorators = [k8s.self_login_request, xframe_options_sameorigin]

    @method_decorator(decorators)
    def get(self, request):
        namespace = request.GET.get("namespace")
        pod_name = request.GET.get("pod_name")
        containers = request.GET.get("containers").split(',')  # 返回 nginx1,nginx2，转成一个列表方便前端处理
        # 认证类型和token，用于传递到websocket，websocket根据sessionid获取token，让websocket处理连接k8s认证用
        auth_type = request.session.get('auth_type')
        token = request.session.get('token')
        connect = {'namespace': namespace, 'pod_name': pod_name, 'containers': containers, 'auth_type': auth_type,
                   'token': token}
        return render(self.request, 'workload/terminal.html', {'connect': connect})
