import ollama
import re
import json
import os
from prompts import SUBJECT_SYSTEM_PROMPT

class ChatClient:
    def __init__(self, model=None, system_prompt=None):
        self.config = self._load_config()
        self.model = model or self.config.get("model", "sam860/lfm2.5:1.2b")
        self.system_prompt = system_prompt
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def _load_config(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json: {e}")
        return {}

    def clean_text(self, text):
        # Remove Markdown bold/italic symbols
        text = text.replace("**", "").replace("*", "")
        # Remove emojis using regex
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        return text.strip()

    def set_system_prompt(self, level, subject):
        self.system_prompt = SUBJECT_SYSTEM_PROMPT.format(level=level, subject=subject)
        self.clear_history()

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
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})
