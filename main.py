# -*- coding: utf-8 -*-
import os
from wxauto import WeChat
from wxauto import WxParam
from wxauto.msgs import FriendMessage
from logger import logger
from weather import handle_weather_query
from checkin import handle_checkin
from config import GROUPS_TO_LISTEN
from PyQt5.QtCore import pyqtSignal, QObject
from openai import OpenAI  

wx = WeChat()

# 初始化 DeepSeek 客户端
# client = OpenAI(
#     api_key="sk-80bad6b1e6064f1f97a59210163870a5",  # 替换为你的 DeepSeek API Key
#     base_url="https://api.deepseek.com"
# )
client = OpenAI(
    api_key="36791800-dcb6-4521-8df6-6bd6376780df",
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
    # api_key="36791800-dcb6-4521-8df6-6bd6376780df",  # 替换为你的 DeepSeek API Key
    # base_url="https://ark.cn-beijing.volces.com/api/v3"
)


class MessageHandler(QObject):
    
    message_received = pyqtSignal(object, object)  # msg, chat
    WxParam.FORCE_MESSAGE_XBIAS = True  # 获取分辨率缩放

    def __init__(self):
        super().__init__()

    def handle(self, msg, chat):
        logger.info(f"📩 收到消息事件：{msg.content} 来自 {chat.who}")
        self.message_received.emit(msg, chat)
        logger.debug("🔔 已触发 message_received.emit()")

        if isinstance(msg, FriendMessage):
            # if '天气' in msg.content:
                # handle_weather_query(msg, chat)
            if msg.content == '打卡':
                logger.debug("🛠️ 正在执行打卡功能")
                handle_checkin(msg, chat)
                
            elif  msg.content == '打卡日历':
                wx.SendFiles(filepath="C:/Users/Administrator/Desktop/July.jpg", who=chat.who, exact=False)

            elif '@nuomy' in msg.content:
                # 示例1：将消息记录到本地文件
                # response = client.chat.completions.create(
                # # model="deepseek-reasoner",
                # model="doubao-seed-1-6-flash-250615",
                # # model="bot-20250708154930-zdw5d",
                # messages=[
                #     {"role": "system", "content": "你是一只人工智能小猫，请用简洁的语言回答问题"},
                #     {"role": "user", "content": msg.content},
                # ],
                # # stream=False
                # )
                response = client.chat.completions.create(
                model="bot-20250708154930-zdw5d",  # bot-20250708154930-zdw5d 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
                messages=[
                    {"role": "system", "content": "你是一只人工智能小猫，请用简洁的语言回答问题"},
                    {"role": "user", "content": msg.content},
                ],
                )
                # R1
                # print(response.choices[0].message.content)
                # if hasattr(response, "references"):
                #     print(response.references)
                # if hasattr(response.choices[0].message, "reasoning_content"):
                #     print(response.choices[0].message.reasoning_content)
                # V3
                print(response.choices[0].message.content)
                if hasattr(response, "references"):
                    print(response.references)
                

                # ai_response = response.choices[0].message.content
                ai_response = response.choices[0].message.content

                logger.info(f"🤖 AI 回复：{ai_response}")
                msg.reply(ai_response)  # 使用 wxauto 的 SendMsg 方法发送回复

            else:    
                
                with open('msgs.txt', 'a', encoding='utf-8') as f:
                    f.write(msg.content + '\n')

message_handler = MessageHandler()