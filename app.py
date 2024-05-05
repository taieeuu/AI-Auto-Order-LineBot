# coding:utf-8
import json
from flask import Flask, request, abort, jsonify, make_response
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, QuickReply, QuickReplyButton, MessageAction
import _G
import ast
import re
from _G import log_debug, log_info, log_error, log_warning
import tempfile, os
from datetime import datetime, timedelta
import openai
import time
import traceback
from openai_manager import OpenAIManager
from utils import get_menu_text, limit_tokens, trim_messages
from mongo_manager import MongoDBManager

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

openai_manager = OpenAIManager()
mongo_manager = MongoDBManager(os.getenv('MONGODB_URI'), os.getenv('MONGODB_DB_NAME'))



def init():
    try:
        # 創建建菜單消息
        _G.menu_message = TemplateSendMessage(
            alt_text='Menu',
            template=ButtonsTemplate(
                title='Menu',
                text='Just item:',
                actions=[
                    PostbackTemplateAction(
                        label=f"{item} - {price['價格']}元",
                        data=f'item={item}'
                    ) for item, price in _G.menu.items()
                ]
            )
        )
        log_info("_G.menu",_G.menu)
        get_menu_text()
    except Exception as e:
        log_error(f"Error creating menu message: {e}")

def parse_order(text):
    # 提取姓名
    customer_name = re.search('姓名:(.*?)品項:', text).group(1).strip()
    
    # 移除姓名部分，仅保留品項和備註
    items_with_notes_text = text.split('品項:', 1)[1].strip()

    # 使用正则表达式匹配所有品项和数量
    items = re.findall('([^\s,]+):(\d+)', items_with_notes_text)

    order_details = []
    for i in range(len(items)):
        item_name, quantity = items[i]
        # 備註是当前品项与下一个品项之间的文本
        if i < len(items) - 1:
            # 查找当前品项结束位置到下一个品项开始位置之间的文本
            start_pos = items_with_notes_text.find(items[i][0] + ':' + items[i][1]) + len(items[i][0] + ':' + items[i][1])
            end_pos = items_with_notes_text.find(items[i + 1][0] + ':' + items[i + 1][1])
            note = items_with_notes_text[start_pos:end_pos-1].replace('備註:', '').strip()
        else:
            # 最后一个品项，其備註直到字符串末尾
            start_pos = items_with_notes_text.find(items[i][0] + ':' + items[i][1]) + len(items[i][0] + ':' + items[i][1])
            note = items_with_notes_text[start_pos:].replace('備註:', '').strip()

        # 假设每个品项的名字都对应到menu中的一个项
        if item_name in _G.menu and quantity.isdigit():
            order_details.append({
                "item": item_name,
                "quantity": int(quantity),
                "price": _G.menu[item_name]["價格"] * int(quantity),
                "note": note
            })

    return customer_name, order_details

def cleanup_inactive_users(minutes):
    inactive_threshold = timedelta(minutes=minutes)  # 设置不活跃的阈值，例如30分钟
    current_time = datetime.now()
    inactive_users = [user_id for user_id, last_active in _G.user_last_active.items() if current_time - last_active > inactive_threshold]
    
    for user_id in inactive_users:
        # 清理不活跃用户的消息列表和最后活动时间戳
        if user_id in _G.user_messages:
            del _G.user_messages[user_id]
        if user_id in _G.user_last_active:
            del _G.user_last_active[user_id]

def process_order(event, customer_name, orders):
    """Process and record the order."""
    total_price = sum(order["price"] for order in orders)
    order_summary = "\n".join(f"{order['item']} x {order['quantity']} = {order['price']}元" for order in orders)
    order_data = {"user_id": event.source.user_id, "user_name": customer_name, "items": orders, "total_price": total_price}
    mongo_manager.insert_document(os.getenv('MONGODB_COLLECTION_USER_MESSAGES'), order_data)
    # orders_collection.insert_one(order_data)
    message = TextSendMessage(text=f"{customer_name}，已收到您的訂單，總金額：{total_price}元\n\n{order_summary}")
    line_bot_api.reply_message(event.reply_token, message)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return make_response('', 200)

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    '''deal with user message'''
    user_id = event.source.user_id
    _G.user_last_active[user_id] = datetime.now()  # 更新用户的最后活动时间
    cleanup_inactive_users(10)  # 在添加新消息之前，检查是否有不活跃的用户需要清理
    
    if user_id not in _G.user_messages:
        openai_system_setting = os.getenv('OPENAI_SYSTEM_SETTING')
        OPENAI_SYSTEM_SETTING = openai_system_setting.format(menu_items=_G.menu_items)
        _G.user_messages[user_id] = [{"role": "system", "content": OPENAI_SYSTEM_SETTING}]
    
    _G.user_messages[user_id] = trim_messages(_G.user_messages.get(user_id, []))
    _G.user_messages[user_id] = limit_tokens(_G.user_messages[user_id])

    if event.message.text == "菜單":  # 如果接收到的消息是 "菜單"，則向用戶發送菜單訊息
        log_info("菜單")
        line_bot_api.reply_message(event.reply_token, _G.menu_message)
    else:
        print({"role": "user", "content": event.message.text})
        _G.user_messages[user_id].append({"role": "user", "content": event.message.text})
        response = openai_manager._get_chat_completion(_G.user_messages[user_id])
        print("response",response)
        print("user_messages: ",_G.user_messages[user_id])
        # 在处理特定命令之前更新对话历史
        _G.user_messages[user_id].append({"role": "assistant", "content": response["content"]})

        # 检查是否包含訂餐命令
        if "/訂餐" in response["content"]:
            command_text = response["content"].split("/訂餐")[1]  # 获取命令之后的文本部分
            customer_name, orders = parse_order(command_text)
            if orders:
                process_order(event, customer_name, orders)
                return  # 完成訂單处理后返回，已经更新了對話歷史
            else:
                message = TextSendMessage(text="很抱歉，無法處理您的訂單")
                line_bot_api.reply_message(event.reply_token, message)

        if  response.get("need_user_trigger"):
            # 如果需要用户操作来继续，发送回复和“继续”按钮
            send_reply_with_quick_reply(event.reply_token, response["content"])
        else:
            # 如果不需要进一步操作，只发送文本回复
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response["content"]))

def send_reply_with_quick_reply(reply_token, text, button_label="繼續", button_data="繼續"):
    messages = TextSendMessage(
        text=text,
        quick_reply=QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label=button_label, text=button_data)
                )
            ]
        )
    )
    line_bot_api.reply_message(reply_token, messages)
    
if __name__ == '__main__':
    init()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
