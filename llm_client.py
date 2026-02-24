import requests
import json
import os

class GeminiClient:
    def __init__(self, api_key, model="gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate(self, prompt, system_instruction=None):
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_instruction:
            payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

        response = requests.post(self.url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return f"Error parsing response: {result}"
        return f"API Error: {response.status_code} - {response.text}"

class DeepSeekClient:
    def __init__(self, api_key, model="deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.deepseek.com/chat/completions"

    def generate(self, prompt, system_instruction=None):
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        return f"DeepSeek API Error: {response.status_code} - {response.text}"
