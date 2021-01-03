from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response

from pathlib import Path

# from kubernetes import client, config

from devops_kubernetes.k8s_login import auth_check, self_login_request


# Create your views here.
class LogIn(View):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        token = self.request.POST.get('token', None)
        if token:
            result = auth_check(token=token, auth_type='token')
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
            result = auth_check(auth_type='kube_config', token=random_str)
            if result.get('code') == 0:
                request.session['is_login'] = True
                request.session['auth_type'] = 'kube_config'
                request.session['token'] = random_str
        next_file = request.GET.get('next', None)
        if next_file:
            result['next'] = next_file
        print(result)
        return JsonResponse(result)


def logout(request):
    request.session.delete()
    return redirect('login')


class IndexViewApi(APIView):
    @method_decorator(self_login_request)
    def get(self, request):
        return Response({'code': 1, 'msg': 'test测试使用'})
