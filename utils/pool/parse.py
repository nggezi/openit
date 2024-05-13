def parse(data_in):
    dtp = []
    for x in data_in:
        dtp.append(x.replace('data/', ''))
    dtpr1 = [x for x in dtp if "/" in x]
    dtpr2 = [x for x in dtpr1 if ".yaml" in x]
    textdict = {}
    for x in dtpr2:
        # 为解决类似0pmtpm/2024_05_05/J5WT3hh.yaml目录结构导致失败的问题，这个数据包含多个 / 分隔符，导致了解包错误。为了解决这个问题，分割操作之前对数据进行进一步处理，以确保每个字符串只包含一个 / 分隔符。
        # 进一步处理数据，只保留第一个 '/' 分隔符之前的部分作为日期，剩余部分作为文件名
        parts = x.split('/', 1)  # 仅分割一次，保留第一个分隔符之前的部分
        if len(parts) != 2:
            print("Error in data:", x)  # 输出导致错误的具体数据
            raise ValueError("Input should contain exactly one '/' separator")
        
        date, filename = parts
        if date in textdict:
            textdict[date].append(filename)
        else:
            textdict[date] = [filename]

    return textdict

def makeclash(dictin):
    badprotocols = ['vless']
    proxies = []
    for x in dictin:
        for y in x:
            try:
                if y in proxies:
                    pass
                else:
                    if y['type'] in badprotocols:
                        pass
                    else:
                        proxies.append(y)
            except:
                continue
    return proxies
