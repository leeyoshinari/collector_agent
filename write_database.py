#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import time
import json
import queue
import traceback
from concurrent.futures import ThreadPoolExecutor

import redis
import requests
import influxdb
from common import get_ip, logger, get_configure


class WriterDB(object):
    def __init__(self):
        self._redis_data = None
        self._influx_line = None
        self.IP = get_ip()
        self.thread_pool = int(get_configure('threadPool')) if int(get_configure('threadPool')) > 0 else 1

        self.influx_host = '127.0.0.1'
        self.influx_port = 8086
        self.influx_username = 'root'
        self.influx_password = '123456'
        self.influx_database = 'test'
        self.redis_host = '127.0.0.1'
        self.redis_port = 6379
        self.redis_password = '123456'
        self.redis_db = 0
        self.deploy_path = ''

        self.get_config_from_server()
        self.writer_task = queue.Queue()   # FIFO queue
        self.executor = ThreadPoolExecutor(self.thread_pool)
        self.influx_client = influxdb.InfluxDBClient(self.influx_host, self.influx_port, self.influx_username,
                                              self.influx_password, self.influx_database)
        self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_password,
                                        db=self.redis_db, decode_responses=True)

        self.writer()

    @property
    def influx_line(self):
        return self._influx_line

    @influx_line.setter
    def influx_line(self, value):
        self.writer_task.put((self.write_influx, value))

    @property
    def redis_data(self):
        return self._redis_data

    @redis_data.setter
    def redis_data(self, value):
        self.writer_task.put((self.write_redis, value))

    def worker(self):
        """
        Get data from the queue and run func
        :return:
        """
        while True:
            func, param = self.writer_task.get()
            func(param)
            self.writer_task.task_done()

    def writer(self):
        """
        start multiple threads
        :return:
        """
        for i in range(self.thread_pool):
            self.executor.submit(self.worker)

    def write_redis(self, data: list):
        """
        :param data: list, [key: str, value: str, expire_time: int (seconds)]
        :return:
        """
        try:
            self.redis_client.set(name=data[0], value=data[1], ex=data[2])
            logger.debug(f'write redis success: {data}')
        except:
            logger.error(data)
            logger.error(traceback.format_exc())

    def write_influx(self, line):
        """
        :param line:
        :return:
        """
        try:
            self.influx_client.write_points(line)
            logger.debug(f'write influx success: {line}')
        except:
            logger.error(line)
            logger.error(traceback.format_exc())

    def get_config_from_server(self):
        url = f'http://{get_configure("address")}/register/first'
        header = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json; charset=UTF-8"}
        post_data = {
            'host': self.IP,
            'port': get_configure('port')
        }

        while True:
            try:
                res = requests.post(url=url, json=post_data, headers=header)
                logger.info(f"The result of registration is {res.content.decode('unicode_escape')}")
                if res.status_code == 200:
                    response_data = json.loads(res.content.decode('unicode_escape'))
                    if response_data['code'] == 0:
                        self.influx_host = response_data['data']['influx']['host']
                        self.influx_port = response_data['data']['influx']['port']
                        self.influx_username = response_data['data']['influx']['username']
                        self.influx_password = response_data['data']['influx']['password']
                        self.influx_database = response_data['data']['influx']['database']
                        self.redis_host = response_data['data']['redis']['host']
                        self.redis_port = response_data['data']['redis']['port']
                        self.redis_password = response_data['data']['redis']['password']
                        self.redis_db = response_data['data']['redis']['db']
                        self.deploy_path = response_data['data']['deploy_path']
                        break
                    else:
                        logger.error(response_data['msg'])
                        raise Exception(response_data['msg'])

                time.sleep(1)

            except(Exception):
                logger.error(traceback.format_exc())
                time.sleep(1)

    def __del__(self):
        del self.redis_client, self.influx_client


def notification(msg):
    """
     Send email.
    :param msg: Email body
    :return:
    """
    url = f'http://{get_configure("address")}/monitor/register/notification'

    header = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json; charset=UTF-8"}

    post_data = {
        'host': get_ip(),
        'msg': msg
    }

    logger.debug(f'The content of the email is {msg}')

    res = requests.post(url=url, json=post_data, headers=header)
    if res.status_code == 200:
        response = json.loads(res.content.decode())
        if response['code'] == 0:
            logger.info('Send email successfully.')
        else:
            logger.error(response['msg'])
    else:
        logger.error('Failed to send mail.')
