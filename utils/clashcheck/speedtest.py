import requests

def download_speed_test(proxy, download_test_url, download-test-timeout):
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
        response = requests.get(download_results, proxy, download_test_url, download_test_timeout, sema_download)
        speed_in_bytes = len(response.content)
        speed_in_mb = speed_in_bytes / (1024 * 1024)
        return speed_in_mb
    except Exception as e:
        print(f"Download speed test failed for proxy {proxy['name']}: {str(e)}")
        return None
