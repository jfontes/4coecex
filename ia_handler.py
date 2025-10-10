import logging
import os, tempfile, time
import json
from dataclasses import dataclass, field
from typing import List
from google import genai
from google.api_core import exceptions as google_exceptions
from google.genai import types
from openai import OpenAI, APIConnectionError, RateLimitError
from config import GEMINI_API_KEY, OPENAI_API_KEY
from pydantic import BaseModel, Field
from typing import Optional

# --- Definição do Esquema de Resposta ---
# (Movido de gemini.py para cá para ser usado por ambos os handlers)
class AnaliseInteligente(BaseModel):
    Analise: str = Field(description="A análise detalhada baseada no critério fornecido.")
    Metadado1: Optional[str] = Field(None, description="Metadado opcional 1, conforme definido no prompt.")
    Metadado2: Optional[str] = Field(None, description="Metadado opcional 2.")
    Metadado3: Optional[str] = Field(None, description="Metadado opcional 3.")

# --- Handler Específico para a OpenAI (o nosso fallback) ---
class OpenAIHandler:
      def get_structured_analysis(self, parts: List, prompt: str) -> dict:
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

        logging.warning(f"Executando fallback com o modelo OpenAI: {self.model}")
        # Converte as 'parts' do Gemini para um formato de texto simples que o OpenAI entende
        content_str = "\n\n".join([part.text for part in parts if hasattr(part, 'text')])
        
        system_prompt = f"""Você é um assistente de análise de documentos. Analise o contexto fornecido e responda estritamente no formato JSON, seguindo o esquema: {AnaliseInteligente.model_json_schema(indent=2)}"""
        user_prompt = f"Critério de análise: '{prompt}'.\n\nContexto dos documentos:\n{content_str}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            return json.loads(response_text)
        except (APIConnectionError, RateLimitError) as e:
            logging.error(f"Erro de conexão ou limite de taxa da API OpenAI: {e}")
            raise  # Propaga o erro para ser capturado pelo orquestrador
        except Exception as e:
            logging.error(f"Erro inesperado na OpenAI: {e}")
            raise

# --- Handler Específico para o Gemini (o nosso principal) ---
class GeminiHandler:
    def get_structured_analysis(self, parts: List, prompt: str) -> dict:
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

        logging.warning(f"Tentando com o modelo Gemini: {self.model}")
        tentativas = 7
        for t in range(tentativas):
            logging.warning(f"------------------API Gemini: Iniciando tentativa {t+1}/{tentativas} com o modelo {self.model}.------------------")
            try:
                resposta = self.client.models.generate_content(
                    model=self.model,
                    contents=[parts, prompt],
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "response_schema": AnaliseInteligente,
                        },
                )
                r = json.loads(resposta.text)

                return r
            except Exception as e:
                #Mudando o modelo para a próxima tentativa
                self.model = "gemini-2.5-pro" if self.model == "gemini-2.5-flash" else "gemini-2.5-flash"
                logging.warning(f"API Gemini: Alterando para o modelo {self.model} para a próxima tentativa")
                time.sleep(2 ** t)
        logging.error(f"API Gemini: Todas as {tentativas} tentativas falharam. A IA está sobrecarregada.")
        raise #ValueError(f"Tentativas esgotadas, IA sobrecarregada.")

# --- Classe Principal do Orquestrador ---
class GenerativeAI:
    #def __init__(self):
        #self.gemini_models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro"]
        #self.openai_fallback_model = "gpt-4o-mini"

    def get_structured_analysis(self, parts: List, prompt: str) -> dict:
        """
        Tenta gerar uma análise estruturada usando os modelos Gemini.
        Se todos falharem, recorre à OpenAI como fallback.
        """
        # 1. Tentar todos os modelos Gemini em sequência
        try:
            result = GeminiHandler().get_structured_analysis(parts, prompt)
            logging.info(f"Sucesso com o modelo Gemini.")
            return result
        except:
            # 2. Se o loop terminar sem sucesso, usar o fallback da OpenAI
            logging.warning(f"Todos os modelos Gemini falharam. Ativando fallback para OpenAI.")
            try:
                result = OpenAIHandler().get_structured_analysis(parts, prompt)
                logging.info(f"Sucesso com o fallback da OpenAI: {self.openai_fallback_model}")
                return result
            except Exception as e:
                logging.critical(f"FALLBACK DA OPENAI TAMBÉM FALHOU: {e}")
                # Se ambos os serviços falharem, propaga uma exceção final
                raise ValueError("Ambos os serviços de IA (Gemini e OpenAI) estão indisponíveis.") from e
            raise

    @staticmethod
    def lerPDF(files: List) -> List[types.Part]:
        """
        Converte uma lista de arquivos PDF em uma lista de 'parts' para as APIs.
        Como método estático, não precisa de uma instância da classe para ser chamado.
        """
        parts = []
        for pdf in files:
            try:
                # O ficheiro temporário é apagado automaticamente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    pdf.save(tmp.name)
                    # Usamos from_uri para que a biblioteca faça a gestão do ficheiro
                    parts.append(types.Part.from_bytes(data=tmp.read(), mime_type="application/pdf"))
            except Exception as e:
                raise IOError(f"Falha ao ler o ficheiro PDF '{pdf.filename}': {e}")
            finally:
                # Garante que o ficheiro temporário seja sempre apagado
                if 'tmp' in locals() and os.path.exists(tmp.name):
                    os.remove(tmp.name)
        return parts