#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import time
import json
import queue
import traceback
from concurrent.futures import ThreadPoolExecutor

import redis
import influxdb
from common import get_ip, logger, get_configure, http_post


class WriterDB(object):
    def __init__(self):
        self.influx_stream = 'influx_stream'  # stream name
        self.group_name = 'my_group'  # consumer group name
        self._redis_data = None
        self._influx_line = None
        self._influx_batch = []
        self._jmeter_agent = {}     # exclusively for jmeter-agent
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
        pool = redis.ConnectionPool(host=self.redis_host, port=self.redis_port, password=self.redis_password,
                                    db=self.redis_db, decode_responses=True, max_connections=10)
        self.redis_client = redis.StrictRedis(connection_pool=pool)
        groups_info = self.redis_client.xinfo_groups(name=self.influx_stream)
        if not groups_info:
            self.redis_client.xgroup_create(name=self.influx_stream, groupname=self.group_name, mkstream=True)

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

    @property
    def jmeter_agent(self):
        return self._jmeter_agent

    @jmeter_agent.setter
    def jmeter_agent(self, value):
        self.writer_task.put((self.deal_jmeter_agent, value))

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
        self.executor.submit(self.subscribe)
        for i in range(self.thread_pool-1):
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
        finally:
            del data

    def subscribe(self):
        while True:
            try:
                messages = self.redis_client.xreadgroup(groupname=self.group_name, consumername=self.IP,
                                                        streams={self.influx_stream: '>'}, count=10, block=900000000)
                logger.debug(messages)
                for stream, message in messages.items():
                    logger.debug(message)
                    for message_id, message_data in message:
                        self.write_influx(message_data)
                        self.redis_client.xack(self.influx_stream, self.IP, message_id)
            except:
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

    def deal_jmeter_agent(self, data):
        try:
            logger.debug(data)
            self.influx_client.write_points(data['influx'])
            total_num = len(self.redis_client.keys(data['num_key']))
            if self.redis_client.llen(data['data_key']) >= total_num:
                res = self.redis_client.lrange(data['data_key'], 0, total_num - 1)
                self.redis_client.ltrim(data['data_key'], total_num + 1, total_num + 1)  # remove all
                self.write_jmeter_agent_data_to_influx(data['task_id'], res)
            _ = self.redis_client.lpush(data['data_key'], str(data['redis']))
            if self.redis_client.llen(data['data_key']) >= total_num:
                res = self.redis_client.lrange(data['data_key'], 0, total_num - 1)
                self.redis_client.ltrim(data['data_key'], total_num + 1, total_num + 1)  # remove all
                self.write_jmeter_agent_data_to_influx(data['task_id'], res)
            self.redis_client.expire(data['data_key'], 180)
        except:
            logger.error(data)
            logger.error(traceback.format_exc())
        finally:
            del data

    def get_redis_keys(self, key):
        try:
            return self.redis_client.keys(key)
        except:
            logger.error(traceback.format_exc())
            raise

    def get_redis_value(self, key):
        try:
            return self.redis_client.get(key)
        except:
            logger.error(traceback.format_exc())
            raise

    def get_config_from_server(self):
        url = f'http://{get_configure("address")}/register/first'
        post_data = {'host': self.IP, 'port': get_configure('port')}

        while True:
            try:
                res = http_post(url, post_data)
                logger.info(f"The result of registration is {res}")
                self.influx_host = res['influx']['host']
                self.influx_port = res['influx']['port']
                self.influx_username = res['influx']['username']
                self.influx_password = res['influx']['password']
                self.influx_database = res['influx']['database']
                self.redis_host = res['redis']['host']
                self.redis_port = res['redis']['port']
                self.redis_password = res['redis']['password']
                self.redis_db = res['redis']['db']
                self.deploy_path = res['deploy_path']
                break
            except:
                logger.error(traceback.format_exc())
                time.sleep(1)

    def write_jmeter_agent_data_to_influx(self, task_id, datas):
        d = [json.loads(r) for r in datas]
        data = [r for r in zip(*d)]
        logger.debug(data)
        total_sample = sum(data[0])
        rt = sum([x * y / total_sample for x, y in zip(data[0], data[2])])
        line = [{'measurement': 'performance_jmeter_task',
                 'tags': {'task': task_id, 'host': 'all'},
                 'fields': {'c_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'samples': total_sample, 'tps': sum(data[1]),
                            'avg_rt': rt, 'min_rt': min(data[3]), 'max_rt': max(data[4]), 'err': sum(data[5]),
                            'active': sum(data[6])}}]
        self.influx_client.write_points(line)
        del task_id, datas, data, d, total_sample, rt, line

