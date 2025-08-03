#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
from utils.config import LOG_PATH
from logging.handlers import TimedRotatingFileHandler


def config_log(file_name):
    """
    日志方法
    :return:
    """
    file_path = f"{LOG_PATH}/{file_name}"
    fmt = '[%(asctime)s] - %(threadName)s - %(filename)s - %(message)s'
    log = logging.getLogger('')
    file_time_handler = TimedRotatingFileHandler(file_path, when="MIDNIGHT", interval=1, backupCount=3)
    file_time_handler.suffix = "%Y%m%d"
    file_time_handler.setFormatter(logging.Formatter(fmt))
    logging.basicConfig(level=logging.INFO, format=fmt)
    log.addHandler(file_time_handler)
