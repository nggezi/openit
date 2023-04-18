import requests
import json



def check(alive, proxy, apiurl,sema,timeout, testurl,testurl-google,testurl-10mb):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl-google+'&timeout=' + str(timeout), timeout=10)
        response = json.loads(r.text)
        try:
            if response['delay'] > 0:
                r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl+'&timeout=' + str(timeout), timeout=10)
                response = json.loads(r.text)
                try:
                    if response['delay'] > 0:
                        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+testurl-10mb+'&timeout=' + str(timeout), timeout=15)
                        response = json.loads(r.text)
                        try:
                            if response['delay'] > 0:
                                alive.append(proxy)
                        except:
                            pass
                except:
                    pass
        except:
            pass
    except:
        pass

    sema.release()
