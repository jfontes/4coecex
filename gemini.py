from google import genai
from google.genai import types
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("A chave GOOGLE_API_KEY não está definida.")
        self.model_name = model_name

    def get(self, conteudo: str, pergunta: str) -> str:
        prompt = [
            {"role": "user", "parts": [{"text": str(conteudo)}]},
            {"role": "user", "parts": [{"text": pergunta}]},
        ]
        try:
            client = genai.Client(api_key=self.api_key)
            resposta = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            return resposta.text
        except Exception as e:
            raise ValueError(f"Erro ao gerar resposta: {e}")
