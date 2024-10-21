import time
import yaml
import requests
from crawl import get_file_list, get_proxies
from parse import parse, makeclash
from clash import push
from multiprocessing import Process, Manager
from yaml.loader import SafeLoader
import base64

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def local(proxy_list, file):
    try:
        with open(file, 'r') as reader:
            working = yaml.safe_load(reader)
        data_out = []
        if 'proxies' in working:
            for x in working['proxies']:
                data_out.append(x)
            proxy_list.append(data_out)
        else:
            print(f"{file}: 没有找到 'proxies' 字段")
    except FileNotFoundError:
        print(f"{file}: 文件不存在")
    except yaml.YAMLError as e:
        print(f"{file}: 解析 YAML 文件时出错: {e}")

def url(proxy_list, link):
    try:
        response = requests.get(url=link, timeout=240, headers=headers)
        content = response.text.strip()

        # 判断是否是base64格式
        try:
            # 尝试解码base64
            decoded_content = base64.b64decode(content).decode('utf-8')
            working = yaml.safe_load(decoded_content)
        except Exception:
            # 如果解码失败，尝试直接解析
            working = yaml.safe_load(content)

        data_out = []
        if 'proxies' in working:
            for x in working['proxies']:
                data_out.append(x)
            proxy_list.append(data_out)
        else:
            print(f"{link}: 无法找到 'proxies' 字段，可能不是Clash格式")
    except requests.RequestException as e:
        print(f"请求错误: {link}, 错误信息: {e}")
    except yaml.YAMLError as e:
        print(f"{link}: 解析 YAML 文件时出错: {e}")

def fetch(proxy_list, filename):
    current_date = time.strftime("%Y_%m_%d", time.localtime())
    baseurl = 'https://raw.githubusercontent.com/changfengoss/pub/main/data/'
    try:
        response = requests.get(url=baseurl + current_date + '/' + filename, timeout=240)
        content = response.text.strip()

        # 尝试解析内容
        working = yaml.safe_load(content)

        data_out = []
        if 'proxies' in working:
            for x in working['proxies']:
                data_out.append(x)
            proxy_list.append(data_out)
        else:
            print(f"{filename}: 无法找到 'proxies' 字段，可能不是Clash格式")
    except requests.RequestException as e:
        print(f"请求错误: {filename}, 错误信息: {e}")
    except yaml.YAMLError as e:
        print(f"{filename}: 解析 YAML 文件时出错: {e}")

proxy_list=[]
if __name__ == '__main__':
    with Manager() as manager:
        proxy_list = manager.list()
        current_date = time.strftime("%Y_%m_%d", time.localtime())
        start = time.time() #time start
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
            processes=[]
            filenames = list()
            filenames = data[current_date]
        except KeyError:
            print("Success: 找到 " + str(sfiles) + " Clash 链接")
        else:
            print("Success: 找到 " + str(tfiles) + " Clash 链接")

        processes=[]

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
            print("收集完成，用时 " + "{:.2f}".format(end-start) + " 秒")
        except Exception as e:
            end = time.time() # time end
            print(f"收集失败，用时 {end-start:.2f} 秒: {e}")

        proxy_list=list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
