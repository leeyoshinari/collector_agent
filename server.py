#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: leeyoshinari

import os
import asyncio
import traceback
from aiohttp import web
from common import get_ip, logger, get_configure, http_get, http_post
from write_database import WriterDB


writer = WriterDB()
HOST = get_ip()
PID = os.getpid()
with open('pid', 'w', encoding='utf-8') as f:
    f.write(str(PID))


async def register(request):
    """
    :param request:
    :return:
    """
    try:
        data = await request.json()
        post_data = {
            'influx': {'host': writer.influx_host, 'port': writer.influx_port, 'username': writer.influx_username,
                       'password': writer.influx_password, 'database': writer.influx_database}, 'redis': {
                'host': writer.redis_host, 'port': writer.redis_port, 'password': writer.redis_password,
                'db': writer.redis_db}, 'deploy_path': writer.deploy_path}
        if data['type'] == 'monitor-agent' or data['type'] == 'nginx-agent':
            res = http_get(f"http://{get_configure('address')}/monitor/register/getinfo?host={data['host']}")
            post_data.update(res)

        return web.json_response({'code': 0, 'msg': '', 'data': post_data})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'get message failure ~'})


async def write_influx(request):
    """
    :param request:
    :return:
    """
    try:
        data = await request.json()
        writer.influx_line = data.get('data')
        del data
        return web.json_response({'code': 0, 'msg': 'Write influxDB success ~'})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Write influxDB failure ~'})


async def batch_write_influx(request):
    """
    :param request:
    :return:
    """
    try:
        data = await request.json()
        writer.influx_batch = data.get('data')
        del data
        return web.json_response({'code': 0, 'msg': 'Write influxDB success ~'})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Write influxDB failure ~'})


async def write_redis(request):
    """
    :param request:
    :return:
    """
    try:
        data = await request.json()
        writer.redis_data = data.get('data')
        del data
        return web.json_response({'code': 0, 'msg': 'Write redis success ~'})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Write redis failure ~'})

async def write_jmeter_agent(request):
    """
        :param request:
        :return:
        """
    try:
        data = await request.json()
        writer.jmeter_agent = data
        del data
        return web.json_response({'code': 0, 'msg': 'Write success ~'})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Write jmeter-agent failure ~'})


async def get_redis_keys(request):
    """
    :param request:
    :return:
    """
    try:
        key = request.match_info['key']
        num = int(request.match_info['num'])
        keys = writer.get_redis_keys(key.strip())
        if num == 1:
            return web.json_response({'code': 0, 'msg': 'success', 'data': len(keys)})
        else:
            return web.json_response({'code': 0, 'msg': 'success', 'data': keys})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Get redis key failure ~'})

async def get_redis_value(request):
    """
    :param request:
    :return:
    """
    try:
        key = request.match_info['key']
        value = writer.get_redis_value(key.strip())
        return web.json_response({'code': 0, 'msg': 'success', 'data': value})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'Get redis key failure ~'})

async def set_message(request):
    """
    :param request:
    :return:
    """
    try:
        data = await request.json()
        url = f'http://{get_configure("address")}/performance/task/register/getMessage'
        _ = http_post(url, data)
        del data
        return web.json_response({'code': 0, 'msg': 'success ~'})
    except:
        logger.error(traceback.format_exc())
        return web.json_response({'code': 1, 'msg': 'failure ~'})


async def main():
    app = web.Application()

    app.router.add_route('POST', '/redis/write', write_redis)
    app.router.add_route('POST', '/influx/write', write_influx)
    app.router.add_route('POST', '/influx/batch/write', batch_write_influx)
    app.router.add_route('POST', '/jmeter/agent/write', write_jmeter_agent)
    app.router.add_route('POST', '/register', register)
    app.router.add_route('POST', '/setMessage', set_message)
    app.router.add_route('GET', '/redis/get/keys/{key}/{num}', get_redis_keys)
    app.router.add_route('GET', '/redis/get/{key}', get_redis_value)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, get_configure('port'))
    await site.start()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
