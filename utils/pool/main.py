import base64
import time
import yaml
import requests
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def is_base64_encoded(data):
    try:
        # 尝试解码Base64
        base64.b64decode(data)
        return True
    except Exception:
        return False

def process_node_data(proxy_list, content):
    try:
        # 尝试将内容作为Clash配置加载
        working = yaml.safe_load(content)
        if 'proxies' in working:
            # 如果是Clash配置，添加proxies到列表
            data_out = [x for x in working['proxies']]
            proxy_list.append(data_out)
        else:
            # 如果不是Clash格式，则将其视为节点URL列表
            node_list = content.strip().splitlines()
            proxy_list.append(node_list)
    except yaml.YAMLError:
        print("处理节点数据时出错")

def process_url(proxy_list, link):
    try:
        # 从URL获取内容
        response = requests.get(url=link, timeout=240, headers=headers)
        content = response.text

        # 检查内容是否是Base64编码
        if is_base64_encoded(content):
            content = base64.b64decode(content).decode('utf-8')
        
        # 处理节点数据
        process_node_data(proxy_list, content)
    except Exception as e:
        print(f"从 {link} 收集时出错: {e}")

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        content = response.text

        # 处理节点数据
        process_node_data(proxy_list, content)
    except Exception as e:
        print(f"获取 {filename} 时出错: {e}")

proxy_list = []

if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time()
        config_file = 'config.yaml'

        with open(config_file, 'r') as reader:
            config = yaml.load(reader, Loader=SafeLoader)
            subscribe_links = config.get('sub', [])
            subscribe_files = config.get('local', [])

        directories, total = get_file_list()
        data = parse(directories)

        try:
            sfiles = len(subscribe_links)
            tfiles = len(subscribe_links) + len(data.get(current_date, []))
            filenames = data.get(current_date, [])
        except KeyError:
            print("Success: " + "找到 " + str(sfiles) + " Clash 链接")
        else:
            print("Success: " + "找到 " + str(tfiles) + " Clash 链接")

        processes = []

        try:
            # 并行处理每个文件和URL
            for i in subscribe_files:
                p = Process(target=local, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for i in subscribe_links:
                p = Process(target=process_url, args=(proxy_list, i))
                p.start()
                processes.append(p)
            for i in filenames:
                p = Process(target=fetch, args=(proxy_list, i))
                p.start()
                processes.append(p)

            # 等待所有进程完成
            for p in processes:
                p.join()

            end = time.time()
            print("收集完成，用时 " + "{:.2f}".format(end - start) + " 秒")

        except Exception as e:
            end = time.time()
            print(f"收集失败，用时 {end - start:.2f} 秒: {e}")

        # 将proxy_list转换为普通列表
        proxy_list = list(proxy_list)
        # 生成Clash配置
        proxies = makeclash(proxy_list)
        # 推送到Clash
        push(proxies)
