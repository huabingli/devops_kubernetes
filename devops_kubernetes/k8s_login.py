from django.conf import settings
from django.shortcuts import redirect


from kubernetes import client, config

from pathlib import Path


def auth_check(auth_type, token):
    if auth_type == 'token':
        configuration = client.Configuration()
        configuration.host = 'https://192.168.35.61:6443'
        configuration.ssl_ca_cert = Path(settings.BASE_DIR, 'static', 'ca.crt')
        configuration.verify_ssl = True
        configuration.api_key = {'authorization': 'Bearer {}'.format(token)}
        client.Configuration.set_default(configuration)

    elif auth_type == 'kube_config':
        file_path = Path('kube_config', token)
        config.load_kube_config(r'%s' % file_path)

    try:
        core_api = client.CoreApi()
        core_api.get_api_versions()
        code = 0
        msg = '登录成功'
    except client.exceptions.ApiException as e:
        print(e)
        if auth_type == 'kube_config':
            msg = '认证文件无效'
        elif auth_type == 'token':
            msg = 'token无效'
        else:
            msg = '请使用认证文件或者token认证'
        code = 1
    result = {'code': code, 'msg': msg}
    return result


def self_login_request(func=None):
    # from django.http import HttpResponseRedirect

    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        if is_login:
            return func(request, *args, **kwargs)
        else:
            # path = request.path
            return redirect('login')
            # return HttpResponseRedirect(reverse('login') + '?pre_url=' + path)  # 用于记录访问历史页面，便于登录后跳转

    return inner
