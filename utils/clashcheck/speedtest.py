import requests

def download_speed_test(download_results, proxy, download_test_url, download_test_timeout, sema_download):
    """
    下载速度测试

    Args:
        proxy (dict): 代理信息
        download_test_url (str): 下载测试文件的 URL
        download_timeout (int): 下载超时时间

    Returns:
        float: 下载速度（单位：MB/s）
    """
    try:
        start_time = time.time()
        response = requests.get(download_results, proxy, download_test_url, download_test_timeout, sema_download)
        end_time = time.time()
        total_time = end_time - start_time
        latency = response.elapsed.total_seconds()
        file_size = len(response.content)
        file_in_mb = file_size / (1024 * 1024)
        speed_in_mb = file_in_mb / (total_time - latency)
        return speed_in_mb
    except Exception as e:
        print(f"Download speed test failed for proxy {proxy['name']}: {str(e)}")
        return None
