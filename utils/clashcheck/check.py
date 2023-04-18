import requests
import yaml


# 定义检测代理的函数
def check(alive, proxy, apiurl, sema, timeout, testurl, download_speed):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl+'&timeout=' + str(timeout), timeout=10)
        response = json.loads(r.text)
        if 'delay' in response and response['delay'] > 0:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                download_time = response['delay']
                download_speed_actual = 10 / download_time
                if download_speed> download_speed:
                    alive.append(proxy)
    except:
        pass
    sema.release()
