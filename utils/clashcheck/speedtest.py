import time
import requests

def download_speed_test(download_results, proxy, download_test_url, download_test_timeout, download_speed_threads):
    start_time = time.time()  # 记录开始时间

    # 发起下载请求
    try:
        response = requests.get(download_test_url, proxies=proxy, timeout=download_test_timeout)
    except requests.exceptions.RequestException:
        download_time = None  # 下载失败，将下载时间设为 None
    else:
        end_time = time.time()  # 记录结束时间
        #delay = response.elapsed.total_seconds()  # 获取延迟时间

        download_time = end_time - start_time - delay  # 计算下载时间（减去延迟时间）

    # 将下载时间和代理信息保存到共享列表
    download_results.append({'proxy': proxy, 'download_time': download_time})
