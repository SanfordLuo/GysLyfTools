"""
@Author  :   luoyafei
@Time    :   2025/8/3 17:45
@Desc    :   监控商品评论
https://www.amazon.com/dp/B0FBRM728Y
"""
import socket
import logging
from lxml import etree
from curl_cffi import requests
from utils.logger import config_log
from utils.feishu import send_fs_msg


class MonitorAsinReview(object):
    def __init__(self):
        self.timeout = 10
        self.retry = 3

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
                    self.set_proxy(session)
                    response = session.get(url, timeout=self.timeout, verify=False)
                    logging.info(f"[request_asin_review response]: {response.status_code}")

                    if response.status_code == 404:
                        logging.info(f"商品不存在")
                        return False, url, "商品不存在"
                    elif response.status_code == 200:
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

    def run_monitor(self, asin):
        """
        入口
        :param asin:
        :return:
        """
        rating, reviews = 0, 0
        msg_status = "success"

        resp_tag, asin_url, resp_text = self.request_asin_review(asin)
        if resp_tag:
            rating, reviews = self.parse_review(resp_text)
            if rating is None and reviews is None:
                msg_status = "未解析到评论信息"
        else:
            msg_status = resp_text

        msg_dict = {
            "title": "商品评论数监控",
            "text": {
                "ASIN": asin,
                "商品链接": asin_url,
                "当前评分": rating,
                "当前评论总数": reviews,
                "status": msg_status,
                "主机名称": socket.gethostname()
            }
        }
        send_fs_msg(msg_dict)


if __name__ == '__main__':
    config_log("run_asin_rank.log")

    _asin = "B0FBRM728Y"

    obj = MonitorAsinReview()
    obj.run_monitor(_asin)
