"""
根据是否存在第二轮测试 testurl1 的判断，决定使用哪个 URL 进行测试。
如果存在第二轮测试，则使用 testurl1 进行测试；否则，只执行第一轮测试，使用 testurl 进行测试。
请注意，在 main.py 中调用 check() 函数时，确保正确传入 testurl 和 testurl1 的值。
"""

import requests
import json

def check(alive, proxy, apiurl, sema, timeout, testurl, testurl1=None):
    """
    检查代理的活跃性

    Args:
        alive (list): 存储活跃代理的列表
        proxy (dict): 待测试的代理信息
        apiurl (str): Clash API 的 URL
        sema (Semaphore): 信号量，用于进程同步
        timeout (int): 请求超时时间
        testurl (str): 第一轮测试的 URL
        testurl1 (str, optional): 第二轮测试的 URL，可选参数

    Returns:
        None
    """
    try:
        # 根据是否存在第二轮测试选择测试的 URL
        if testurl1 is not None and testurl1.strip():
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl1 + '&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            # 如果延迟大于0，将代理添加到活跃代理列表
            if 'delay' in response and response['delay'] > 0:
                alive.append(proxy)
        else:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl + '&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            # 如果延迟大于0，将代理添加到活跃代理列表
            if 'delay' in response and response['delay'] > 0:
                alive.append(proxy)
    except:
        pass

    sema.release()
