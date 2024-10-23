const fs = require('fs');
const location = require('./location');
const config = require('./config');

// Input file paths, defaulting to './url'
let urls = fs.readFileSync('./url', 'utf8');
let flags = JSON.parse(fs.readFileSync('./flags.json', 'utf8'));

let urlList = urls.split('\n');
let resList = [];
let stringList = [];
let finalList = [];
let finalURLs = [];
let countryList = ['UN'];
let emojiList = ['🏳️']; // 设置一个默认的旗帜符号
let countryCount = { UN: 0 };
let urlCountryList = { UN: [] };

async function run() {
    // Process flags
    for (let i = 0; i < flags.length; i++) {
        countryList.push(flags[i].code);
        emojiList.push(flags[i].emoji);
        countryCount[flags[i].code] = 0;
        urlCountryList[flags[i].code] = [];
    }

    // Parse URLs
    for (let i = 0; i < urlList.length; i++) {
        let url = urlList[i].trim();
        if (!url) continue; // Skip empty lines
        try {
            let protocol = url.split('://')[0];
            switch (protocol) {
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
                    console.log(`未知协议类型: ${protocol}`);
                    break;
            }
        } catch (e) {
            console.log(`解析URL出错: ${url}, 错误: ${e.message}`);
        }
    }

    // Deduplicate by converting objects to strings
    for (let i = 0; i < resList.length; i++) {
        stringList.push(JSON.stringify(resList[i]));
    }
    let afterList = Array.from(new Set(stringList));

    // Convert back to objects
    for (let i = 0; i < afterList.length; i++) {
        finalList.push(JSON.parse(afterList[i]));
    }

    // Batch test country
    for (let i = 0; i < finalList.length; i++) {
        try {
            finalList[i].country = await location.get(finalList[i].address) || 'UN';
        } catch (e) {
            finalList[i].country = 'UN';
            console.log(`获取国家信息出错: ${finalList[i].address}, 错误: ${e.message}`);
        }
    }

    // Convert back to links
    for (let i = 0; i < finalList.length; i++) {
        let item = finalList[i];
        let country = item.country || 'UN';
        countryCount[country]++;
        let name = emojiList[countryList.indexOf(country)] + country + ' ' + countryCount[country] + config.nodeAddName;

        if (!urlCountryList[country]) {
            urlCountryList[country] = [];
        }

        try {
            switch (item.type) {
                case 'vmess':
                    item.data.ps = name;
                    urlCountryList[country].push('vmess://' + Buffer.from(JSON.stringify(item.data), 'utf8').toString('base64'));
                    break;
                case 'trojan':
                    urlCountryList[country].push('trojan://' + item.data + '#' + encodeURIComponent(name));
                    break;
                case 'ss':
                    urlCountryList[country].push('ss://' + item.data + '#' + encodeURIComponent(name));
                    break;
                case 'ssr':
                    urlCountryList[country].push('ssr://' + Buffer.from(item.data.replace('{name}', Buffer.from(name, 'utf8').toString('base64')), 'utf8').toString('base64'));
                    break;
                case 'https':
                    urlCountryList[country].push('https://' + item.data + '#' + encodeURIComponent(name));
                    break;
                default:
                    console.log(`未知类型: ${item.type}`);
                    break;
            }
        } catch (e) {
            console.log(`生成链接错误: ${e.message}, 类型: ${item.type}`);
        }
    }

    // Flatten the URL list
    for (const country in urlCountryList) {
        finalURLs = finalURLs.concat(urlCountryList[country]);
    }

    console.log(`去重改名完成\n一共${urlList.length}个节点，去重${urlList.length - finalURLs.length}个节点，剩余${finalURLs.length}个节点`);
    
    // Output to './out'
    fs.writeFileSync('./out', finalURLs.join('\n'));
}

run();
