import ollama
import re
from prompts import SYSTEM_PROMPT

class ChatClient:
    def __init__(self, model="sam860/lfm2.5:1.2b"):
        self.model = model
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def clean_text(self, text):
        # Remove Markdown bold/italic symbols
        text = text.replace("**", "").replace("*", "")
        # Remove emojis using regex
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        return text.strip()

    def get_initial_greeting(self):
        try:
            response = ollama.chat(model=self.model, messages=self.messages)
            bot_message = self.clean_text(response["message"]["content"])
            self.messages.append({"role": "assistant", "content": bot_message})
            return bot_message
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def get_response(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(model=self.model, messages=self.messages)
            bot_message = self.clean_text(response["message"]["content"])
            self.messages.append({"role": "assistant", "content": bot_message})
            return bot_message
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def clear_history(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
