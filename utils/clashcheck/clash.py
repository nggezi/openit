import os
import yaml
import flag  # 用于处理国家/地区的旗帜符号
import socket  # 用于解析服务器地址
import maxminddb  # 用于通过 IP 查询国家/地区信息
import platform
import psutil
import requests
from tqdm import tqdm  # 进度条显示
from pathlib import Path  # 文件路径操作

# 将列表推送到 Clash 配置文件
def push(list, outfile):
    country_count = {}  # 国家计数器，用于命名节点
    count = 1  # 节点序号
    clash = {'proxies': [], 'proxy-groups': [
            {'name': 'automatic', 'type': 'url-test', 'proxies': [], 'url': 'https://www.google.com/favicon.ico',
             'interval': 300}, {'name': '🌐 Proxy', 'type': 'select', 'proxies': ['automatic']}],
             'rules': ['MATCH,🌐 Proxy']}

    # 打开 GeoIP 数据库，用于解析节点 IP 对应的国家
    with maxminddb.open_database('Country.mmdb') as countrify:
        for i in tqdm(range(len(list)), desc="Parse"):
            x = list[i]
            try:
                # 校验是否为 VMess 节点
                float(x['password'])
            except:
                try:
                    float(x['uuid'])
                except:
                    try:
                        # 尝试解析节点信息
                        ip = str(socket.gethostbyname(x["server"]))
                    except:
                        ip = str(x["server"])  # 若解析失败则直接使用原 server
                    try:
                        # 获取对应的国家 ISO 代码
                        country = str(countrify.get(ip)['country']['iso_code'])
                    except:
                        country = 'UN'  # 未知国家则用 UN 代替
                    flagcountry = country  # 使用国家代码作为 flag 标志
                    try:
                        # 统计国家对应的节点数量，生成节点名称
                        country_count[country] = country_count[country] + 1
                        x['name'] = str(flag.flag(flagcountry)) + " " + country + " " + str(count)
                    except:
                        country_count[country] = 1
                        x['name'] = str(flag.flag(flagcountry)) + " " + country + " " + str(count)
                    
                    # 将节点添加到 Clash 配置中
                    clash['proxies'].append(x)
                    clash['proxy-groups'][0]['proxies'].append(x['name'])
                    clash['proxy-groups'][1]['proxies'].append(x['name'])
                    count += 1

    # 写入最终配置文件
    with open(outfile, 'w') as writer:
        yaml.dump(clash, writer, sort_keys=False)


# 检查系统环境和 Clash 可执行文件
def checkenv():
    """
    检查系统的操作系统和架构，并返回相应的 Clash 可执行文件名称。
    """
    operating_system = f"{platform.system()}/{platform.machine()} with {platform.node()}"
    print('Try to run Clash on ' + operating_system)

    if operating_system.startswith('Darwin'):
        # macOS 系统
        if 'arm64' in operating_system:
            clashname = './clash-darwin-arm64'
        elif 'x86_64' in operating_system:
            clashname = './clash-darwin-amd64'
        else:
            print('System is supported (Darwin), but Architecture is not supported.')
            exit(1)
    elif operating_system.startswith('Linux'):
        # Linux 系统
        if 'x86_64' in operating_system:
            clashname = './clash-linux-amd64'
        elif 'aarch64' in operating_system:
            clashname = './clash-linux-arm64'
        else:
            print('System is supported (Linux), but Architecture is not supported.')
            exit(1)
    elif operating_system.startswith('Windows'):
        # Windows 系统
        if 'AMD64' in operating_system:
            clashname = 'clash-windows-amd64.exe'
        else:
            print('System is supported (Windows), but Architecture is not supported.')
            exit(1)
    else:
        print('System is not supported.')
        exit(1)

    return clashname, operating_system


