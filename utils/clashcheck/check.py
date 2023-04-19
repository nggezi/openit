import requests
import json

def check(alive, proxy, apiurl, sema, timeout, testurl):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl+'&timeout=' + str(timeout), timeout=10)
        response = json.loads(r.text)
        if 'delay' in response and response['delay'] > 0:
            download_time_response = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url=https://cachefly.cachefly.net/10mb.test&timeout=' + str(timeout), timeout=10)
            download_response = json.loads(download_time_response.text)
            if 'delay' in download_response and download_response['delay'] > 0:
                download_time = download_response['delay']
                download_speed = 10 / download_time
                if download_speed > 3:
                    alive.append(proxy)
    except:
        pass

    sema.release()
