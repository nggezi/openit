import requests
import json


def check(alive, proxies, apiurl, sema, timeout, testurl):
    if not proxies:
        return
    
    first_pass = []
    
    # Test delay for the first URL and filter proxies with delay > 0
    for proxy in proxies:
        try:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=' + testurl + '&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                first_pass.append(proxy)
        except:
            pass
    
    if not first_pass:
        return
    
    second_pass = []
    
    # Test delay for the second URL and filter proxies with delay > 0
    for proxy in first_pass:
        try:
            r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
            response = json.loads(r.text)
            if 'delay' in response and response['delay'] > 0:
                r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/speed?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
                response = json.loads(r.text)
                if 'speed' in response and response['speed'] > 3:
                    second_pass.append(proxy)
        except:
            pass
    
    alive.extend(second_pass)
    sema.release()
