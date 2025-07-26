"""
@Author  :   luoyafei
@Time    :   2025/7/26 18:01
@Desc    :   None
"""
from lxml import etree
from loguru import logger
from curl_cffi import requests

logger.add(
    "xxw_demo.log"
)


def set_session():
    headers = {
        "Host": "www.amazon.com",
        "device-memory": "8",
        "sec-ch-device-memory": "8",
        "dpr": "2",
        "sec-ch-dpr": "2",
        "viewport-width": "1260",
        "sec-ch-viewport-width": "1260",
        "rtt": "350",
        "downlink": "1.55",
        "ect": "3g",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-platform-version": "\"10.0.0\"",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "referer": "https://www.amazon.com/ref=nav_bb_logo",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=0, i",
        "accept-encoding": "gzip, deflate, br, zstd"
    }
    user = "roxvybuild2024"
    pwd = "flyRSIiKKyuYUlWfgE98"
    country = "us"
    country_format = f"-region-{country.lower()}" if country else ""
    # proxy_url = f"http://{user}{country_format}:{pwd}@zjdanli007.pr-as.roxlabs.cn:4600"
    proxy_url = "http://127.0.0.1:8888"
    logger.info(f"proxy_url: {proxy_url}")
    proxy_handler = {"http": proxy_url, "https": proxy_url}

    session = requests.Session(impersonate="chrome131")
    session.headers = headers
    session.proxies = proxy_handler

    return session


def get_nav_logo(session):
    url = "https://www.amazon.com/ref=nav_logo"
    headers = {
        "Host": "www.amazon.com",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=0, i",
        "accept-encoding": "gzip, deflate, br, zstd"
    }
    try:
        response = session.get(url, headers=headers, verify=False, timeout=20)
        logger.info(f"get_nav_bb_logo response: {response.status_code}")
        if response.status_code == 200:
            resp_text = response.text
            return resp_text
    except Exception as error:
        logger.exception(f"get_nav_bb_logo error: {error}")

    return None


def change_zipcode(session, zipcode):
    url = "https://www.amazon.com/portal-migration/hz/glow/address-change"
    params = {
        "actionSource": "glow"
    }
    data = {
        "locationType": "LOCATION_INPUT",
        "zipCode": zipcode,
        "deviceType": "web",
        "storeContext": "generic",
        "pageType": "Gateway",
        "actionSource": "glow"
    }
    try:
        response = session.post(url, params=params, json=data, verify=False, timeout=20)
        logger.info(f"change_zipcode response: {response.status_code}")
        if response.status_code == 200:
            resp_json = response.json()
            return resp_json
    except Exception as error:
        logger.exception(f"change_zipcode error: {error}")

    return None


def search_sponsored(session, keywords):
    url = "https://www.amazon.com/s/ref=nb_sb_noss_1"
    params = {
        "url": "search-alias=aps",
        "field-keywords": keywords,
        "crid": "DT72AI7G7F2R",
        "sprefix": f"{keywords},aps,432"
    }

    try:
        response = session.get(url, params=params, verify=False, timeout=20)
        logger.info(f"search_sponsored response: {response.status_code}")
        if response.status_code == 200:
            resp_text = response.text
            return resp_text
    except Exception as error:
        logger.exception(f"change_zipcode error: {error}")

    return None


def parse_sponsored(resp_text):
    sponsored_dict = {}

    try:
        tree = etree.HTML(resp_text)
        divs = tree.xpath('//div[@role="listitem" and @data-index]')
        for _div in divs:
            # 判断是否是 Sponsored 的
            sponsored_span = _div.xpath('.//span[@aria-label="View Sponsored information or leave ad feedback"]')
            if not sponsored_span:
                continue
            span_text = tree.xpath(
                './/h2[@class="a-size-base-plus a-spacing-none a-color-base a-text-normal"]/span/text()')
            if not span_text:
                continue
            title = span_text[0]

            data_index = _div.get('data-index')
            asin = _div.get("data-asin")

            sponsored_dict[data_index] = {
                "asin": asin
            }
    except Exception as error:
        logger.exception(f"parse_sponsored error: {error}")

    return sponsored_dict


def run():
    sponsored_dict = {}

    zipcode = "77429"
    keywords = "pack and play mattress"
    blue_asin = "B0F7Y61Q6X"

    session = set_session()

    get_nav_logo(session)

    # 更改邮编
    change_resp = change_zipcode(session, zipcode)
    if not change_resp:
        return sponsored_dict
    resp_zipcode = change_resp.get("address", {}).get("zipCode", "")
    if resp_zipcode != zipcode:
        logger.error(f"change_zipcode failed. zipcode: {zipcode}, resp_zipcode: {resp_zipcode}")
        return sponsored_dict
    now_resp_text = get_nav_logo(session)

    resp_text = search_sponsored(session, keywords)
    if resp_text:
        sponsored_dict = parse_sponsored(resp_text)

    logger.info(f"sponsored_dict: {sponsored_dict}")
    return sponsored_dict


if __name__ == '__main__':
    success_total = 0
    for _idx in range(1):
        ret = run()
        if ret:
            success_total += 1

        logger.info(f"success_total: {success_total}")

    logger.info(f"=========== end: {success_total} ==========")

    crid_dict = {
        "77429": "QWZJHQPU5KN7",
        "34711": "1G3VLH04CCVO6"
    }

"""
77429

34711

https://www.amazon.com/ref=nav_bb_logo

91TPCPSGHAM8

//*[@id="12f625b7-b41e-4eba-aacf-deef7340439c"]/div/div/span/div/div/div[2]/span/a/div/img
"""
