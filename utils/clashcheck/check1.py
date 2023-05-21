import requests
import json

def check1(alive, proxy, apiurl, sema, timeout, testurl1):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl1+'&timeout=' + str(timeout), timeout=10)
        response = json.loads(r.text)
        if 'delay' in response and response['delay'] > 0:
            alive.append(proxy)
    except: pass
    sema.release()
