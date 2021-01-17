from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator

from pathlib import Path

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
            file_path = Path('kube_config', random_str)
            file_obj = request.FILES.get("file")
            try:
                with open(file_path, 'w', encoding='utf8') as f:
                    date = file_obj.read().decode()
                    f.write(date)
            except FileNotFoundError:
                import os
                os.mkdir('kube_config')
                return JsonResponse({'code': 1, 'msg': '请刷新后重试！'})
            except Exception as e:
                return JsonResponse({'code': 1, 'msg': '文件类型错误！', 'except': '{}'.format(e)})
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
