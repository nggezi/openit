import requests

def download_speed_test(proxy, download_test_url, download_test_timeout):
    """
    下载速度测试

    Args:
        proxy (dict): 代理信息
        download_test_url (str): 下载测试文件的 URL
        download_test_timeout (int): 下载超时时间

    Returns:
        float: 下载速度（单位：MB/s）
    """
    try:
        response = requests.get(download_test_url, proxies=proxy, timeout=download_test_timeout)
        speed_in_bytes = len(response.content)
        speed_in_mb = speed_in_bytes / (1024 * 1024)
        return speed_in_mb
    except Exception as e:
        print("下载速度测试失败:", str(e))
        return None
sema.release()
