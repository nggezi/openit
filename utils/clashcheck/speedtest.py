import requests
import time

import requests
import json

def download_speed_test(alive, proxy, apiurl, timeout, download_test_url, download_test_timeout, sema1):
    try:
        r = requests.get(url=apiurl + '/proxies/' + str(proxy['name']) + '/delay?url='+download_test_url+'&timeout=' + str(timeout), timeout=download_test_timeout)
        response = json.loads(r.text)
        start_time = time.time()
        end_time = time.time()
        if response.status_code == 200:
            download_speed_bytes = len(response.content) / (end_time - start_time)
            download_speed_mbps = download_speed_bytes * 8 / 1000000  # 转换为兆字节/秒
            proxy['download_speed'] = download_speed_mbps
        else:
            proxy['download_speed'] = None

        download_results.append(proxy)
    except Exception:
        proxy['download_speed'] = None
        download_results.append(proxy)
    finally:
        sema1.release()

"""
def download_speed_test(download_results, proxy, download_test_url, download_test_timeout, sema1):
    try:
        session = requests.Session()
        session.proxies = {'http': proxy['proxies']['http'], 'https': proxy['proxies']['https']}
        start_time = time.time()
        response = session.get(download_test_url, timeout=download_test_timeout)
        end_time = time.time()

        if response.status_code == 200:
            download_speed_bytes = len(response.content) / (end_time - start_time)
            download_speed_mbps = download_speed_bytes * 8 / 1000000  # 转换为兆字节/秒
            proxy['download_speed'] = download_speed_mbps
        else:
            proxy['download_speed'] = None

        download_results.append(proxy)
    except Exception:
        proxy['download_speed'] = None
        download_results.append(proxy)
    finally:
        sema1.release()
"""
