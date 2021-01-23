import yaml

from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.core.cache import cache

from kubernetes import client

from devops_kubernetes import k8s


# Create your views here.
class LogIn(View):
    template_name = "dashboard/login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        token = self.request.POST.get('token', None)
        if token:
            result = k8s.auth_check(token=token, auth_type='token')
            if result.get('code') == 0:
                request.session['is_login'] = True
                request.session['auth_type'] = 'token'
                request.session['token'] = token
        else:
            import random
            import hashlib
            random_str = hashlib.md5(str(random.random()).encode()).hexdigest()
            random_str = f'kube_config.{random_str}'
            """
            弃用的kube_config保存，使用缓存来存储数据
            # file_path = Path('kube_config', random_str)
            # file_obj = request.FILES.get("file")
            # try:
            #     with open(file_path, 'w', encoding='utf8') as f:
            #         date = file_obj.read().decode()
            #         f.write(date)
            # except FileNotFoundError:
            #     import os
            #     os.mkdir('kube_config')
            #     return JsonResponse({'code': 1, 'msg': '请刷新后重试！'})
            # except Exception as e:
            #     return JsonResponse({'code': 1, 'msg': '文件类型错误！', 'except': '{}'.format(e)})
            """
            file_obj = request.FILES.get("file")
            try:
                context = file_obj.read().decode()
                context = yaml.load(context, Loader=yaml.FullLoader)
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': '文件类型错误！', 'except': '{}'.format(e)})
            else:
                cache.set(random_str, context, timeout=86400)
                result = k8s.auth_check(auth_type='kube_config', token=random_str)
            if result.get('code') == 0:
                request.session['is_login'] = True
                request.session['auth_type'] = 'kube_config'
                request.session['token'] = random_str
        next_file = request.GET.get('next', None)
        if next_file:
            result['next'] = next_file
        return JsonResponse(result)


def logout(request):
    request.session.clear()
    return redirect('login')


class IndexViewApi(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        return render(request, 'test.html')


class ExportResourceViewApi(View):
    @method_decorator(k8s.self_login_request)
    def get(self, request):
        import yaml
        import json
        k8s.load_auth(request=self.request)
        core_api = client.CoreV1Api()
        apps_api = client.AppsV1Api()
        networking_api = client.NetworkingV1beta1Api()
        namespace = self.request.GET.get('namespace', None)
        resource = self.request.GET.get('resource', None)
        name = self.request.GET.get('name', None)

        try:
            if resource == 'namespace':
                data_dict = core_api.read_namespace(name=name, _preload_content=False).read()
            elif resource == 'deployment':
                data_dict = apps_api.read_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'replicaset':
                data_dict = apps_api.read_namespaced_replica_set(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'daemonset':
                data_dict = apps_api.read_namespaced_daemon_set(
                    namespace=namespace,
                    name=name,
                    _preload_content=False
                ).read()
            elif resource == 'statefulset':
                data_dict = apps_api.read_namespaced_stateful_set(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'pod':
                data_dict = core_api.read_namespaced_pod(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'service':
                data_dict = core_api.read_namespaced_service(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'ingress':
                data_dict = networking_api.read_namespaced_ingress(
                    namespace=namespace,
                    name=name,
                    _preload_content=False
                ).read()
            elif resource == 'pvc':
                data_dict = core_api.read_namespaced_persistent_volume_claim(
                    name=name,
                    namespace=namespace,
                    _preload_content=False
                ).read()
            elif resource == 'pv':
                data_dict = core_api.read_persistent_volume(name=name, _preload_content=False).read()
            elif resource == 'node':
                data_dict = core_api.read_node(name=name, _preload_content=False).read()
            elif resource == 'configmap':
                data_dict = core_api.read_namespaced_config_map(
                    namespace=namespace,
                    name=name,
                    _preload_content=False
                ).read()
            elif resource == 'secret':
                data_dict = core_api.read_namespaced_secret(
                    namespace=namespace,
                    name=name,
                    _preload_content=False
                ).read()
            else:
                raise client.exceptions.ApiException(status=400, reason='未选择资源')
        except client.exceptions.ApiValueError as e:
            result = {'code': 1, 'msg': '{}'.format(e)}
        except client.exceptions.ApiException as e:
            result = {'code': 1, 'msg': '{}'.format(e)}
        else:
            try:
                data_str = str(data_dict, 'utf-8')
                data_yaml = yaml.safe_dump(json.loads(data_str))
            except Exception as e:
                result = {'code': 1, 'msg': '{}'.format(e)}
            else:
                result = {'code': 0, 'msg': '获取数据成功', 'data': data_yaml}
        return JsonResponse(result)


@xframe_options_sameorigin
def ace_editor(request):
    if request.method == 'GET':
        name = request.GET.get('name', None)
        namespace = request.GET.get('namespace', None)
        resource = request.GET.get('resource', None)

        return render(request, 'ace_editor.html', {'name': name, 'namespace': namespace, 'resource': resource})
