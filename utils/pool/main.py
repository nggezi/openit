import time
import yaml
import requests
import base64
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            working = yaml.safe_load(reader)
        data_out = []
        for x in working['proxies']:
            data_out.append(x)
        proxy_list.append(data_out)
    except:
        print(file + ": No such file")

def url(proxy_list, link):
    try:
        working = yaml.safe_load(requests.get(url=link, timeout=240, headers=headers).text)
        data_out = []
        for x in working['proxies']:
            data_out.append(x)
        proxy_list.append(data_out)
    except:
        print("Error in Collecting " + link)

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    working = yaml.safe_load(requests.get(url=baseurl + current_date + '/' + filename, timeout=240).text)
    data_out = []
    for x in working['proxies']:
        data_out.append(x)
    proxy_list.append(data_out)

def convert_non_clash(node):
    """调用subconverter模块处理非Clash节点"""
    with open('./utils/subconverter/input.txt', 'w') as f:
        f.write(node)
    
    os.system('base64 ./utils/subconverter/input.txt > ./utils/subconverter/b64 -w 0')
    os.system('./utils/subconverter/subconverter -g --artifact "push"')
    with open('./utils/subconverter/output.txt', 'r') as f:
        converted_nodes = f.read()
    
    return converted_nodes

def is_base64_encoded(s):
    try:
        return base64.b64encode(base64.b64decode(s)).decode() == s
    except Exception:
        return False

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
            filenames = list()
            filenames = data[current_date]
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

            # 处理非Clash节点
            new_proxy_list = []
            for node in proxy_list:
                if node and not isinstance(node[0], dict):  # 如果不是字典，认为是非Clash节点
                    # 先判断是否为 Base64 编码
                    if is_base64_encoded(node[0]):
                        new_proxy_list.append(yaml.safe_load(node[0]))  # 直接追加到 Clash 节点
                    else:
                        converted_nodes = convert_non_clash(node[0])
                        new_proxy_list.append(yaml.safe_load(converted_nodes))  # 将转换后的节点加载到proxy_list
                else:
                    new_proxy_list.append(node)  # 如果是字典则直接添加

            proxy_list = new_proxy_list  # 更新代理列表

            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end-start) + " seconds")
        except:
            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end-start) + " seconds")

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
