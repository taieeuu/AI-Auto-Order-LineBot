import _G

def trim_messages(messages):
  """
  如果消息列表中的消息超過了最大數量，從最舊的開始刪除，直到數量符合要求。
  保留角色為 "system" 的消息。
  """
  user_messages = [msg for msg in messages if msg["role"] != "system"]
  system_messages = [msg for msg in messages if msg["role"] == "system"]
  
  while len(user_messages) + len(system_messages) > _G.MAX_MESSAGES:
    if user_messages:
      user_messages.pop(0)
    else:
      break  # 如果沒有用戶消息可以刪除，則終止循環
  
  return system_messages + user_messages

def limit_tokens(messages):
  """
  限制消息的 token 數量，如果超過最大 token 數，則從最舊的消息開始刪除，直到總 token 數量小於限制。
  """
  # 分離系統消息和用戶消息
  user_messages = [msg for msg in messages if msg["role"] != "system"]
  system_messages = [msg for msg in messages if msg["role"] == "system"]

  # 計算總令牌數
  total_tokens = sum(len(msg["content"]) for msg in user_messages)

  # 當總令牌數超過限制時，用戶消息中移除最早的消息
  while total_tokens > _G.MAX_TOKENS and len(user_messages) > 0:
    removed_message = user_messages.pop(0)
    total_tokens -= len(removed_message["content"])

  # 消息合併
  return system_messages + user_messages

def get_menu_text():
  _G.menu_items = ", ".join(_G.menu.keys())
  for dish, info in _G.menu.items():
    ingredient = info.get("食材", "未指定")
    _G.menu_items += f"\n{dish}的食材包括：{ingredient}"