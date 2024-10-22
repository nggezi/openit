import time
import yaml
import requests
from yaml.loader import SafeLoader

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip', 'Connection': 'Keep-Alive', 'User-Agent': 'Clash'}

def parse_content(content):
    """解析YAML格式的内容，并返回代理列表"""
    try:
        working = yaml.safe_load(content)
        if 'proxies' in working:
            return working['proxies']
    except yaml.YAMLError:
        print("不是有效的YAML格式，跳过解析")
    return []

def check_source(source):
    """检查节点源并返回有效的代理列表"""
    try:
        response = requests.get(url=source, timeout=10, headers=headers)
        response.raise_for_status()  # 如果响应码不是200，将抛出异常
        content = response.text
        proxies = parse_content(content)
        if proxies:
            print(f"{source} ：找到 {len(proxies)} 个有效代理")
            return True, proxies
        else:
            print(f"{source} ：未找到有效的代理")
    except Exception as e:
        print(f"{source} ：无法访问 - {e}")
    return False, []

if __name__ == '__main__':
    start = time.time()
    config = 'config.yaml'

    with open(config, 'r') as reader:
        config = yaml.load(reader, Loader=SafeLoader)
        subscribe_links = config['sub']
        subscribe_files = config['local']

    all_proxies = []
    valid_links = []
    invalid_links = []
    
    # 检查订阅文件
    for file in subscribe_files:
        try:
            with open(file, 'r') as reader:
                content = reader.read()
                proxies = parse_content(content)
                if proxies:
                    print(f"{file} ：找到 {len(proxies)} 个有效代理")
                    all_proxies.extend(proxies)
                    valid_links.append(file)  # 添加到有效链接列表
                else:
                    print(f"{file} ：未找到有效的代理")
                    invalid_links.append(file)  # 添加到无效链接列表
        except FileNotFoundError:
            print(f"{file} ：无法找到文件")
            invalid_links.append(file)  # 添加到无效链接列表

    # 检查订阅链接
    for link in subscribe_links:
        is_valid, proxies = check_source(link)
        if is_valid:
            all_proxies.extend(proxies)
            valid_links.append(link)  # 添加到有效链接列表
        else:
            invalid_links.append(link)  # 添加到无效链接列表

    end = time.time()
    print(f"检测完成，用时 {end - start:.2f} 秒")
    print(f"总共找到 {len(all_proxies)} 个有效代理")

    # 输出有效和无效链接
    print("\n有效链接:")
    for valid in valid_links:
        print(valid)

    print("\n无效链接:")
    for invalid in invalid_links:
        print(invalid)
