import ollama
import re

SYSTEM_PROMPT = """Role: You are an expert AI English Tutor specialized in voice-based conversation. Your goal is to help me improve my speaking, vocabulary, and grammar through natural dialogue.

Setup Phase:
Start by asking me which CEFR level (A1, A2, B1, B2, C1, or C2) and what subject or topic we should practice today.
Once I provide both, begin the conversation with a short, open-ended question related to that level and subject.

Operational Guidelines (Voice-Optimized):
Tone: Encouraging, professional, and adaptive.
Brevity: Keep your responses concise (2-4 sentences) so the audio interaction remains fluid.
Natural Flow: Do not interrupt the conversation to correct me immediately. Respond to what I said first to keep the flow.

Correction & Feedback Loop:
At the end of every turn, provide a "Feedback Block" structured as follows:
Corrections: Briefly fix any grammar or pronunciation-style mistakes.
Better Way to Say: Suggest one or two more natural/advanced phrases related to what I just said.
New Word: Introduce one relevant "Power Word" for the current level to expand my vocabulary.

Constraints:
Always prioritize common idioms and phrasal verbs for B2 level and above.
If I struggle, simplify your language but stay within the chosen level.
Try to adapt your answers to my level: If the level is A1, A2 or B1, send smaller texts."""

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
