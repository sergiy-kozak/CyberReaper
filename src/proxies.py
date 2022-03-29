import json
import random
import re
import time
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import typing
from PyRoxy import ProxyType, Proxy
import logging


logging.basicConfig(format='[%(asctime)s - %(levelname)s] %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


TIMEOUT = 10
PROXY_TIMEOUT = 5
SCRAPE_THREADS = 20
PROXY_THREADS = 100
IP_REGEX = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
PORT_REGEX = r'[0-9]+'
IP_PORT_REGEX = rf'({IP_REGEX}):({PORT_REGEX})'
IP_PORT_TABLE_REGEX = rf'({IP_REGEX})\s*</td>\s*<td>\s*({PORT_REGEX})'


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
]


def get_headers():
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.google.com/',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-Gpc': '1',
        'Upgrade-Insecure-Requests': '1',
    }


class Provider:
    def __init__(self, url, proto):
        self.url = url
        self.proto = proto

    def scrape(self):
        return self.parse(self.fetch(self.url))

    def fetch(self, url):
        response = requests.get(url=url, timeout=TIMEOUT, headers=get_headers())
        response.raise_for_status()
        return response.text

    def parse(self, data):
        raise NotImplementedError

    def __str__(self):
        return f'{self.proto.name} | {self.url}'


class RegexProvider(Provider):
    def __init__(self, url, proto, regex):
        super().__init__(url, proto)
        self.regex = regex

    def parse(self, data):
        for ip, port in re.findall(self.regex, data):
            yield ip, port, self.proto


class PubProxyProvider(RegexProvider):
    def __init__(self, url, proto, regex=IP_PORT_REGEX):
        super().__init__(url, proto, regex)

    def scrape(self):
        for _ in range(10):
            yield from super().scrape()
            time.sleep(1)


class GeonodeProvider(Provider):
    def parse(self, data):
        data = json.loads(data)
        for row in data['data']:
            yield row['ip'], row['port'], self.proto


class UaShieldProvider(Provider):
    def __init__(self, url):
        super().__init__(url, proto=ProxyType.HTTP)

    def parse(self, data):
        data = json.loads(data)
        for obj in data:
            if 'auth' in obj:
                continue
            ip, port = obj['ip'].split(':')
            yield ip, port, ProxyType[obj['scheme'].upper()]


class HideMyNameProvider(RegexProvider):
    def __init__(self, url, proto, regex=IP_PORT_TABLE_REGEX, pages=(1, 10)):
        self.pages = pages
        super().__init__(url, proto, regex)

    def scrape(self):
        for page in range(*self.pages):
            url = self.url
            if page != 1:
                url = url + '&start=' + str(64 * (page - 1))

            result = list(self.parse(self.fetch(url)))
            if not result:
                return

            yield from result


class ProxyListProvider(RegexProvider):
    def __init__(self, url, proto, regex=r"Proxy\('([\w=]+)'\)"):
        super().__init__(url, proto, regex)

    def scrape(self):
        for page in range(1, 20):
            url = self.url + '?p=' + str(page)
            result = list(self.parse(self.fetch(url)))
            if not result:
                return
            yield from result
            time.sleep(1)

    def parse(self, data):
        for proxy in re.findall(self.regex, data):
            ip, port = b64decode(proxy).decode().split(':')
            yield ip, port, self.proto


class FarmProxyProvider(RegexProvider):
    def __init__(self, api_key, proxy):
        self.proxy = proxy
        super().__init__(
            url=f'https://panel.farmproxy.net/api/v1/proxies.protocol-ip-port.txt?api_key={api_key}',
            proto=ProxyType.HTTP,
            regex=rf'(socks4|socks5|http)://({IP_REGEX}):({PORT_REGEX})'
        )

    def parse(self, data):
        for proto, ip, port in re.findall(self.regex, data):
            yield ip, port, ProxyType[proto.upper()]

    def fetch(self, url):
        response = requests.get(url=url, timeout=TIMEOUT, headers=get_headers(), proxies={'https': self.proxy})
        response.raise_for_status()
        return response.text


