import os
import google.generativeai as genai
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.api_key = GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("A chave GOOGLE_API_KEY não está definida.")
        self.model_name = model_name
        self._configurar()

    def _configurar(self):
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def get(self, conteudo: str, pergunta: str) -> str:
        prompt = [
            {"role": "user", "parts": [{"text": str(conteudo)}]},
            {"role": "user", "parts": [{"text": pergunta}]},
        ]
        try:
            resposta = self.model.generate_content(prompt)
            return resposta.text
        except Exception as e:
            print(f"Erro ao gerar resposta: {e}")
            return ""
