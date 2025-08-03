"""
@Author  :   luoyafei
@Time    :   2025/8/3 20:06
@Desc    :   None
"""
import redis
import logging
from setting.config import RedisConfig
from utils.singleton import Singleton


class GlobalSetting(Singleton):
    def __init__(self):
        self.redis_socket_connect_timeout = 30
        self.redis_socket_timeout = 30
        self.redis_db_0 = None

        self.init_setting()

    def init_setting(self):
        logging.info(f"init_setting begin ... ")

        self.redis_db_0 = redis.Redis(
            host=RedisConfig.host, port=RedisConfig.port,
            db=0, password=RedisConfig.password,
            socket_connect_timeout=self.redis_socket_connect_timeout,
            socket_timeout=self.redis_socket_timeout,
            decode_responses=True
        )
        logging.info(f"redis_db_0 finish")

        logging.info(f"init_setting end ... ")