# 检查 Clash 是否正在运行
def checkuse(clashname, operating_system):
    """
    如果 Clash 进程已存在，终止其进程。
    """
    pids = psutil.process_iter()
    for pid in pids:
        if pid.name() == clashname:
            if operating_system.startswith('Darwin') or operating_system.startswith('Linux'):
                os.kill(pid.pid, 9)
            elif operating_system.startswith('Windows'):
                os.popen(f'taskkill.exe /pid:{pid.pid}')
            else:
                print(f"{clashname}, {pid.pid} ← kill to continue")
                exit(1)

# 过滤和处理 Clash 配置文件中的代理节点
def filter(config):
    list = config["proxies"]
    # 定义支持的加密方式等
    ss_supported_ciphers = ['aes-128-gcm', 'aes-192-gcm', 'aes-256-gcm', 'aes-128-cfb', 'aes-192-cfb', 'aes-256-cfb', 'aes-128-ctr', 'aes-192-ctr', 'aes-256-ctr', 'rc4-md5', 'chacha20', 'chacha20-ietf', 'xchacha20', 'chacha20-ietf-poly1305', 'xchacha20-ietf-poly1305']
    ssr_supported_obfs = ['plain', 'http_simple', 'http_post', 'random_head', 'tls1.2_ticket_fastauth', 'tls1.2_ticket_auth']
    ssr_supported_protocol = ['origin', 'auth_sha1_v4', 'auth_aes128_md5', 'auth_aes128_sha1', 'auth_chain_a', 'auth_chain_b']
    vmess_supported_ciphers = ['auto', 'aes-128-gcm', 'chacha20-poly1305', 'none']
    iplist = {}
    passlist = []
    count = 1
    # 初始化 Clash 配置文件结构
    clash = {'proxies': [], 'proxy-groups': [
            {'name': 'automatic', 'type': 'url-test', 'proxies': [], 'url': 'https://www.google.com/favicon.ico',
             'interval': 300}, {'name': '🌐 Proxy', 'type': 'select', 'proxies': ['automatic']}],
             'rules': ['MATCH,🌐 Proxy']}
    with maxminddb.open_database('Country.mmdb') as countrify:
        for i in tqdm(range(int(len(list))), desc="Parse"):
            try:
                x = list[i]
                authentication = ''
                x['port'] = int(x['port'])
                # 统一 password 字段为字符串类型
                if 'password' in x:
                    try:
                        # 强制将 password 转为字符串类型
                        x['password'] = str(x['password'])
                    except Exception as e:
                        print(f"Error processing password for node {x['name']}: {e}")
                        x['password'] = ''  # 如果处理失败，设置为空字符串或跳过该节点
                else:
                    x['password'] = ''  # 如果字段缺失，设置默认值
                try:
                    ip = str(socket.gethostbyname(x["server"]))
                except:
                    ip = x['server']
                try:
                    country = str(countrify.get(ip)['country']['iso_code'])
                except:
                    country = 'UN'

                # 节点类型校验逻辑
                if x['type'] in ['grpc', 'h2']:
                    # 确保 TLS 开启
                    if 'tls' not in x or not x['tls']:
                        x['tls'] = True
                    x['name'] = f"{str(flag.flag(country))} {country} {count} {x['type'].upper()}"
                    authentication = 'password'
                
                elif x['type'] == 'ss':
                    try:
                        if x['cipher'] not in ss_supported_ciphers:
                            continue
                        if ip in iplist:
                            continue
                        else:
                            iplist[ip] = []
                            iplist[ip].append(x['port'])
                        x['name'] = f"{str(flag.flag(country))} {country} {count} SSS"
                        authentication = 'password'
                    except:
                        continue
                
                elif x['type'] == 'ssr':
                    try:
                        if x['cipher'] not in ss_supported_ciphers:
                            continue
                        if x['obfs'] not in ssr_supported_obfs:
                            continue
                        if x['protocol'] not in ssr_supported_protocol:
                            continue
                        if ip in iplist:
                            continue
                        else:
                            iplist[ip] = []
                            iplist[ip].append(x['port'])
                        authentication = 'password'
                        x['name'] = f"{str(flag.flag(country))} {country} {count} SSR"
                    except:
                        continue
                
                elif x['type'] == 'vmess':
                    try:
                        if 'udp' in x and x['udp'] not in [False, True]:
                            continue
                        if 'tls' in x and x['tls'] not in [False, True]:
                            continue
                        if 'skip-cert-verify' in x and x['skip-cert-verify'] not in [False, True]:
                            continue
                        if x['cipher'] not in vmess_supported_ciphers:
                            continue
                        x['name'] = f"{str(flag.flag(country))} {country} {count} VMS"
                        authentication = 'uuid'
                    except:
                        continue
                
                elif x['type'] == 'trojan':
                    try:
                        # 校验配置项 'udp' 是否符合布尔值
                        if 'udp' in x:
                            if x['udp'] not in [False, True]:
                                continue
                        # 校验配置项 'skip-cert-verify' 是否符合布尔值
                        if 'skip-cert-verify' in x:
                            if x['skip-cert-verify'] not in [False, True]:
                                continue
                        # 设置节点名称，格式为 "国家旗帜 ISO码 序号 类型标识"
                        x['name'] = str(flag.flag(country)) + ' ' + str(country) + ' ' + str(count) + ' ' + 'TJN'
                        authentication = 'password'  # 使用密码作为认证字段
                    except:
                        continue
                
                elif x['type'] == 'snell':
                    try:
                        # 校验配置项 'udp' 是否符合布尔值
                        if 'udp' in x:
                            if x['udp'] not in [False, True]:
                                continue
                        # 校验配置项 'skip-cert-verify' 是否符合布尔值
                        if 'skip-cert-verify' in x:
                            if x['skip-cert-verify'] not in [False, True]:
                                continue
                        # 设置节点名称，格式为 "国家旗帜 ISO码 序号 类型标识"
                        x['name'] = str(flag.flag(country)) + ' ' + str(country) + ' ' + str(count) + ' ' + 'SNL'
                        authentication = 'psk'  # 使用预共享密钥 (PSK) 作为认证字段
                    except:
                        continue
                
                elif x['type'] == 'http':
                    try:
                        # 校验配置项 'tls' 是否符合布尔值
                        if 'tls' in x:
                            if x['tls'] not in [False, True]:
                                continue
                        # 设置节点名称，格式为 "国家旗帜 ISO码 序号 类型标识"
                        x['name'] = str(flag.flag(country)) + ' ' + str(country) + ' ' + str(count) + ' ' + 'HTT'
                        # HTTP 类型暂时不需要认证字段
                        # authentication = 'userpass'
                    except:
                        continue
                
                elif x['type'] == 'socks5':
                    try:
                        # 校验配置项 'tls' 是否符合布尔值
                        if 'tls' in x:
                            if x['tls'] not in [False, True]:
                                continue
                        # 校验配置项 'udp' 是否符合布尔值
                        if 'udp' in x:
                            if x['udp'] not in [False, True]:
                                continue
                        # 校验配置项 'skip-cert-verify' 是否符合布尔值
                        if 'skip-cert-verify' in x:
                            if x['skip-cert-verify'] not in [False, True]:
                                continue
                        # 设置节点名称，格式为 "国家旗帜 ISO码 序号 类型标识"
                        x['name'] = str(flag.flag(country)) + ' ' + str(country) + ' ' + str(count) + ' ' + 'SK5'
                        # SOCKS5 类型暂时不需要认证字段
                        # authentication = 'userpass'
                    except:
                        continue
                
                else:
                    # 如果节点类型不符合预期，跳过处理
                    continue

                # 避免重复节点
                if ip in iplist and x['port'] in iplist[ip]:
                    if x[authentication] in passlist:
                        continue
                    else:
                        passlist.append(x[authentication])
                else:
                    try:
                        iplist[ip].append(x['port'])
                    except:
                        iplist[ip] = []
                        iplist[ip].append(x['port'])

                clash['proxies'].append(x)
                clash['proxy-groups'][0]['proxies'].append(x['name'])
                clash['proxy-groups'][1]['proxies'].append(x['name'])
                count += 1

            except:
                #print('shitwentwrong' + str(x))
                continue

    return clash
