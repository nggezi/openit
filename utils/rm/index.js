const fs = require('fs');
const location = require('./location');
const config = require('./config');

// 默认输入路径
let urls = fs.readFileSync('./url', 'utf8');
let flags = JSON.parse(fs.readFileSync('./flags.json', 'utf8'));

// 初始化变量
let urlList = urls.split('\n');
let resList = [];
let stringList = [];
let finalList = [];
let finalURLs = [];
let countryList = ['UN']; // 将'unknown'改为'UN'
let emojiList = ['🏳']; // 默认的旗帜
let countryCount = { UN: 0 };
let urlCountryList = { UN: [] };

// 深度检测函数
async function deepDetectCountry(address) {
    let country = await location.get(address);
    if (!country || country === 'unknown') {
        // 如果 location.get 无法识别国家，则尝试使用备用逻辑
        if (address.match(/^\d+\.\d+\.\d+\.\d+$/)) {
            // 简单的 IP 地址检测逻辑，可以扩展为调用外部 IP 数据库服务
            // 例如，通过判断 IP 的区域划分来推测国家
            country = 'UN'; // 未识别的情况下使用 'UN' 作为默认值
        } else {
            // 其它情况仍使用默认值
            country = 'UN';
        }
    }
    return country;
}

async function run() {
    // 处理flags
    for (let i = 0; i < flags.length; i++) {
        countryList.push(flags[i].code);
        emojiList.push(flags[i].emoji);
        countryCount[flags[i].code] = 0;
        urlCountryList[flags[i].code] = [];
    }

    // 解析URL
    for (let i = 0; i < urlList.length; i++) {
        let url = urlList[i];
        switch (url.split('://')[0]) {
            case 'vmess':
                let vmessJSON = JSON.parse(Buffer.from(url.split('://')[1], 'base64').toString('utf-8'));
                vmessJSON.ps = null;
                resList.push({ type: 'vmess', data: vmessJSON, address: vmessJSON.add });
                break;
            case 'trojan':
                let trojanData = url.split('://')[1].split('#')[0];
                let trojanAddress = trojanData.split('@')[1].split('?')[0].split(':')[0];
                resList.push({ type: 'trojan', data: trojanData, address: trojanAddress });
                break;
            case 'ss':
                let ssData = url.split('://')[1].split('#')[0];
                let ssAddress = ssData.split('@')[1].split('#')[0].split(':')[0];
                resList.push({ type: 'ss', data: ssData, address: ssAddress });
                break;
            case 'ssr':
                let ssrData = Buffer.from(url.split('://')[1], 'base64').toString('utf-8');
                let ssrAddress = ssrData.split(':')[0];
                resList.push({ type: 'ssr', data: ssrData.replace(/remarks=.*?(?=&)/, "remarks={name}&"), address: ssrAddress });
                break;
            case 'https':
                let httpsData = url.split('://')[1].split('#')[0];
                let httpsAddress = Buffer.from(httpsData.split('?')[0], "base64").toString('utf8').split('@')[1].split(':')[0];
                resList.push({ type: 'https', data: httpsData, address: httpsAddress });
                break;
            default:
                console.log('未知协议类型: ' + url.split('://')[0]);
                break;
        }
    }

    // 去重并处理国家信息
    for (let i = 0; i < resList.length; i++) {
        stringList.push(JSON.stringify(resList[i]));
    }
    let afterList = Array.from(new Set(stringList));
    for (let i = 0; i < afterList.length; i++) {
        finalList.push(JSON.parse(afterList[i]));
    }

    // 深度检测国家
    for (let i = 0; i < finalList.length; i++) {
        finalList[i].country = await deepDetectCountry(finalList[i].address);
    }

    // 生成链接
    for (let i = 0; i < finalList.length; i++) {
        let item = finalList[i];
        countryCount[finalList[i].country]++;
        let name = emojiList[countryList.indexOf(finalList[i].country)] + finalList[i].country + ' ' + countryCount[finalList[i].country] + config.nodeAddName;
        switch (item.type) {
            case 'vmess':
                try {
                    item.data.ps = name;
                    urlCountryList[finalList[i].country].push('vmess://' + Buffer.from(JSON.stringify(item.data), 'utf8').toString('base64'));
                } catch (e) {
                    console.log('生成链接错误: ' + e.message + ', 类型: vmess');
                }
                break;
            case 'trojan':
                try {
                    urlCountryList[finalList[i].country].push('trojan://' + item.data + '#' + encodeURIComponent(name));
                } catch (e) {
                    console.log('生成链接错误: ' + e.message + ', 类型: trojan');
                }
                break;
            case 'ss':
                try {
                    urlCountryList[finalList[i].country].push('ss://' + item.data + '#' + encodeURIComponent(name));
                } catch (e) {
                    console.log('生成链接错误: ' + e.message + ', 类型: ss');
                }
                break;
            case 'ssr':
                try {
                    urlCountryList[finalList[i].country].push('ssr://' + Buffer.from(item.data.replace('{name}', Buffer.from(name, 'utf8').toString('base64')), 'utf8').toString('base64'));
                } catch (e) {
                    console.log('生成链接错误: ' + e.message + ', 类型: ssr');
                }
                break;
            case 'https':
                try {
                    urlCountryList[finalList[i].country].push('https://' + item.data + '#' + encodeURIComponent(name));
                } catch (e) {
                    console.log('生成链接错误: ' + e.message + ', 类型: https');
                }
                break;
            default:
                break;
        }
    }

    // 输出最终结果
    for (const i in urlCountryList) {
        if (urlCountryList[i].length > 0) {
            finalURLs.push(...urlCountryList[i]);
        }
    }
    console.log(`去重改名完成，共${urlList.length}个节点，去重后剩余${finalURLs.length}个节点`);
    fs.writeFileSync('./out', finalURLs.join('\n'));
}

run();
