import re
from kubernetes import client
from devops_kubernetes import k8s


# CPU单位转浮点数
def cpu_unit_tof(c):
    if c.endswith('m'):
        n = re.findall(r'\d+', c)[0]
        n = round(float(n) / 1000, 2)
        return n
    else:
        return float(c)


def memory_unit_tog(m):
    g = float
    if m.endswith('M') or m.endswith('Mi'):
        m = re.findall(r'\d+', m)[0]
        g = round(float(m) / 1024, 2)
    elif m.endswith('K') or m.endswith('Ki'):
        k = re.findall(r'\d+', m)[0]
        g = round(float(k) / 1024 / 1024, 2)
    elif m.endswith('G') or m.endswith('Gi'):
        g = re.findall(r'\d+', m)[0]
    return g


def node_info(core_api, n_name=None):
    node_dic: dict = dict()
    for node in core_api.list_node().items:
        node_name: str = node.metadata.name
        node_dic[node_name] = dict(
            node_name='', hostname='', internal_ip='', os="", cpu_arch='', kernel='',
            pod_cidr='', container_runtime_version='', kubelet_version='', kube_proxy_version='',
            labels='', unschedulable='', taints='', create_time=''
        )
        node_dic[node_name]['node_name'] = node_name
        for i in node.status.addresses:
            if i.type == 'InternalIP':
                node_dic[node_name]['internal_ip'] = i.address
            elif i.type == 'Hostname':
                node_dic[node_name]['hostname'] = i.address
        node_dic[node_name]['pod_cidr'] = node.spec.pod_cidr
        node_dic[node_name]["os"] = node.status.node_info.os_image
        node_dic[node_name]["kernel"] = node.status.node_info.kernel_version
        node_dic[node_name]["cpu_arch"] = node.status.node_info.architecture
        node_dic[node_name]["container_runtime_version"] = node.status.node_info.container_runtime_version
        node_dic[node_name]["kubelet_version"] = node.status.node_info.kubelet_version
        node_dic[node_name]["kube_proxy_version"] = node.status.node_info.kube_proxy_version
        node_dic[node_name]["unschedulable"] = ("是" if node.spec.unschedulable else "否")
        node_dic[node_name]["labels"] = node.metadata.labels
        node_dic[node_name]["taints"] = node.spec.taints
        node_dic[node_name]["create_time"] = k8s.dt_format(node.metadata.creation_timestamp)

    if n_name is None:
        return node_dic
    else:
        return node_dic[n_name]


def node_resource(core_api, n_name=None):
    node_resources = dict()
    for node in core_api.list_node().items:
        node_name = node.metadata.name
        node_resources[node_name] = dict(
            allocatable_cpu="", capacity_cpu="", allocatable_memory="", capacity_memory="",
            allocatable_ephemeral_storage="", capacity_ephemeral_storage="",
            capacity_pods="", pods_number=round(0, 2), cpu_requests=round(0, 2), cpu_limits=round(0, 2),
            memory_requests=round(0, 2), memory_limits=round(0, 2)
        )
        # 可分配资源
        allocatable_cpu = node.status.allocatable['cpu']
        allocatable_memory = node.status.allocatable['memory']
        allocatable_storage = node.status.allocatable['ephemeral-storage']
        node_resources[node_name]["allocatable_cpu"] = int(allocatable_cpu)
        node_resources[node_name]["allocatable_memory"] = memory_unit_tog(allocatable_memory)
        allocatable_storage = round(int(allocatable_storage) / 1024 / 1024 / 1024, 2)
        node_resources[node_name]["allocatable_ephemeral_storage"] = allocatable_storage

        # 总容量
        capacity_cpu = node.status.capacity['cpu']
        capacity_memory = node.status.capacity['memory']
        capacity_storage = node.status.capacity['ephemeral-storage']
        capacity_pods = node.status.capacity['pods']
        node_resources[node_name]["capacity_cpu"] = int(capacity_cpu)
        node_resources[node_name]["capacity_memory"] = memory_unit_tog(capacity_memory)
        node_resources[node_name]["capacity_ephemeral_storage"] = memory_unit_tog(capacity_storage)
        node_resources[node_name]["capacity_pods"] = capacity_pods

        # 调度 & 准备就绪
        schedulable = node.spec.unschedulable
        status = node.status.conditions[-1].status  # 取最新状态
        node_resources[node_name]["schedulable"] = schedulable
        node_resources[node_name]["status"] = status

        # 如果不传节点名称计算资源请求和资源限制并汇总，否则返回节点资源信息
    for pod in core_api.list_pod_for_all_namespaces().items:
        # pod_name = pod.metadata.name
        node_name = pod.spec.node_name
        # print(pod_name)
        # node_resources[node_name]['pod_name'] = pod_name
        # 如果节点名为None，说明该Pod未成功调度创建，跳出循环，不计算其中
        if node_name is None:
            continue

            # 遍历pod中容器
        for c in pod.spec.containers:
            # c_name = c.name
            # 资源请求
            if c.resources.requests is not None:
                if "cpu" in c.resources.requests:
                    cpu_request = c.resources.requests["cpu"]
                    # 之前用 += 方式，但浮点数运算时会出现很多位小数，所以要用round取小数
                    node_resources[node_name]['cpu_requests'] = round(
                        node_resources[node_name]['cpu_requests'] + cpu_unit_tof(cpu_request), 2
                    )
                if "memory" in c.resources.requests:
                    memory_request = c.resources.requests["memory"]
                    node_resources[node_name]['memory_requests'] = round(
                        node_resources[node_name]['memory_requests'] + memory_unit_tog(memory_request), 2
                    )
            # 资源限制
            if c.resources.limits is not None:
                if "cpu" in c.resources.limits:
                    cpu_limit = c.resources.limits["cpu"]
                    node_resources[node_name]['cpu_limits'] = round(
                        node_resources[node_name]['cpu_limits'] + cpu_unit_tof(cpu_limit), 2)
                if "memory" in c.resources.limits:
                    memory_limit = c.resources.limits["memory"]
                    node_resources[node_name]['memory_limits'] = round(
                        node_resources[node_name]['memory_limits'] + memory_unit_tog(memory_limit), 2)
        node_resources[node_name]['pods_number'] += 1

    if n_name is None:
        return node_resources
    else:
        return node_resources[n_name]


