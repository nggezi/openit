"""
这段 `main.py` 的代码的主要作用是进行代理测试和筛选，包括启动 Clash 进程、执行第一轮测试、执行第二轮测试（如果适用）、将测试结果写入文件，并进行一些清理操作。

代码的主要流程如下：
1. 初始化配置和环境设置
2. 启动 Clash 进程
3. 第一轮测试：使用 testurl 进行代理测试
4. 根据第一轮测试结果进行筛选
5. 如果存在第二轮测试的 testurl1，执行第二轮测试
6. 将第二轮测试结果作为最终结果
7. 将测试结果写入文件
8. 清理进程和临时文件

注意事项：
- 代码使用了多进程进行并发测试，提高测试效率
- 使用了进度条库 tqdm，用于显示测试进度

如果有第二轮测试，第二轮测试是在第一轮测试的结果之上进行的。
在第一轮测试完成后，将活跃代理列表 alive 的内容作为第二轮测试的初始数据。
第二轮测试将使用 testurl1 进行测试，并将第二轮测试的结果作为最终结果。
所以最后的结果是第二轮测试的最终结果，即第二轮测试中的活跃代理列表 alive。
如果没有第二轮测试或者 testurl1 为空，则最终结果就是第一轮测试的结果，即第一轮测试中的活跃代理列表 alive。
"""

import time
import subprocess
from multiprocessing import Process, Manager, Semaphore
from check import check
from tqdm import tqdm
from init import init, clean
from clash import push, checkenv, checkuse

if __name__ == '__main__':
    with Manager() as manager:
        alive = manager.list()
        # 初始化配置
        http_port, api_port, threads, source, timeout, outfile, proxyconfig, apiurl, testurl, testurl1, config = init()
        clashname, operating_system = checkenv()
        checkuse(clashname[2::], operating_system)
        # 启动 Clash 进程
        clash = subprocess.Popen([clashname, '-f', './temp/working.yaml', '-d', '.'])
        processes = []
        sema = Semaphore(threads)
        time.sleep(5)  # 等待 Clash 进程启动

        # 第一轮测试，使用 testurl
        for i in tqdm(range(len(config['proxies'])), desc="Testing Round 1"):
            sema.acquire()
            p = Process(target=check, args=(alive, config['proxies'][i], apiurl, sema, timeout, testurl))
            p.start()
            processes.append(p)
        for p in processes:
            p.join

        # 将第一轮测试的结果作为最终结果
        alive = list(alive)
        
        # 如果存在第二轮测试的 testurl1，进行第二轮测试
        if testurl1 and testurl1.strip():
            processes = []
            second_round_alive = manager.list()

            # 第二轮测试，使用 testurl1，基于第一轮测试的活跃代理
            for proxy in tqdm(alive, desc="Testing Round 2"):
                sema.acquire()
                p = Process(target=check, args=(second_round_alive, config['proxies'][i], apiurl, sema, timeout, testurl1))
                p.start()
                processes.append(p)
            for p in processes:
                p.join
                
            # 将第二轮测试的结果作为最终结果
            alive = list(second_round_alive)
            print("第二次测试结果数量:", len(alive))
        else:
            # 没有第二轮测试时，将第一轮测试的结果作为最终结果
            alive = list(alive)
            print("只进行了第一次测试，结果数量:", len(alive))
        

        # 将测试结果写入文件
        push(alive, outfile)
        # 清理进程和临时文件
        clean(clash)
