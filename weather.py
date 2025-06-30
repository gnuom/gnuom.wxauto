# -*- coding: utf-8 -*-
import requests
from config import WEATHER_API_KEY, GEO_URL, WEATHER_URL
from logger import logger


def get_location_id(city_name):
    """通过城市名获取location ID"""
    try:
        params = {'location': city_name}
        headers = {"X-QW-Api-Key": WEATHER_API_KEY}
        response = requests.get(GEO_URL, headers=headers, params=params)
        logger.debug(f"地理查询响应状态码: {response.status_code}")
        logger.debug(f"地理查询响应内容: {response.text}")

        if response.status_code != 200:
            logger.error("地理信息查询失败")
            return None

        data = response.json()
        cities = data.get('location', [])
        if not cities:
            logger.warning(f"未找到与“{city_name}”相关的城市信息。")
            return None

        matched_city = next((c for c in cities if c['name'] == city_name), cities[0])
        return matched_city['id']
    except Exception as e:
        logger.error(f"获取location_id失败: {e}", exc_info=True)
        return None


def get_weather(location_id, city_name):
    """获取天气数据并生成回复文本"""
    try:
        params = {'location': location_id}
        headers = {"X-QW-Api-Key": WEATHER_API_KEY}
        response = requests.get(WEATHER_URL, headers=headers, params=params)
        logger.debug(f"天气API响应状态码: {response.status_code}")
        logger.debug(f"天气API响应内容: {response.text}")

        if response.status_code != 200:
            logger.error("天气接口请求失败")
            return "天气接口请求失败，请稍后再试。"

        data = response.json()
        if data.get('code') != '200':
            logger.warning(f"未找到 {city_name} 的天气信息")
            return f"未找到 {city_name} 的天气信息，请确认城市名称是否正确。"

        weather_info = data['now']
        reply = (
            f"🌤️【{city_name}天气】\n"
            f"天气状况：{weather_info['text']}\n"
            f"当前温度：{weather_info['temp']}℃\n"
            f"体感温度：{weather_info['feelsLike']}℃\n"
            f"湿度：{weather_info['humidity']}%\n"
            f"风向：{weather_info['windDir']}\n"
            f"风力等级：{weather_info['windScale']}级"
        )
        return reply
    except Exception as e:
        logger.error(f"获取天气失败: {e}", exc_info=True)
        return "获取天气信息失败，请稍后再试。"


def handle_weather_query(msg, chat):
    city_name = msg.content.replace('天气', '').strip()
    if not city_name:
        return msg.reply("请输入城市名，例如“厦门天气”")

    location_id = get_location_id(city_name)
    if not location_id:
        return msg.reply("地理信息查询失败，请稍后再试。")

    reply = get_weather(location_id, city_name)
    msg.reply(reply)