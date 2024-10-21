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
    """检查字符串是否是Base64编码"""
    try:
        if base64.b64encode(base64.b64decode(content)).decode() == content:
            return True
    except Exception:
        pass
    return False

def parse_content(content):
    """解析内容并转换为Clash配置格式"""
    # 如果是Base64编码，先解码
    if is_base64(content):
        content = base64.b64decode(content).decode('utf-8')
        print("Base64解码成功")

    lines = content.strip().splitlines()
    proxies = []

    for line in lines:
        line = line.strip()
        if line.startswith("ss://"):
            # 处理Shadowsocks节点
            proxy = convert_to_clash_proxy(line, "ss")
            proxies.append(proxy)
        elif line.startswith("vmess://"):
            # 处理Vmess节点
            proxy = convert_to_clash_proxy(line, "vmess")
            proxies.append(proxy)
        elif line.startswith("trojan://"):
            # 处理Trojan节点
            proxy = convert_to_clash_proxy(line, "trojan")
            proxies.append(proxy)
        elif line.startswith("hy2://"):
            # 处理Hysteria2节点
            proxy = convert_to_clash_proxy(line, "hy2")
            proxies.append(proxy)
        else:
            # 如果是Clash格式的配置，直接添加
            try:
                yaml_content = yaml.safe_load(line)
                if 'proxies' in yaml_content:
                    proxies.extend(yaml_content['proxies'])
            except yaml.YAMLError:
                print("不是有效的Clash格式配置，跳过")

    return proxies

def convert_to_clash_proxy(node, node_type):
    """将不同格式的节点转换为Clash代理格式"""
    if node_type == "ss":
        # 示例SS节点解析和转换
        return {
            "name": "SS代理",
            "type": "ss",
            "server": "...",
            "port": "...",
            "cipher": "...",
            "password": "...",
            "plugin": "",
            "plugin-opts": {}
        }
    elif node_type == "vmess":
        # 示例Vmess节点解析和转换
        return {
            "name": "Vmess代理",
            "type": "vmess",
            "server": "...",
            "port": "...",
            "uuid": "...",
            "alterId": "0",
            "cipher": "auto",
            "tls": False
        }
    elif node_type == "trojan":
        # 示例Trojan节点解析和转换
        return {
            "name": "Trojan代理",
            "type": "trojan",
            "server": "...",
            "port": "...",
            "password": "...",
            "sni": ""
        }
    elif node_type == "hy2":
        # 示例Hysteria2节点解析和转换
        return {
            "name": "Hy2代理",
            "type": "hysteria",
            "server": "...",
            "port": "...",
            "auth_str": "...",
            "protocol": "udp",
            "up_mbps": 10,
            "down_mbps": 50,
            "sni": ""
        }
    else:
        # 未知类型，直接返回原数据
        return node

def local(proxy_list, file):
    """读取本地文件并添加代理到列表"""
    try:
        with open(file, 'r') as reader:
            content = reader.read()
        proxies = parse_content(content)
        proxy_list.append(proxies)
        print(f"{file}: 成功添加代理到列表")
    except:
        print(f"{file}: 无法找到文件或处理失败")

def url(proxy_list, link):
    """从URL读取内容并添加代理到列表"""
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        proxies = parse_content(response.text)
        proxy_list.append(proxies)
        print(f"{link}: 成功添加代理到列表")
    except:
        print(f"{link}: 处理失败")

def fetch(proxy_list, filename):
    """从GitHub源获取代理"""
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        proxies = parse_content(response.text)
        proxy_list.append(proxies)
        print(f"{filename}: 成功添加代理到列表")
    except:
        print(f"{filename}: 处理失败")

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

        processes = []

        # 处理本地文件
        for i in subscribe_files:
            p = Process(target=local, args=(proxy_list, i))
            p.start()
            processes.append(p)
        # 处理URL订阅
        for i in subscribe_links:
            p = Process(target=url, args=(proxy_list, i))
            p.start()
            processes.append(p)
        # 处理远程文件
        for i in data.get(current_date, []):
            p = Process(target=fetch, args=(proxy_list, i))
            p.start()
            processes.append(p)
        # 等待所有子进程完成
        for p in processes:
            p.join()

        end = time.time()
        print(f"收集完成，用时 {end - start:.2f} 秒")

        # 转换代理列表为Clash格式并推送
        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
