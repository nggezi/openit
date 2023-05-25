import requests

def download_speed_test(proxy, download_test_url, download_test_timeout, download_results):
    """
    下载速度测试

    Args:
        proxy (dict): 代理信息
        download_test_url (str): 下载测试文件的 URL
        download_test_timeout (int): 下载超时时间
        download_results (list): 下载速度测试结果列表

    Returns:
        float: 下载速度（单位：MB/s）
    """
    try:
        response = requests.get(download_test_url, proxies=proxy, timeout=download_test_timeout)
        speed_in_bytes = len(response.content)
        speed_in_mb = speed_in_bytes / (1024 * 1024)
        
        # 将下载速度测试结果添加到共享列表中
        download_results.append({
            'proxy': proxy,
            'speed': speed_in_mb
        })
        
        return speed_in_mb
    except requests.RequestException as e:
        print("下载速度测试失败:", str(e))
    except Exception as e:
        print("下载速度测试异常:", str(e))

    return None
