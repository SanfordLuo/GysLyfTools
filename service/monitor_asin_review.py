"""
@Author  :   luoyafei
@Time    :   2025/8/3 17:45
@Desc    :   监控商品评论
https://www.amazon.com/dp/B0FBRM728Y
"""
import json
import socket
import logging
import datetime
from lxml import etree
from curl_cffi import requests
from urllib.parse import urljoin
from utils.logger import config_log
from utils.feishu import send_fs_msg
from setting.global_setting import GlobalSetting


class MonitorAsinReview(object):
    def __init__(self):
        self.setting = GlobalSetting.instance()
        self.redis_db_0 = self.setting.redis_db_0
        self.timeout = 10
        self.retry = 3
        self.cache_stats_review_key = "STATS:REVIEW:{asin}"
        self.cache_stats_review_exp = 60 * 60 * 24 - 60 * 5

    def set_headers(self, session):
        """
        设置请求头
        :param session:
        :return:
        """
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
        session.headers = headers

    def set_proxy(self, session):
        """
        设置代理
        :param session:
        :return:
        """
        proxy_url = "http://127.0.0.1:8888"
        logging.info(f"proxy_url: {proxy_url}")
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        session.proxies = proxies

    def request_validate_captcha(self, url, session, response):
        """
        :return:
        """
        resp_text = response.text
        doc = etree.HTML(resp_text)
        form_actions = doc.xpath('//form/@action')
        validate_action = ""
        for action in form_actions:
            if "errors/validateCaptcha" in action:
                validate_action = action
                break

        if validate_action:
            try:
                form = doc.xpath(f'//form[@action="{validate_action}"]')[0]
                input_dict = {}
                for input_tag in form.xpath('.//input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value')
                    input_dict[name] = value
                validate_url = urljoin(url, validate_action)

                logging.info(f"[request_validate_captcha request]: {validate_url}, {input_dict}")

                response = session.get(url, params=input_dict, timeout=self.timeout, verify=False)
                logging.info(f"[request_validate_captcha response]: {response.status_code}. {response.url}")
            except Exception as error:
                logging.exception(f"[request_validate_captcha error]: {error}")

        return response

    def request_asin_review(self, asin):
        """
        搜索商品
        :param asin:
        :return:
        """
        url = f"https://www.amazon.com/dp/{asin}"

        logging.info(f"[request_asin_review request]: {url}")
        for _idx in range(self.retry):
            try:
                with requests.Session(impersonate="chrome131") as session:
                    self.set_headers(session)
                    # self.set_proxy(session)
                    response = session.get(url, timeout=self.timeout, verify=False)
                    logging.info(f"[request_asin_review response]: {response.status_code}. {response.url}")

                    if response.status_code == 404:
                        logging.info(f"商品不存在")
                        return False, url, "商品不存在"

                    elif response.status_code == 200:
                        response = self.request_validate_captcha(url, session, response)

                        doc = etree.HTML(response.text)
                        if doc.xpath('//*[@id="acrCustomerReviewText"]'):
                            return True, url, response.text

            except Exception as error:
                logging.exception(f"[request_asin_review error]: {error}")

        return False, url, "请求失败"

    def parse_review(self, resp_text):
        """
        解析评论
        :return:
        """
        rating, reviews = 0, 0

        doc = etree.HTML(resp_text)

        # 评分
        try:
            rating = doc.xpath('//*[@id="acrPopover"]/span[1]/a/span/text()')[0].strip()
            rating = float(rating)
            logging.info(f"rating: {rating}")
        except Exception as error:
            logging.exception(f"评分解析失败: {error}")

        # 评论数
        try:
            reviews = doc.xpath('//*[@id="acrCustomerReviewText"]/text()')[0].strip()
            reviews = int(reviews.split(" ")[0])
            logging.info(f"reviews: {reviews}")
        except Exception as error:
            logging.exception(f"评论数解析失败: {error}")

        return rating, reviews

    def update_cache_review(self, asin, rating, reviews):
        """
        :return:
        """
        is_update = False
        cache_key = self.cache_stats_review_key.format(asin=asin)

        review_data = {}
        for _idx in range(2):
            try:
                cache_value = self.redis_db_0.get(cache_key)
                logging.info(f"get_cache_review. cache_key: {cache_key}, cache_value: {cache_value}")
                if cache_value:
                    review_data = json.loads(cache_value)
                break
            except Exception as error:
                logging.exception(f"get_cache_review error: {error}")

        if review_data.get("rating", 0) != rating or review_data.get("reviews", 0) != reviews:
            is_update = True
            new_review_data = {
                "rating": rating,
                "reviews": reviews,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            cache_value = json.dumps(new_review_data)
            for _idx in range(2):
                try:
                    self.redis_db_0.setex(name=cache_key, value=cache_value, time=self.cache_stats_review_exp)
                    logging.info(f"set_cache_review. cache_key: {cache_key}, cache_value: {cache_value}")
                    break
                except Exception as error:
                    logging.exception(f"set_cache_review error: {error}")

        return is_update

    def run_monitor(self, asin):
        """
        入口
        :param asin:
        :return:
        """
        fs_switch = False
        rating, reviews = 0, 0
        msg_status = "成功-评论无变化"

        resp_tag, asin_url, resp_text = self.request_asin_review(asin)
        if resp_tag:
            rating, reviews = self.parse_review(resp_text)
            is_update = self.update_cache_review(asin, rating, reviews)
            if is_update:
                msg_status = "成功-评论有变化"
                fs_switch = True
            if not rating or not reviews:
                msg_status = "未解析到评论信息"
                fs_switch = True
        else:
            msg_status = resp_text
            fs_switch = True

        msg_dict = {
            "title": "商品评论数监控",
            "text": {
                "ASIN": asin,
                "商品链接": asin_url,
                "当前评分": rating,
                "当前评论数": reviews,
                "监控状态": msg_status,
                "主机名称": socket.gethostname()
            }
        }

        logging.info(f"fs_switch: {fs_switch}")

        if fs_switch:
            send_fs_msg(msg_dict)


if __name__ == '__main__':
    config_log("monitor_asin_review.log")

    # 别人
    # _asin = "B0FBRM728Y"
    # 喵喵
    _asin = "B0F7Y61Q6X"

    obj = MonitorAsinReview()
    obj.run_monitor(_asin)
