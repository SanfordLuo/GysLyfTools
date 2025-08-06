"""
@Author  :   luoyafei
@Time    :   2025/8/6 0:12
@Desc    :   监控商品评论
"""
import json
import socket
import logging
import time
import datetime
import random
from lxml import etree
import selenium.webdriver.support.expected_conditions as ec
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from utils.logger import config_log
from utils.feishu import send_fs_msg
from setting.global_setting import GlobalSetting


class MonitorAsinReviewDriver(object):
    def __init__(self):
        self.driver = None
        self.wait_time = 3
        self.setting = GlobalSetting.instance()
        self.redis_db_0 = self.setting.redis_db_0
        self.cache_stats_review_key = "STATS:REVIEW:{asin}"
        self.cache_stats_review_exp = 60 * 60 * 24 - 60 * 10
        self.cache_request_failed_key = "INCR:REQUEST_FAILED:{asin}"
        self.request_failed_incr_limit = 5

    def init_driver(self):
        """
        :return:
        """
        if self.driver:
            return True

        logging.info("init_driver begin")

        try:
            chrome_options = Options()

            # 基础配置, --disable-dev-shm-usage 和 --no-sandbox 参数，这是无头模式在Linux服务器稳定运行的关键配置
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")  # 关键解决内存问题
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--incognito")

            # 高级防检测
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 自定义UA
            chrome_version = random.randint(120, 137)
            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_argument(f'accept-language=en-US,en;q=0.9')

            # 初始化驱动
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # 超时设置
            self.driver.set_page_load_timeout(40)
            self.driver.set_script_timeout(40)

            logging.info("init_driver success")
            return True

        except Exception as error:
            logging.error(f"init_driver error: {error}")

        return False

    def quit_driver(self):
        """
        :return:
        """
        try:
            self.driver.quit()
        except Exception as error:
            pass

    def driver_search_asin(self, asin):
        """
        :return:
        """
        rating, reviews = 0, 0

        for _idx in range(3):
            logging.info(f"driver_search_asin begin, {_idx}")

            is_success = self.init_driver()
            if not is_success:
                continue

            # 打开首页
            try:
                url = "https://www.amazon.com/errors/validateCaptcha"
                self.driver.get(url)
                time.sleep(self.wait_time)
                button = self.driver.find_element(By.CLASS_NAME, "a-button-text")
                button.click()
                time.sleep(self.wait_time)
                logging.info("打开首页成功")
            except Exception as error:
                logging.error(f"打开首页失败: {error}")
                continue

            # 搜索商品
            try:
                button = WebDriverWait(self.driver, self.wait_time).until(
                    ec.visibility_of_element_located((By.XPATH, '//*[@id="twotabsearchtextbox"]')))
                button.click()
                time.sleep(self.wait_time)
                button.send_keys(asin)
                time.sleep(self.wait_time)
                button = WebDriverWait(self.driver, self.wait_time).until(
                    ec.visibility_of_element_located((By.XPATH, '//*[@id="nav-search-submit-button"]')))
                button.click()
                time.sleep(self.wait_time)
                logging.info("搜索商品成功")
            except Exception as error:
                logging.error(f"搜索商品失败: {error}")
                continue

            # 解析商品
            try:
                page_content = self.driver.page_source
                doc = etree.HTML(page_content)
                asin_node = doc.xpath(f'//*[@data-asin="{asin}"]')[0]
                # ['4.8 out of 5 stars', '26']
                span_text_list = []
                span_text_nodes = asin_node.xpath('.//div[@data-cy="reviews-block"]//span/text()')
                for _node in span_text_nodes:
                    if _node.strip():
                        span_text_list.append(_node.strip())
                logging.info(f"span_text_list: {span_text_list}")
                if len(span_text_list) < 2:
                    continue
                # 评分
                rating = span_text_list[0].split(" ")[0]
                rating = float(rating)
                # 评论数
                reviews = span_text_list[1]
                reviews = int(reviews)

                logging.info("解析商品成功")
                return rating, reviews, ""
            except Exception as error:
                logging.error(f"解析商品失败: {error}")

        return rating, reviews, "请求失败"

    def get_request_failed_incr(self, asin):
        """
        :param asin:
        :return:
        """
        cache_key = self.cache_request_failed_key.format(asin=asin)
        for _idx in range(2):
            try:
                cache_value = self.redis_db_0.get(cache_key)
                logging.info(f"get_request_failed_incr. {cache_key}: {cache_value}")
                if cache_value:
                    return int(cache_value)
                return 0
            except Exception as error:
                logging.exception(f"get_request_failed_incr. error: {error}")

        return 0

    def add_request_failed_incr(self, asin):
        """
        :param asin:
        :return:
        """
        cache_key = self.cache_request_failed_key.format(asin=asin)
        for _idx in range(2):
            try:
                cache_value = self.redis_db_0.incr(cache_key)
                logging.info(f"add_request_failed_incr. {cache_key}: {cache_value}")
                return int(cache_value)
            except Exception as error:
                logging.exception(f"add_request_failed_incr. error: {error}")

        return 0

    def del_request_failed_incr(self, asin):
        """
        :param asin:
        :return:
        """
        cache_key = self.cache_request_failed_key.format(asin=asin)
        for _idx in range(2):
            try:
                cache_value = self.redis_db_0.delete(cache_key)
                logging.info(f"del_request_failed_incr. {cache_key}: {cache_value}")
                return
            except Exception as error:
                logging.exception(f"del_request_failed_incr. error: {error}")

        return

    def update_cache_review(self, asin, rating, reviews):
        """
        :return:
        """
        fs_switch = False
        set_switch = False
        msg_status = "成功"
        cache_key = self.cache_stats_review_key.format(asin=asin)

        time_format = "%Y-%m-%d %H:%M:%S"

        # 旧数据
        review_data = {}
        for _idx in range(2):
            try:
                cache_value = self.redis_db_0.get(cache_key)
                logging.info(f"get_cache_review. {cache_key}: {cache_value}")
                if cache_value:
                    review_data = json.loads(cache_value)
                break
            except Exception as error:
                logging.exception(f"get_cache_review error: {error}")

        # 新数据
        new_review_data = {
            "rating": rating,
            "reviews": reviews,
            "time": datetime.datetime.now().strftime(time_format)
        }

        if review_data.get("rating", 0) != new_review_data.get("rating", 0) \
                or review_data.get("reviews", 0) != new_review_data.get("reviews", 0):
            set_switch = True
            if review_data and new_review_data:
                fs_switch = True
                msg_status = "成功-评论有变化"
        else:
            old_time = review_data.get("time", datetime.datetime.now().strftime(time_format))
            new_time = new_review_data["time"]
            seconds_diff = (datetime.datetime.strptime(new_time, time_format)
                            - datetime.datetime.strptime(old_time, time_format)).total_seconds()
            if seconds_diff >= self.cache_stats_review_exp:
                set_switch = True
                fs_switch = True

        if set_switch:
            cache_value = json.dumps(new_review_data)
            for _idx in range(2):
                try:
                    self.redis_db_0.set(cache_key, cache_value)
                    logging.info(f"set_cache_review. {cache_key}: {cache_value}")
                    break
                except Exception as error:
                    logging.exception(f"set_cache_review. error: {error}")

        return fs_switch, msg_status

    def run_monitor(self, asin):
        """
        入口
        :param asin:
        :return:
        """
        fs_switch = False
        asin_url = f"https://www.amazon.com/dp/{asin}"

        # 查询失败次数是否达上限
        now_incr = self.get_request_failed_incr(asin)
        if now_incr >= self.request_failed_incr_limit:
            logging.info("请求失败次数达上限, 暂不执行")
            return False

        rating, reviews, msg_status = self.driver_search_asin(asin)
        self.quit_driver()
        # 请求失败成功
        if msg_status:
            now_incr = self.add_request_failed_incr(asin)
            if now_incr >= self.request_failed_incr_limit:
                fs_switch = True
        # 请求成功
        else:
            self.del_request_failed_incr(asin)
            fs_switch, msg_status = self.update_cache_review(asin, rating, reviews)

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
    config_log("monitor_asin_review_driver.log")

    # 别人
    # _asin = "B0FBRM728Y"
    # 喵喵
    _asin = "B0F7Y61Q6X"

    obj = MonitorAsinReviewDriver()
    obj.run_monitor(_asin)
