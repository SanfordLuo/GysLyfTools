"""
@Author  :   luoyafei
@Time    :   2025/3/28 10:22
@Desc    :   None
"""
import logging
import requests
from setting.config import FS_ROBOT_URL


def send_fs_msg(msg_dict):
    """
    飞书群提醒
    :param msg_dict:
    :return:
    """
    url = FS_ROBOT_URL
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "content": msg_dict.get("title"),
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"{k}: {v}",
                        "tag": "lark_md"
                    }
                }
                for k, v in msg_dict.get("text").items()
            ],
        }
    }
    for _r in range(3):
        try:
            with requests.session() as session:
                session.verify = False
                session.headers = {"Content-Type: application/json"}
                logging.info(f"发送飞书请求: {url}, {msg_dict}")
                response = session.post(url=url, json=data, timeout=(5, 15))
                logging.info(f"发送飞书响应:{response.status_code} {response.reason} {response.content}")
                response_dict = response.json()
                if response.status_code == 200 and response_dict.get("StatusMessage").__contains__("success"):
                    return True
        except BaseException as e:
            logging.exception(e)

    logging.info(f"发送飞书失败:{msg_dict} {url}")
    return False
