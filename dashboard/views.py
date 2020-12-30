from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from kubernetes import client, config

from devops_kubernetes.settings import BASE_DIR

from pathlib import Path


# Create your views here.
class LogIn(TemplateView):
    template_name = "login.html"

    def post(self, *args, **kwargs):
        token = self.request.POST.get('token', None)
        if token:
            configuration = client.Configuration()
            configuration.host = 'https://192.168.35.61:6443'
            configuration.ssl_ca_cert = Path(BASE_DIR, 'static', 'ca.crt')
            configuration.verify_ssl = True
            configuration.api_key = {'authorization': 'Bearer' + token}
            client.Configuration.set_default(configuration)
        else:
            import random, hashlib
            random_str = hashlib.md5(str(random.random()).encode()).hexdigest()
            file_path = Path(BASE_DIR, 'kube_config', random_str)
            file_obj = self.request.FILES.get('file')
            print(self.request.FILES)
            try:
                with open(file_path, 'w', encoding='utf8') as f:
                    date = file_obj.read().decode()
                    f.write(date)
            except Exception as e:
                print(e)
                code = 1
                msg = '文件类型错误'
                res = {'code': code, 'msg': msg}
                return JsonResponse(res)
            config.load_kube_config(file_path)
        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()
            code = 0
            msg = '登录成功'
        except Exception as e:
            code = 1
            if e.args:
                msg = 'token无效'
            else:
                msg = '错误'
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)


class Index(TemplateView):
    template_name = 'index.html'

    def post(self):
        pass
