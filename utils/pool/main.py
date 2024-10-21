import time
import yaml
import base64
import requests
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def is_base64_encoded(data):
    try:
        base64.b64decode(data, validate=True)
        return True
    except Exception:
        return False

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            content = reader.read()
            process_content(proxy_list, content)
    except Exception as e:
        print(file + ": Error occurred -", e)

def url(proxy_list, link):
    try:
        content = requests.get(url=link, timeout=240, headers=headers).text
        process_content(proxy_list, content)
    except Exception as e:
        print("Error in Collecting " + link + " -", e)

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        content = requests.get(url=baseurl + current_date + '/' + filename, timeout=240, headers=headers).text
        process_content(proxy_list, content)
    except Exception as e:
        print("Error in fetching " + filename + " -", e)

def process_content(proxy_list, content):
    # 判断是否是Base64格式
    if is_base64_encoded(content):
        # 如果是Base64编码，先解码
        decoded_content = base64.b64decode(content).decode('utf-8')
        add_proxies(proxy_list, decoded_content)
    else:
        # 如果不是Base64编码，尝试将其转换为Base64格式
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        # 判断是否是直接的节点格式
        if is_base64_encoded(encoded_content):
            # 如果是直接的节点格式，直接追加
            add_proxies(proxy_list, content)
        else:
            # 不是直接的节点格式，解码并提取节点
            decoded_content = base64.b64decode(encoded_content).decode('utf-8')
            add_proxies(proxy_list, decoded_content)

def add_proxies(proxy_list, content):
    try:
        # 尝试解析为Clash格式的节点
        working = yaml.safe_load(content)
        if 'proxies' in working:
            proxy_list.append(working['proxies'])
        else:
            # 如果不是Clash格式的节点，则逐行追加
            for line in content.splitlines():
                proxy_list.append(line.strip())
    except Exception:
        # 解析失败，按普通格式逐行追加
        for line in content.splitlines():
            proxy_list.append(line.strip())

proxy_list = []
if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time()
        config = 'config.yaml'
        with open(config, 'r') as reader:
            config = yaml.load(reader, Loader=SafeLoader)
            subscribe_links = config['sub']
            subscribe_files = config['local']
        directories, total = get_file_list()
        data = parse(directories)
        try:
            sfiles = len(subscribe_links)
            tfiles = len(subscribe_links) + len(data[current_date])
            processes = []
            filenames = list()
            filenames = data[current_date]
        except KeyError:
            print("Success: " + "find " + str(sfiles) + " Clash link")
        else:
            print("Success: " + "find " + str(tfiles) + " Clash link")

        processes = []

        try:
            for i in subscribe_files:
                p = Process(target=local, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
            for i in subscribe_links:
                p = Process(target=url, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
            for i in filenames:
                p = Process(target=fetch, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
            end = time.time()
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds")
        except Exception:
            end = time.time()
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds")

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
