const fs = require('fs');
const location = require('./location');
const config = require('./config');

// 默认输入路径'./url'
let urls = fs.readFileSync('./url', 'utf8');
let flags = JSON.parse(fs.readFileSync('./flags.json', 'utf8'));

// 默认旗帜设置
const DEFAULT_COUNTRY = 'UN';
const DEFAULT_EMOJI = '🌍';

// 初始化变量
let urlList = urls.split('\n');
let resList = [];
let stringList = [];
let finalList = [];
let finalURLs = [];
let countryList = [DEFAULT_COUNTRY];
let emojiList = [DEFAULT_EMOJI];
let countryCount = { [DEFAULT_COUNTRY]: 0 };
let urlCountryList = { [DEFAULT_COUNTRY]: [] };

// 初始化国家和旗帜数据
function initializeCountryData() {
    for (let flag of flags) {
        countryList.push(flag.code);
        emojiList.push(flag.emoji);
        countryCount[flag.code] = 0;
        urlCountryList[flag.code] = [];
    }
}

// 处理并解析 URL
function parseURLs() {
    for (let url of urlList) {
        try {
            let protocol = url.split('://')[0];
            let node = {};

            switch (protocol) {
                case 'vmess':
                    let vmessJSON = JSON.parse(Buffer.from(url.split('://')[1], 'base64').toString('utf-8'));
                    vmessJSON.ps = null;
                    node = { type: 'vmess', data: vmessJSON, address: vmessJSON.add };
                    break;
                case 'trojan':
                    let trojanData = url.split('://')[1].split('#')[0];
                    let trojanAddress = trojanData.split('@')[1].split('?')[0].split(':')[0];
                    node = { type: 'trojan', data: trojanData, address: trojanAddress };
                    break;
                case 'ss':
                    let ssData = url.split('://')[1].split('#')[0];
                    let ssAddress = ssData.split('@')[1].split('#')[0].split(':')[0];
                    node = { type: 'ss', data: ssData, address: ssAddress };
                    break;
                case 'ssr':
                    let ssrData = Buffer.from(url.split('://')[1], 'base64').toString('utf-8');
                    let ssrAddress = ssrData.split(':')[0];
                    node = { type: 'ssr', data: ssrData.replace(/remarks=.*?(?=&)/, "remarks={name}&"), address: ssrAddress };
                    break;
                case 'https':
                    let httpsData = url.split('://')[1].split('#')[0];
                    let httpsAddress = Buffer.from(httpsData.split('?')[0], "base64").toString('utf8').split('@')[1].split(':')[0];
                    node = { type: 'https', data: httpsData, address: httpsAddress };
                    break;
                default:
                    continue;
            }

            resList.push(node);
        } catch (e) {
            console.log(`${protocol} node parsing error:`, e.message);
        }
    }
}

// 去重
function deduplicate() {
    stringList = resList.map(node => JSON.stringify(node));
    let afterList = Array.from(new Set(stringList));
    finalList = afterList.map(nodeStr => JSON.parse(nodeStr));
}

// 并行处理国家信息
async function processCountries() {
    await Promise.all(finalList.map(async (item) => {
        try {
            item.country = await location.get(item.address) || DEFAULT_COUNTRY;
        } catch (e) {
            console.log('Country lookup error:', e.message);
            item.country = DEFAULT_COUNTRY;
        }
    }));
}

// 生成最终链接列表
function generateFinalURLs() {
    for (let item of finalList) {
        let country = item.country;
        let countryEmoji = emojiList[countryList.indexOf(country)] || DEFAULT_EMOJI;
        countryCount[country] = (countryCount[country] || 0) + 1;

        let nodeName = `${countryEmoji}${country} ${countryCount[country]}${config.nodeAddName}`;
        
        try {
            switch (item.type) {
                case 'vmess':
                    item.data.ps = nodeName;
                    urlCountryList[country].push('vmess://' + Buffer.from(JSON.stringify(item.data), 'utf8').toString('base64'));
                    break;
                case 'trojan':
                    urlCountryList[country].push(`trojan://${item.data}#${encodeURIComponent(nodeName)}`);
                    break;
                case 'ss':
                    urlCountryList[country].push(`ss://${item.data}#${encodeURIComponent(nodeName)}`);
                    break;
                case 'ssr':
                    urlCountryList[country].push('ssr://' + Buffer.from(item.data.replace('{name}', Buffer.from(nodeName, 'utf8').toString('base64')), 'utf8').toString('base64'));
                    break;
                case 'https':
                    urlCountryList[country].push(`https://${item.data}#${encodeURIComponent(nodeName)}`);
                    break;
                default:
                    break;
            }
        } catch (e) {
            console.log(`${item.type} node processing error:`, e.message);
        }
    }
    
    for (const countryNodes of Object.values(urlCountryList)) {
        finalURLs.push(...countryNodes);
    }
}

// 输出结果
function outputResults() {
    console.log(`去重改名完成\n一共${urlList.length}个节点，去重${urlList.length - finalURLs.length}个节点，剩余${finalURLs.length}个节点`);
    fs.writeFileSync('./out', finalURLs.join('\n'));
}

// 主运行函数
async function run() {
    initializeCountryData();
    parseURLs();
    deduplicate();
    await processCountries();
    generateFinalURLs();
    outputResults();
}

run();
