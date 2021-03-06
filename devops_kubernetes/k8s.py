from django.conf import settings
from django.shortcuts import redirect
from django.core.cache import cache

from kubernetes import client, config

from pathlib import Path


# k8s认证
def load_auth(auth_type=None, token=None, **kwargs):
    if not auth_type and not token:
        request = kwargs.get('request', None)
        auth_type = request.session.get('auth_type')
        token = request.session.get('token')
    if auth_type == 'token':
        token = cache.get(token)
        configuration = client.Configuration()
        configuration.host = 'https://192.168.35.61:6443'
        configuration.ssl_ca_cert = Path(settings.BASE_DIR, 'static', 'ca.crt')
        configuration.verify_ssl = True
        configuration.api_key = {'authorization': 'Bearer {}'.format(token)}
        client.Configuration.set_default(configuration)

    elif auth_type == 'kube_config':
        """
        弃用的认证方式
        # file_path = Path('kube_config', token)
        # config.load_kube_config(r'%s' % file_path)
        """
        kube_yaml = cache.get(token)
        config.load_kube_config_from_dict(kube_yaml)


def auth_check(auth_type, token):
    load_auth(auth_type, token)
    try:
        core_api = client.CoreApi()
        core_api.get_api_versions()
        code = 0
        msg = '登录成功'
    except client.exceptions.ApiException as e:
        print(e.status)
        if auth_type == 'kube_config':
            msg = '认证文件无效'
        elif auth_type == 'token':
            msg = 'token无效'
        else:
            msg = '请使用认证文件或者token认证'
        code = 1
    result = {'code': code, 'msg': msg}
    return result


# 登录认证装饰器
def self_login_request(func):
    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        random_str_token = request.session.get('token', 'None')
        token = True if cache.get(random_str_token, False) else False
        # 设置cache中config配置文件的过期时间
        if token:
            # 获取session过期时间
            time = request.session.get_expiry_age()
            # 更新cache过期时间
            cache.touch(random_str_token, time)
        if is_login and token:
            return func(request, *args, **kwargs)
        else:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    return inner


def paging_data(page, limit, data):
    page, limit = int(page), int(limit)
    start = (page - 1) * limit
    end = page * limit
    data = data[start:end]
    return data


# 内存转换
def memory_convert(value):
    import re
    value = int(''.join(re.findall(r'\d', value)))
    units = ["KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size


# 时间转换
def dt_format(timestamp):
    from datetime import date, timedelta
    t = date.strftime(timestamp + timedelta(hours=8), '%Y-%m-%d %H:%M:%S')
    return t
