from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from kubernetes import client, config

from django.conf import settings

from pathlib import Path


# Create your views here.
def core_api_def(*args, **kwargs):
    file_path = kwargs.get('file_path', None)
    token = kwargs.get('token', None)
    if file_path:
        config.load_kube_config(r'%s' %file_path)
    elif token:
        configuration = client.Configuration()
        configuration.host = 'https://192.168.35.61:6443'
        print(Path('static', 'ca.crt'))
        configuration.ssl_ca_cert = Path(settings.STATICFILES_DIRS, 'static', 'ca.crt')
        print(Path(settings.STATICFILES_DIRS, 'static', 'ca.crt'))
        configuration.verify_ssl = True
        configuration.api_key = {'authorization': 'Bearer' + token}
        client.Configuration.set_default(configuration)
    try:
        core_api = client.CoreApi()
        core_api.get_api_versions()
        code = 0
        msg = '登录成功'
    except client.exceptions.ApiException as e:
        print(e)
        if file_path:
            msg = '认证文件无效'
        elif token:
            msg = 'token无效'
        else:
            msg = '请使用认证文件或者token认证'
        code = 1
    result = {'code': code, 'msg': msg}
    return result


class LogIn(View):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        token = self.request.POST.get('token', None)
        if token:
            result = core_api_def(token=token)

        else:
            import random
            import hashlib
            random_str = hashlib.md5(str(random.random()).encode()).hexdigest()
            file_path = Path('kube_config', random_str)
            file_obj = request.FILES.get("file")
            try:
                with open(file_path, 'w', encoding='utf8') as f:
                    date = file_obj.read().decode()
                    f.write(date)
            except Exception as e:
                print(e)
                code = 1
                msg = '文件类型错误！'
                result = {'code': code, 'msg': msg}
                return JsonResponse(result)
            result = core_api_def(file_path=file_path)
        return JsonResponse(result)


class Index(TemplateView):
    template_name = 'index.html'

    def post(self):
        pass
