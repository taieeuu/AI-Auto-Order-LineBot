from openai import OpenAI
import os
from dotenv import load_dotenv
import _G

load_dotenv()

class OpenAIManager:
  def __init__(self):
    self.api_key = os.getenv("OPENAI_API_KEY")
    self.clientOpenAI = OpenAI(api_key=self.api_key)

  def _get_chat_completion(self, messages):  # Add 'self' here and make sure 'messages' is a list
    try:
      response = self.clientOpenAI.chat.completions.create(
        messages=messages,  # Ensure 'messages' is a list of dicts
        model="gpt-4-turbo-preview",
        max_tokens=int(_G.MAX_TOKENS/2),
      )
      part_response = response.choices[0].message.content
      finish_reason = response.choices[0].finish_reason

      need_user_trigger = finish_reason not in ["stop", "eos"]
      return {"content": part_response, "need_user_trigger": need_user_trigger}
    except Exception as e:
      return {"error": str(e), "need_user_trigger": False}

if __name__ == "__main__":
  openai_manager = OpenAIManager()
  messages = ["Hello, how can I help you?"]
  response = openai_manager._get_chat_completion(messages)  # Pass 'messages' as a list
  print(response)
