import time
import yaml
import requests
import os
import subprocess
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

def convert_to_clash_proxy(temp_file):
    try:
        # Base64 encode the temporary file
        base64_file = f'./utils/subconverter/push2'
        subprocess.run(['base64', temp_file, '-w', '0'], stdout=open(base64_file, 'wb'))

        # Call the subconverter to convert to Clash format
        subprocess.run(['./utils/subconverter/subconverter', '-g', '--artifact', 'push'])

        # Read the converted output
        output_file = './utils/subconverter/output.yaml'
        with open(output_file, 'r') as reader:
            clash_proxies = yaml.safe_load(reader)

        # Append converted proxies to the proxy list
        return clash_proxies['proxies']

    except Exception as e:
        print(f"Error converting proxies from {temp_file}: {e}")
        return []

def remove_temp_file(temp_file):
    try:
        os.remove(temp_file)
        print(f"Removed temporary file: {temp_file}")
    except Exception as e:
        print(f"Error removing file {temp_file}: {e}")

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

            # Convert non-Clash nodes
            temp_files = ['./path/to/your/non_clash_file.yaml']  # Replace with your list of temp files
            for temp_file in temp_files:
                clash_proxies = convert_to_clash_proxy(temp_file)
                if clash_proxies:
                    proxy_list.append(clash_proxies)
                remove_temp_file(temp_file)

            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds")
        except:
            end = time.time()  # time end
            print("Collecting in " + "{:.2f}".format(end - start) + " seconds")

        proxy_list = list(proxy_list)
        proxies = makeclash(proxy_list)
        push(proxies)
