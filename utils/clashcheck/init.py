import os
import yaml
import shutil
import requests
from clash import filter
from yaml import SafeLoader

def init():
    if not os.path.exists('./temp'):
        os.mkdir('temp')

    config = 'config/config.yaml'
    # read from config file
    with open(config, 'r') as reader:
        config = yaml.load(reader, Loader=SafeLoader)
        http_port = config['http-port']
        api_port = config['api-port']
        threads = config['threads']
        source = str(config['source'])
        timeout = config['timeout']
        testurl = config['test-url']
        testurl1 = config.get('test-url1', '')  # 使用 get 方法获取键值，如果不存在则返回空字符串
        outfile = config['outfile']
        download_test_enable = config.get('download-test-enable', False)
        download_test_url = config.get('download-test-url', '')
        download_test_timeout = config.get('download-test-timeout', 5)
        download_speed_threshold = config.get('download-speed-threshold', 2)
        download_speed_threads = config.get('download_speed_threads', 5)
        
        # 添加下载速度测试的代码
        download_results = []
        if download_test_enable and download_test_url:
            for proxy in proxyconfig['proxies']:
                speed = download_speed_test(proxy, download_test_url, download_test_timeout)
                if speed is not None and speed > download_speed_threshold:
                    proxy['download-speed'] = speed
                    download_results.append(proxy)
        
        # get clash config file
        if source.startswith('http://'):
            proxyconfig = yaml.load(requests.get(source).text, Loader=SafeLoader)
        elif source.startswith('https://'):
            proxyconfig = yaml.load(requests.get(source).text, Loader=SafeLoader)
        else:
            with open(source, 'r') as reader:
                proxyconfig = yaml.load(reader, Loader=SafeLoader)

        # set clash api url
        baseurl = '127.0.0.1:' + str(api_port)
        apiurl = 'http://' + baseurl

        # filter config files
        proxyconfig = filter(proxyconfig)

        config = {'port': http_port, 'external-controller': baseurl, 'mode': 'global',
                  'log-level': 'silent', 'proxies': proxyconfig['proxies']}

        with open('./temp/working.yaml', 'w') as file:
            file = yaml.dump(config, file)

        # return all variables
        return (
            http_port, api_port, threads, source, timeout, outfile, proxyconfig,
            apiurl, testurl, testurl1, download_test_enable, download_test_url,
            download_test_timeout, download_speed_threshold, download_speed_threads,
            config, download_results
        )

def clean(clash):
    shutil.rmtree('./temp')
    clash.terminate()
    exit(0)

def download_speed_test(proxy, download_test_url, download_timeout):
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
        response = requests.get(download_test_url, proxies=proxy, timeout=download_timeout)
        speed_in_bytes = len(response.content)
        speed_in_mb = speed_in_bytes / (1024 * 1024)
        return speed_in_mb
    except Exception as e:
        print(f"下载速度测试失败（代理：{proxy['name']}）: {str(e)}")
        return None
