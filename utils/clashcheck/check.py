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
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl + '&timeout=' + str(timeout), timeout=5)
        response = json.loads(r.text)
        if 'delay' in response and response['delay'] > 0:
            alive.append(proxy)

        if testurl1 is not None:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl1 + '&timeout=' + str(timeout), timeout=5)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                alive.append(proxy)
    except:
        pass

    sema.release()