# noinspection LongLine
PROVIDERS = [
    # Manual
    RegexProvider('https://raw.githubusercontent.com/porthole-ascend-cinnamon/proxy_scraper/main/manual/socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/porthole-ascend-cinnamon/proxy_scraper/main/manual/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/porthole-ascend-cinnamon/proxy_scraper/main/manual/http.txt', ProxyType.HTTP, IP_PORT_REGEX),

    # Multi-scheme
    UaShieldProvider('https://raw.githubusercontent.com/opengs/uashieldtargets/v2/proxy.json'),
    # FarmProxyProvider(
    #     os.getenv('FARM_PROXY_API_KEY'),
    #     os.getenv('STABLE_IP_PROXY')
    # ),

    # SOCKS4
    RegexProvider('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://www.my-proxy.com/free-socks-4-proxy.html', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://www.socks-proxy.net/', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://www.freeproxychecker.com/result/socks4_proxies.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('http://proxydb.net/?protocol=socks4', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('https://socks-proxy.net/', ProxyType.SOCKS4, IP_PORT_REGEX),
    PubProxyProvider('http://pubproxy.com/api/proxy?limit=5&format=txt&type=socks4', ProxyType.SOCKS4),
    RegexProvider('https://www.proxy-list.download/SOCKS4', ProxyType.SOCKS4, IP_PORT_TABLE_REGEX),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=fast&protocols=socks4', ProxyType.SOCKS4),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=medium&protocols=socks4', ProxyType.SOCKS4),
    HideMyNameProvider('https://hidemy.name/ru/proxy-list/?type=4', ProxyType.SOCKS4),
    RegexProvider('http://www.proxylists.net/socks4.txt', ProxyType.SOCKS4, IP_PORT_REGEX),
    RegexProvider('http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks', ProxyType.SOCKS4, IP_PORT_REGEX),

    # SOCKS5
    RegexProvider('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://spys.me/socks.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://www.my-proxy.com/free-socks-5-proxy.html', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('http://proxydb.net/?protocol=socks5', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://www.proxy-list.download/api/v1/get?type=socks5', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://api.openproxylist.xyz/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://openproxy.space/list/socks5', ProxyType.SOCKS5, f'"{IP_PORT_REGEX}"'),
    PubProxyProvider('http://pubproxy.com/api/proxy?limit=5&format=txt&type=socks5', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('https://www.proxy-list.download/SOCKS5', ProxyType.SOCKS5, IP_PORT_TABLE_REGEX),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=fast&protocols=socks5', ProxyType.SOCKS5),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=medium&protocols=socks5', ProxyType.SOCKS5),
    RegexProvider('https://www.freeproxychecker.com/result/socks5_proxies.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    RegexProvider('http://www.proxylists.net/socks5.txt', ProxyType.SOCKS5, IP_PORT_REGEX),
    HideMyNameProvider('https://hidemy.name/ru/proxy-list/?type=5', ProxyType.SOCKS5),

    # HTTP(S)
    RegexProvider('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://api.proxyscrape.com/?request=displayproxies&proxytype=http', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/almroot/proxylist/master/list.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http%2Bhttps.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http%2Bs.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.proxy-list.download/api/v1/get?type=http', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.proxy-list.download/api/v1/get?type=https', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://spys.me/proxy.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.sslproxies.org/', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.my-proxy.com/free-anonymous-proxy.html', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.my-proxy.com/free-transparent-proxy.html', ProxyType.HTTP, IP_PORT_REGEX),
    *(
        RegexProvider(f'https://www.my-proxy.com/free-proxy-list-{i}.html', ProxyType.HTTP, IP_PORT_REGEX)
        for i in range(1, 11)
    ),
    RegexProvider('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://proxydb.net/?protocol=http&protocol=https', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://api.openproxylist.xyz/http.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://www.google-proxy.net/', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://free-proxy-list.net/', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.us-proxy.org/', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://free-proxy-list.net/uk-proxy.html', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://free-proxy-list.net/anonymous-proxy.html', ProxyType.HTTP, IP_PORT_REGEX),
    PubProxyProvider('http://pubproxy.com/api/proxy?limit=5&format=txt&type=http', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://www.proxylists.net/http.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://openproxy.space/list/http', ProxyType.HTTP, f'"{IP_PORT_REGEX}"'),
    RegexProvider('https://www.proxy-list.download/HTTPS', ProxyType.HTTP, IP_PORT_TABLE_REGEX),
    RegexProvider('https://www.proxy-list.download/HTTP', ProxyType.HTTP, IP_PORT_TABLE_REGEX),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=fast&protocols=http%2Chttps', ProxyType.HTTP),
    GeonodeProvider('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&speed=medium&protocols=http%2Chttps', ProxyType.HTTP),
    RegexProvider('http://www.httptunnel.ge/ProxyListForFree.aspx', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://api.foxtools.ru/v2/Proxy.txt', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('http://proxysearcher.sourceforge.net/Proxy%20List.php?type=http', ProxyType.HTTP, IP_PORT_REGEX),
    RegexProvider('https://www.ipaddress.com/proxy-list/', ProxyType.HTTP, rf'({IP_REGEX})</a>:({PORT_REGEX})'),
    ProxyListProvider('https://proxy-list.org/english/index.php', ProxyType.HTTP),
    HideMyNameProvider('https://hidemy.name/ru/proxy-list/?type=hs', ProxyType.HTTP, pages=(1, 11)),
]


def scrape_all():
    with ThreadPoolExecutor(SCRAPE_THREADS) as executor:
        futures = {
            executor.submit(provider.scrape): provider
            for provider in PROVIDERS
        }
        for future in as_completed(futures):
            provider = futures[future]
            try:
                result = set(future.result())
                logger.info(f'Success: {provider} : {len(result)}')
                yield from result
            except Exception as exc:
                logger.error(f'{provider} : {exc}')


def check_proxies(proxies):
    urls = [
        'http://httpbin.org/get',
        'http://azenv.net/',
        'http://www.proxy-listen.de/azenv.php',
        'http://www.meow.org.uk/cgi-bin/env.pl',
        'https://users.ugent.be/~bfdwever/start/env.cgi',
        'https://www2.htw-dresden.de/~beck/cgi-bin/env.cgi',
        'http://mojeip.net.pl/asdfa/azenv.php',
    ]

    future_to_proxy = {}
    with ThreadPoolExecutor(PROXY_THREADS) as executor:
        for url, proxies_chunk in zip(urls, (proxies[i::len(urls)] for i in range(len(urls)))):
            logger.info(f'Checking {len(proxies_chunk)} proxies against {url}')
            future_to_proxy.update({
                executor.submit(proxy.check, url, PROXY_TIMEOUT): proxy
                for proxy in proxies_chunk
            })

        for future in as_completed(future_to_proxy):
            if future.result():
                yield future_to_proxy[future]


def refresh_proxies():
    proxies = set(scrape_all())
    logger.info(f'Proxies: {len(proxies)}')
    proxies = [
        Proxy(ip, int(port), proto)
        for ip, port, proto in proxies
    ]
    random.shuffle(proxies)
    return proxies



def update_proxies_file(proxies: typing.List[Proxy], proxies_file_path="MHDDoS/files/proxies/proxylist.txt"):
    with open(proxies_file_path, 'w') as out:
        out.writelines((str(proxy) + '\n' for proxy in proxies))


if __name__ == '__main__':
    expected_at_least = 10000
    proxies = refresh_proxies()
    if len(proxies)  < expected_at_least:
        logger.error('Found too few proxies')
        exit(1)
    update_proxies_file(proxies)

