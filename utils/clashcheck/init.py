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
    return http_port, api_port, threads, source, timeout, outfile, proxyconfig, apiurl, testurl, testurl1, download_test_enable, download_test_url, download_test_timeout, download_speed_threshold, download_speed_threads, config

def clean(clash):
    shutil.rmtree('./temp')
    clash.terminate()
    exit(0)
