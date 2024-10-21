import time
import yaml
import requests
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader
import base64
import re

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def parse_node(node):
    """解析节点，检测是否为Base64格式，如果是则解码"""
    node = node.strip()
    if not node:
        return None
    # 检查Base64格式（简单检测，如果包含无效字符则认为不是Base64）
    if re.match(r'^[A-Za-z0-9+/=]+$', node):
        try:
            decoded_node = base64.b64decode(node).decode('utf-8')
            return yaml.safe_load(decoded_node)  # 尝试解析成YAML
        except Exception:
            pass
    # 如果不是Base64或者解码失败，直接尝试解析原始格式
    try:
        return yaml.safe_load(node)
    except Exception:
        return None

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            content = reader.read()
        parsed_data = parse_node(content)
        if parsed_data and 'proxies' in parsed_data:
            data_out = [x for x in parsed_data['proxies']]
            proxy_list.append(data_out)
        else:
            print(f"{file}: Invalid or empty content")
    except Exception as e:
        print(f"{file}: No such file. Error: {e}")

def url(proxy_list, link):
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        response.raise_for_status()
        content = response.text
        parsed_data = parse_node(content)
        if parsed_data and 'proxies' in parsed_data:
            data_out = [x for x in parsed_data['proxies']]
            proxy_list.append(data_out)
        else:
            print(f"Error in Collecting {link}: Invalid or empty content")
    except Exception as e:
        print(f"Error in Collecting {link}: {e}")

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        response.raise_for_status()
        content = response.text
        parsed_data = parse_node(content)
        if parsed_data and 'proxies' in parsed_data:
            data_out = [x for x in parsed_data['proxies']]
            proxy_list.append(data_out)
        else:
            print(f"Error fetching {filename}: Invalid or empty content")
    except Exception as e:
        print(f"Error fetching {filename}: {e}")

proxy_list = []
if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time()  # time start
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
            filenames = data[current_date]
        except KeyError:
            print(f"Success: find {sfiles} Clash link")
        else:
            print(f"Success: find {tfiles} Clash link")

        processes = []

        try:  # 多线程处理
            for i in subscribe_files:
                p = Process(target=local, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            processes.clear()  # 清空进程列表

            for i in subscribe_links:
                p = Process(target=url, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            processes.clear()  # 清空进程列表

            for i in filenames:
                p = Process(target=fetch, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            end = time.time()  # time end
            print(f"Collecting in {end - start:.2f} seconds")
        except Exception as e:
            end = time.time()  # time end
            print(f"Collecting in {end - start:.2f} seconds. Error: {e}")

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
    """
    for i in tqdm(range(int(tfiles)), desc="Download"):
        proxy_list.append(get_proxies(current_date, data[current_date][i]))
    """
