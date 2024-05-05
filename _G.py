from datetime import datetime

VERSION = "0.1.0"

menu = {
  "薯條": {"價格": 30, "食材": "馬鈴薯"},
  "漢堡": {"價格": 50, "食材": "和牛、洋蔥、青菜"},
  "可樂": {"價格": 20, "食材": "可口可樂"}
}

user_messages = {}

menu_items = None

openai_agent = None

menu_message = None

MAX_MESSAGES = 15  # 最大消息數量
MAX_TOKENS = 512  # 最大 token 數量

#最后活動的时间戳
user_last_active = {}

# 0: None, 1: +Error, 2: +Warning, 3: +Info, 4: +Debug
VerboseLevel = 4

def format_curtime():
  return datetime.strftime(datetime.now(), '%H:%M:%S')

def log_error(*args, **kwargs):
  if VerboseLevel >= 1:
    print(f"[{format_curtime()}] [ERROR]:", *args, **kwargs)

def log_warning(*args, **kwargs):
  if VerboseLevel >= 2:
    print(f"[{format_curtime()}] [WARNING]:", *args, **kwargs)

def log_info(*args, **kwargs):
  if VerboseLevel >= 3:
    print(f"[{format_curtime()}] [INFO]:", *args, **kwargs)

def log_debug(*args, **kwargs):
  if VerboseLevel >= 4:
    print(f"[{format_curtime()}] [DEBUG]:", *args, **kwargs)