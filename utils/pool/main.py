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

def is_base64(content):
    """检查内容是否为Base64编码"""
    try:
        base64.b64decode(content)
        return True
    except Exception:
        return False

def convert_to_clash_format(content):
    """尝试将非Clash格式的节点转换为Clash格式"""
    data_out = []
    lines = content.strip().splitlines()
    for line in lines:
        if line.startswith("ss://"):
            # 处理 Shadowsocks 节点
            print("发现SS节点，正在转换为Clash格式")
            data_out.append({'name': 'SS Node', 'type': 'ss', 'server': 'example.com', 'port': 8388, 'cipher': 'aes-128-gcm', 'password': 'password'})
        elif line.startswith("vmess://"):
            # 处理 Vmess 节点
            print("发现Vmess节点，正在转换为Clash格式")
            data_out.append({'name': 'Vmess Node', 'type': 'vmess', 'server': 'example.com', 'port': 443, 'uuid': 'uuid_here', 'alterId': 64, 'cipher': 'auto'})
        elif line.startswith("vless://"):
            # 处理 Vless 节点
            print("发现Vless节点，正在转换为Clash格式")
            data_out.append({'name': 'Vless Node', 'type': 'vless', 'server': 'example.com', 'port': 443, 'uuid': 'uuid_here', 'encryption': 'none'})
        else:
            print(f"未知格式的节点: {line}")
        # 可以继续添加对其他节点格式的支持
    return data_out

def parse_content(content):
    """解析内容并转换为Clash格式"""
    # 检查是否是Base64编码
    if is_base64(content):
        content = base64.b64decode(content).decode('utf-8')
        print("Base64解码成功")

    # 尝试解析为Clash格式
    try:
        working = yaml.safe_load(content)
        if 'proxies' in working:
            print("成功解析为Clash格式")
            return working['proxies']
    except yaml.YAMLError:
        print("YAML解析失败，尝试转换为非Clash格式的节点")

    # 如果不是Clash格式，则尝试将其转换为Clash格式
    return convert_to_clash_format(content)

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            content = reader.read()
        proxies = parse_content(content)
        if proxies:
            proxy_list.append(proxies)
            print(f"{file}: 成功添加代理到列表")
        else:
            print(f"{file}: 无法找到有效的代理配置")
    except FileNotFoundError:
        print(f"{file}: 文件不存在")
    except Exception as e:
        print(f"{file}: 处理时出错: {e}")

def url(proxy_list, link):
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        content = response.text.strip()
        proxies = parse_content(content)
        if proxies:
            proxy_list.append(proxies)
            print(f"{link}: 成功添加代理到列表")
        else:
            print(f"{link}: 无法找到有效的代理配置")
    except requests.RequestException as e:
        print(f"请求错误: {link}, 错误信息: {e}")

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        content = response.text.strip()
        proxies = parse_content(content)
        if proxies:
            proxy_list.append(proxies)
            print(f"{filename}: 成功添加代理到列表")
        else:
            print(f"{filename}: 无法找到有效的代理配置")
    except requests.RequestException as e:
        print(f"请求错误: {filename}, 错误信息: {e}")

proxy_list=[]
if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time() # time start
        config = 'config.yaml'
        with open(config, 'r') as reader:
            config = yaml.load(reader, Loader=SafeLoader)
            subscribe_links = config['sub']
            subscribe_files = config['local']
        directories, total = get_file_list()
        data = parse(directories)
        try:
            sfiles = len(subscribe_links)
            tfiles = len(subscribe_links) + len(data.get(current_date, []))
            filenames = data.get(current_date, [])
            processes = []
        except KeyError:
            print(f"Success: 找到 {sfiles} Clash 链接")
        else:
            print(f"Success: 找到 {tfiles} Clash 链接")

        processes = []

        try: # 多线程处理
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
            end = time.time() # time end
            print(f"收集完成，用时 {end-start:.2f} 秒")
        except Exception as e:
            end = time.time() # time end
            print(f"收集失败，用时 {end-start:.2f} 秒: {e}")

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
