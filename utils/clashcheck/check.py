import requests
import json
from threading import Thread, Semaphore

def check(alive, proxy, apiurl, sema, timeout, testurl):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl + '&timeout=' + str(timeout), timeout=10)
        response = json.loads(r.text)
        if 'delay' in response and response['delay'] > 0:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                download_time = requests.get(url=testurl, proxies={'http': proxy['proxy'],'https': proxy['proxy']}, timeout=10).elapsed.total_seconds()
                download_speed = 10 / download_time
                if download_speed > 3:
                    alive.append(proxy)
    except:
        pass
    sema.release()


def check_proxies(apiurl, testurl, timeout=10, threads=100):
    proxies = json.loads(requests.get(apiurl + '/proxies', timeout=10).text)
    alive = []
    sema = Semaphore(threads)
    for proxy in proxies:
        sema.acquire()
        t = Thread(target=check, args=(alive, proxy, apiurl, sema, timeout, testurl))
        t.start()
    for i in range(threads):
        sema.acquire()
    return alive
