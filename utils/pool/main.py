import time
import yaml
import requests
import base64
import os
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def is_base64_encoded(data):
    try:
        if isinstance(data, str):
            # 尝试解码
            base64.b64decode(data)
            return True
        return False
    except Exception:
        return False

def convert_to_yaml(data):
    """转换为YAML格式"""
    return yaml.dump(data)

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            working = yaml.safe_load(reader)
        data_out = []
        for x in working['proxies']:
            data_out.append(x)
        proxy_list.append(data_out)
    except Exception as e:
        print(file + ": No such file - " + str(e))

def url(proxy_list, link):
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        working_text = response.text
        
        # 判断是否为 Base64 格式
        if is_base64_encoded(working_text):
            working = yaml.safe_load(base64.b64decode(working_text))
        else:
            # 直接将内容解析为节点
            working = yaml.safe_load(working_text)

        # 检查是否有 'proxies' 字段
        if 'proxies' not in working:
            print(f"Warning: 'proxies' field not found in {link}")
            return  # 如果没有 'proxies' 字段则返回

        # 处理非 Clash 节点
        for x in working['proxies']:
            if isinstance(x, str):  # 如果是字符串类型，认为是非 Clash 节点
                converted_nodes = convert_non_clash(x)  # 调用转换函数
                proxy_list.append(yaml.safe_load(converted_nodes))  # 将转换后的节点加载到proxy_list
            else:
                proxy_list.append(x)  # 直接追加字典类型的节点

    except Exception as e:
        print(f"Error in Collecting {link} - {str(e)}")
        print("Received data:", working_text)  # 打印接收到的数据以便调试

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        working_text = response.text
        working = yaml.safe_load(working_text)  # 直接解析为YAML格式
        
        if 'proxies' not in working:
            print(f"Warning: 'proxies' field not found in {filename}")
            return  # 如果没有 'proxies' 字段则返回
        
        # 处理非 Clash 节点
        for x in working['proxies']:
            if isinstance(x, str):  # 如果是字符串类型，认为是非 Clash 节点
                converted_nodes = convert_non_clash(x)  # 调用转换函数
                proxy_list.append(yaml.safe_load(converted_nodes))  # 将转换后的节点加载到proxy_list
            else:
                proxy_list.append(x)  # 直接追加字典类型的节点

    except Exception as e:
        print(f"Failed to fetch {filename}: {e}")

def convert_non_clash(node):
    """调用subconverter模块处理非Clash节点"""
    with open('./utils/subconverter/input.txt', 'w') as f:
        f.write(node)

    os.system('base64 ./utils/subconverter/input.txt > ./utils/subconverter/b64 -w 0')
    os.system('./utils/subconverter/subconverter -g --artifact "push"')
    
    with open('./utils/subconverter/output.txt', 'r') as f:
        converted_nodes = f.read()
    
    return converted_nodes

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
            processes = []
            filenames = list(data[current_date])
        except KeyError:
            print("Success: " + "find " + str(sfiles) + " Clash link")
        else:
            print("Success: " + "find " + str(tfiles) + " Clash link")

        processes = []

        try:  # Process开启多线程
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

            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds")
        except Exception as e:
            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds - Error: " + str(e))

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