def node_pods(core_api, node_name):
    data = list()
    for pod in core_api.list_pod_for_all_namespaces().items:
        name = pod.spec.node_name
        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace
        status = ("运行中" if pod.status.conditions[-1].status else "异常")
        host_network = pod.spec.host_network
        pod_ip = ("主机网络" if host_network else pod.status.pod_ip)
        create_time = k8s.dt_format(pod.metadata.creation_timestamp)

        if name == node_name:
            if len(pod.spec.containers) == 1:
                cpu_requests = "0"
                cpu_limits = "0"
                memory_requests = "0"
                memory_limits = "0"
                for c in pod.spec.containers:
                    # c_name = c.name
                    # c_image= c.image
                    cpu_requests = "0"
                    cpu_limits = "0"
                    memory_requests = "0"
                    memory_limits = "0"
                    if c.resources.requests is not None:
                        if "cpu" in c.resources.requests:
                            cpu_requests = c.resources.requests["cpu"]
                        if "memory" in c.resources.requests:
                            memory_requests = c.resources.requests["memory"]
                    if c.resources.limits is not None:
                        if "cpu" in c.resources.limits:
                            cpu_limits = c.resources.limits["cpu"]
                        if "memory" in c.resources.limits:
                            memory_limits = c.resources.limits["memory"]
            else:
                c_r = "0"
                c_l = "0"
                m_r = "0"
                m_l = "0"
                cpu_requests = ""
                cpu_limits = ""
                memory_requests = ""
                memory_limits = ""
                for c in pod.spec.containers:
                    c_name = c.name
                    # c_image= c.image
                    if c.resources.requests is not None:
                        if "cpu" in c.resources.requests:
                            c_r = c.resources.requests["cpu"]
                        if "memory" in c.resources.requests:
                            m_r = c.resources.requests["memory"]
                    if c.resources.limits is not None:
                        if "cpu" in c.resources.limits:
                            c_l = c.resources.limits["cpu"]
                        if "memory" in c.resources.limits:
                            m_l = c.resources.limits["memory"]

                    cpu_requests += "%s=%s<br>" % (c_name, c_r)
                    cpu_limits += "%s=%s<br>" % (c_name, c_l)
                    memory_requests += "%s=%s<br>" % (c_name, m_r)
                    memory_limits += "%s=%s<br>" % (c_name, m_l)

            pod = {"pod_name": pod_name, "namespace": namespace, "status": status, "pod_ip": pod_ip,
                   "cpu_requests": cpu_requests, "cpu_limits": cpu_limits, "memory_requests": memory_requests,
                   "memory_limits": memory_limits, "create_time": create_time}
            data.append(pod)
    return data
