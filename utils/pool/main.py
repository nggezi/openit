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
    """检查内容是否是Base64编码"""
    try:
        if base64.b64encode(base64.b64decode(content)).decode() == content:
            return True
    except Exception:
        pass
    return False

def parse_content(content):
    """解析YAML格式的内容，并返回代理列表"""
    try:
        # 尝试将内容加载为YAML
        working = yaml.safe_load(content)
        if 'proxies' in working:
            return working['proxies']
    except yaml.YAMLError:
        print("不是有效的YAML格式，跳过解析")
    return []

def process_content(proxy_list, content, source_name, stats):
    """处理节点内容：如果是Base64编码，则解码后解析；否则直接解析"""
    if is_base64(content):
        try:
            # Base64解码
            decoded_content = base64.b64decode(content).decode('utf-8')
            print(f"{source_name}: Base64解码成功")
            proxies = parse_content(decoded_content)
        except Exception as e:
            print(f"{source_name}: Base64解码失败 - {e}")
            proxies = parse_content(content)  # 尝试直接解析原始内容
    else:
        # 直接解析原始内容
        proxies = parse_content(content)

    # 如果有代理，添加到列表并更新统计
    if proxies:
        proxy_list.append(proxies)
        count = len(proxies)
        print(f"{source_name}: 成功添加 {count} 个代理到列表")
        stats[source_name] = count
    else:
        print(f"{source_name}: 未找到有效的代理")
        stats[source_name] = 0

def local(proxy_list, file, stats):
    """读取本地文件并添加代理到列表"""
    try:
        with open(file, 'r') as reader:
            content = reader.read()
        process_content(proxy_list, content, file, stats)
    except FileNotFoundError:
        print(f"{file}: 无法找到文件")

def url(proxy_list, link, stats):
    """从URL读取内容并添加代理到列表"""
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        content = response.text
        process_content(proxy_list, content, link, stats)
    except Exception as e:
        print(f"{link}: 处理失败 - {e}")

def fetch(proxy_list, filename, stats):
    """从GitHub源获取代理"""
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        content = response.text
        process_content(proxy_list, content, filename, stats)
    except Exception as e:
        print(f"{filename}: 处理失败 - {e}")

if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        stats = manager.dict()  # 用于存储每种节点源的代理数量统计
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time()  # 记录开始时间
        config = 'config.yaml'
        
        with open(config, 'r') as reader:
            config = yaml.load(reader, Loader=SafeLoader)
            subscribe_links = config['sub']
            subscribe_files = config['local']

        directories, total = get_file_list()
        data = parse(directories)
        sfiles = len(subscribe_links)
        try:
            tfiles = sfiles + len(data[current_date])
            filenames = data[current_date]
        except KeyError:
            tfiles = sfiles
            filenames = []

        print(f"Success: 找到 {tfiles} Clash 链接")

        processes = []

        try:
            # 处理本地文件
            for i in subscribe_files:
                p = Process(target=local, args=(proxy_list, i, stats))
                p.start()
                processes.append(p)
            # 处理URL订阅
            for i in subscribe_links:
                p = Process(target=url, args=(proxy_list, i, stats))
                p.start()
                processes.append(p)
            # 处理远程文件
            for i in filenames:
                p = Process(target=fetch, args=(proxy_list, i, stats))
                p.start()
                processes.append(p)

            # 等待所有子进程完成
            for p in processes:
                p.join()

            end = time.time()  # 记录结束时间
            print(f"收集完成，用时 {end - start:.2f} 秒")

            # 输出每个节点源的代理数量统计
            for source, count in stats.items():
                print(f"{source}：共收集到 {count} 个代理")

            proxy_list = list(proxy_list)
            proxies = makeclash(proxy_list)
            push(proxies)
        except Exception as e:
            end = time.time()
            print(f"收集过程出现异常，用时 {end - start:.2f} 秒 - 错误: {e}")
