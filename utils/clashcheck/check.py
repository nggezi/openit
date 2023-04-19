import requests
import json


def check(alive, proxies, apiurl, sema, timeout, testurl):
    # 如果代理池为空，直接返回
    if not proxies:
        return
    
    first_pass = []  # 用于存放第一轮测试通过的代理
    
    # 第一轮测试：测试代理的延迟
    for proxy in proxies:
        try:
            # 发起测试请求
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl + '&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                # 如果延迟大于0，代表请求成功，将该代理加入第一轮测试通过的代理列表
                first_pass.append(proxy)
        except:
            pass
    
    # 如果第一轮测试通过的代理列表为空，直接返回
    if not first_pass:
        return
    
    second_pass = []  # 用于存放第二轮测试通过的代理
    
    # 第二轮测试：测试代理的延迟和下载速度
    for proxy in first_pass:
        try:
            # 测试代理的延迟
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                # 如果延迟大于0，代表请求成功，继续测试下载速度
                r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/speed?url=https://cachefly.cachefly.net/1mb.test&timeout=' + str(timeout), timeout=100)
                response = json.loads(r.text)
                if 'speed' in response and response['speed'] > 3000000:
                    # 如果下载速度大于3MB/s，将该代理加入第二轮测试通过的代理列表
                    second_pass.append(proxy)
        except:
            pass
    
    # 将第二轮测试通过的代理列表添加到传递进来的代理存活列表中
    alive.extend(second_pass)
    sema.release()
