import requests
import time

def download_speed_test(download_results, proxy, download_test_url, download_test_timeout, sema1):
    try:
        session = requests.Session()
        session.proxies = {'http': proxy['proxies']['http'], 'https': proxy['proxies']['https']}
        start_time = time.time()
        response = session.get(download_test_url, timeout=download_test_timeout)
        end_time = time.time()

        if response.status_code == 200:
            download_speed = len(response.content) / (end_time - start_time)
            proxy['download_speed'] = download_speed
        else:
            proxy['download_speed'] = None

        download_results.append(proxy)
    except Exception:
        proxy['download_speed'] = None
        download_results.append(proxy)
    finally:
        sema1.release()
