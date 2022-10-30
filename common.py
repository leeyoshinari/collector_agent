#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: leeyoshinari

import os
import json
import datetime
import traceback
import logging.handlers
import configparser
import requests


cfg = configparser.ConfigParser()
cfg.read('config.conf', encoding='utf-8')


def get_configure(key):
    return cfg.get('server', key, fallback=None)


def get_ip():
    """
    Get server's IP address
    :return: IP address
    """
    try:
        if cfg.getAgent('host'):
            IP = cfg.getAgent('host')
        else:
            result = os.popen("hostname -I |awk '{print $1}'").readlines()
            logger.debug(result)
            if result:
                IP = result[0].strip()
                logger.info(f'The IP address is: {IP}')
            else:
                logger.warning('Server IP address not found!')
                IP = '127.0.0.1'
    except:
        logger.error(traceback.format_exc())
        IP = '127.0.0.1'

    return IP


def http_post(url, post_data):
    header = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json; charset=UTF-8"}

    try:
        res = requests.post(url=url, json=post_data, headers=header)
        logger.info(f"The result of request is {res.content.decode('unicode_escape')}")
        if res.status_code == 200:
            response_data = json.loads(res.content.decode('unicode_escape'))
            if response_data['code'] == 0:
                return response_data['data']
            else:
                logger.error(response_data['msg'])
                raise Exception(response_data['msg'])
    except:
        logger.error(traceback.format_exc())
        raise


def http_get(url):
    try:
        res = requests.get(url=url)
        logger.info(f"The result of request is {res.content.decode('unicode_escape')}")
        if res.status_code == 200:
            response_data = json.loads(res.content.decode('unicode_escape'))
            if response_data['code'] == 0:
                return response_data['data']
            else:
                logger.error(response_data['msg'])
                raise Exception(response_data['msg'])
    except:
        logger.error(traceback.format_exc())
        raise


if not os.path.exists(get_configure('logPath')):
    os.mkdir(get_configure('logPath'))

log_level = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(filename)s[line:%(lineno)d] - %(message)s')
logger.setLevel(level=log_level.get(get_configure('level')))

current_day = datetime.datetime.now().strftime('%Y-%m-%d')
log_name = os.path.join(get_configure('logPath'), f'collector-{current_day}.log')
file_handler = logging.handlers.RotatingFileHandler(filename=log_name, maxBytes=10*1024*1024, backupCount=int(get_configure('backupCount')))

# file_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
