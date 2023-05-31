import time
import subprocess
from multiprocessing import Process, Manager, Semaphore
from check import check
from tqdm import tqdm
from init import init, clean
from clash import push, checkenv, checkuse
from speedtest import download_speed_test

if __name__ == '__main__':
    with Manager() as manager:
        alive = manager.list()
        # 初始化配置
        http_port, api_port, threads, source, timeout, outfile, proxyconfig, apiurl, testurl, testurl1, download_test_enable, download_test_url, download_test_timeout, download_speed_threshold, download_speed_threads, config = init()
        clashname, operating_system = checkenv()
        checkuse(clashname[2::], operating_system)
        # 启动 Clash 进程
        clash = subprocess.Popen([clashname, '-f', './temp/working.yaml', '-d', '.'])
        processes = []
        sema = Semaphore(threads)
        sema1 = Semaphore(download_speed_threads)  # 新增的信号量对象
        time.sleep(5)  # 等待 Clash 进程启动

        # 第一轮测试，使用 testurl
        for i in tqdm(range(len(config['proxies'])), desc="Testing Round 1"):
            sema.acquire()
            p = Process(target=check, args=(alive, config['proxies'][i], apiurl, sema, timeout, testurl))
            p.start()
            processes.append(p)
        for p in processes:
            p.join()

        # 如果存在第二轮测试的 testurl1，进行第二轮测试
        if testurl1 and testurl1.strip():
            processes = []
            second_round_alive = manager.list()

            # 第二轮测试，使用 testurl1，基于第一轮测试的活跃代理
            for proxy in tqdm(alive, desc="Testing Round 2"):
                sema.acquire()
                p = Process(target=check, args=(second_round_alive, proxy, apiurl, sema, timeout, testurl1))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            # 将第二轮测试的结果作为最终结果
            alive = list(second_round_alive)
            print("第二次测试结果数量:", len(alive))
        else:
            # 没有第二轮测试时，将第一轮测试的结果作为最终结果
            alive = list(alive)
            print("只进行了第一次测试，结果数量:", len(alive))

        # 执行下载测速测试（仅在 download_test_enable 为 True 且 download_test_url 存在时进行）
        if download_test_enable and download_test_url:
            download_results = manager.list()  # 创建共享的下载结果列表
            processes = []

            # 下载测速测试，基于第一轮或第二轮测试的活跃代理
            for proxy in tqdm(alive, desc="Download Speed Test"):
                sema1.acquire()  # 使用新的信号量对象 sema1
                p = Process(target=download_speed_test, args=(download_results, proxy, download_test_url, download_test_timeout, sema1))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            # 将下载速度测试的结果作为最终结果
            download_alive = [proxy for proxy in download_results if 'download_speed' in proxy and proxy['download_speed'] is not None and proxy['download_speed'] >= download_speed_threshold]
            alive = list(download_alive)

        # 将测试结果写入文件
        push(alive, outfile)
        # 清理进程和临时文件
        clean(clash)
