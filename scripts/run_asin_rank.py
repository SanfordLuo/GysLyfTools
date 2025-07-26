"""
@Author  :   luoyafei
@Time    :   2025/7/26 21:53
@Desc    :   跑商品排名
"""
import time
import os
import uuid
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as ec

logger.add("run_asin_rank.log")


class RunAsinRank(object):
    def __init__(self):
        self.driver = None
        self.wait_time = 5

    def init_driver(self):
        """
        :return:
        """
        logger.info("init_driver begin")

        try:
            temp_user_data_dir = f"/var/log/chrome_options/user_data_{int(time.time())}_{uuid.uuid4()}"
            if not os.path.exists(temp_user_data_dir):
                os.makedirs(temp_user_data_dir, exist_ok=True)

            chrome_options = Options()
            # 明确指定用户数据目录, 服务器不加会报错
            chrome_options.add_argument(f"--user-data-dir={temp_user_data_dir}")
            # 启用无头模式
            chrome_options.add_argument("--headless")
            # 禁止自动化检测
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            # 添加无痕模式选项
            chrome_options.add_argument("--incognito")
            # 禁用扩展
            chrome_options.add_argument("--disable-extensions")

            # 自定义 User-Agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')

            self.driver = webdriver.Chrome(options=chrome_options)
            # 最大化
            self.driver.maximize_window()
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(60)

            logger.info("init_driver success")
            return True

        except Exception as error:
            logger.exception(f"init_driver error: {error}")

        return False

    def quit_driver(self):
        """
        :return:
        """
        self.driver.quit()

    def open_home_and_change_zipcode(self):
        """
        打开首页
        :return:
        """
        logger.info("open_home begin")

        for _idx in range(3):
            try:
                url = "https://www.amazon.com/"
                self.driver.get(url)

                # 有时候进了首页不显示改邮编,需要点一下这个
                try:
                    button = WebDriverWait(self.driver, self.wait_time).until(
                        ec.visibility_of_element_located((By.XPATH, '//*[@href="/ref=nav_bb_logo"]')))
                    button.click()
                    time.sleep(self.wait_time)
                except Exception as error:
                    logger.info(f"no nav_bb_logo")

                # 检测首页进入后是否有修改地址的地方
                WebDriverWait(self.driver, self.wait_time).until(
                    ec.visibility_of_element_located((By.XPATH, '//*[@id="nav-global-location-popover-link"]')))

                logger.info("open_home success")

                # 更改邮编
                is_success = self.change_zipcode(zipcode)
                if is_success:
                    return True

            except Exception as error:
                logger.exception(f"open_home error: {error}")

        return False

    def change_zipcode(self, zipcode):
        """
        更改邮编
        :return:
        """
        logger.info("change_zipcode begin")

        try:
            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, '//input[@data-action-type="SELECT_LOCATION"]')))
            button.click()
            time.sleep(self.wait_time)

            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, '//input[@id="GLUXZipUpdateInput"]')))
            button.click()
            button.send_keys(zipcode)
            time.sleep(self.wait_time)

            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, '//*[@id="GLUXZipUpdate"]/span/input')))
            button.click()
            time.sleep(self.wait_time)

            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="GLUXConfirmClose"]')))
            self.driver.execute_script("arguments[0].click();", button)
            time.sleep(self.wait_time)

            # 检测邮编是否更新成功
            element = self.driver.find_element(By.XPATH, '//*[@id="glow-ingress-line2"]')
            element_text = element.text
            if zipcode in element_text:
                logger.info("change_zipcode success")
                return True

        except Exception as error:
            logger.exception(f"change_zipcode error: {error}")

        return False

    def parse_asin(self):
        """
        处理商品
        :return:
        """
        try:
            sponsored_list = []
            organic_list = []

            WebDriverWait(self.driver, self.wait_time).until(
                ec.presence_of_element_located((By.XPATH, '//div[@role="listitem" and @data-index]')))
            divs = self.driver.find_elements(By.XPATH, '//div[@role="listitem" and @data-index]')
            for _div in divs:
                print(_div)
                # 判断是否是 Sponsored 的
                sponsored_span = None
                try:
                    sponsored_span = _div.find_element(
                        By.XPATH, './/span[@aria-label="View Sponsored information or leave ad feedback"]')
                except Exception as error:
                    logger.info(f"no sponsored_span")
                asin = _div.get_attribute("data-asin")
                if sponsored_span:
                    sponsored_list.append(asin)
                else:
                    organic_list.append(asin)

            sponsored_dict = {str(_idx): _v for _idx, _v in enumerate(sponsored_list)}
            organic_dict = {str(_idx): _v for _idx, _v in enumerate(organic_list)}

            logger.info("parse_asin success")
            logger.info(f"sponsored_dict: {sponsored_dict}")
            logger.info(f"organic_dict: {organic_dict}")
            return sponsored_dict, organic_dict

        except Exception as error:
            logger.exception(f"parse_asin error: {error}")

        return {}, {}

    def search_keywords(self, keywords):
        """
        搜索关键词
        :return:
        """
        logger.info("search_keywords begin")

        try:
            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, '//*[@id="twotabsearchtextbox"]')))
            button.click()
            button.send_keys(keywords)
            time.sleep(self.wait_time)

            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, '//*[@id="nav-search-submit-button"]')))
            button.click()
            time.sleep(self.wait_time)

            sponsored_dict, organic_dict = self.parse_asin()
            if sponsored_dict or organic_dict:
                logger.info("search_keywords success")
                return sponsored_dict, organic_dict

        except Exception as error:
            logger.exception(f"search_keywords error: {error}")

        return {}, {}

    def search_keywords_next(self, page_num):
        """
        下一页
        :return:
        """
        logger.info(f"search_keywords_next begin. page_num: {page_num}")

        try:
            button = WebDriverWait(self.driver, self.wait_time).until(
                ec.visibility_of_element_located((By.XPATH, f'//*[@aria-label="Go to page {page_num}"]')))
            button.click()
            time.sleep(self.wait_time)

            sponsored_dict, organic_dict = self.parse_asin()
            if sponsored_dict or organic_dict:
                logger.info("search_keywords_next success")
                return sponsored_dict, organic_dict

        except Exception as error:
            logger.exception(f"search_keywords_next error: {error}")

        return {}, {}

    def run_asin(self, zipcode, keywords, total_page_nums):
        is_success = self.init_driver()
        if not is_success:
            return False

        # 打开首页并且更改邮编
        is_success = self.open_home_and_change_zipcode()
        if not is_success:
            return False

        # 搜索关键词
        all_asin_dict = {}
        sponsored_dict, organic_dict = self.search_keywords(keywords)
        all_asin_dict["1"] = {
            "sponsored_dict": sponsored_dict,
            "organic_dict": organic_dict
        }

        # 后面的太多, 只要广告位
        for idx in range(1, total_page_nums):
            page_num = idx + 1
            sponsored_dict, organic_dict = self.search_keywords_next(page_num)
            all_asin_dict[str(page_num)] = {
                "sponsored_dict": sponsored_dict,
                "organic_dict": organic_dict
            }

        self.quit_driver()

        logger.info(f"all_asin_dict: {all_asin_dict}")
        return all_asin_dict


if __name__ == '__main__':
    zipcode = "77429"
    keywords = "pack and play mattress"
    total_page_nums = 6
    obj = RunAsinRank()
    obj.run_asin(zipcode, keywords, total_page_nums)
