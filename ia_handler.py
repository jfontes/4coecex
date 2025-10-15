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
class AnaliseInteligente(BaseModel):
    Analise: str = Field(description="A análise detalhada baseada no critério fornecido.")
    Metadado1: Optional[str] = Field(None, description="Metadado opcional 1, conforme definido no prompt.")
    Metadado2: Optional[str] = Field(None, description="Metadado opcional 2.")
    Metadado3: Optional[str] = Field(None, description="Metadado opcional 3.")

# --- Handler Específico para a OpenAI (fallback) ---
class OpenAIHandler:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def get_structured_analysis(self, b: List[bytes], prompt: str) -> dict:
        logging.warning(f"Executando fallback com o modelo OpenAI: {self.model}")

        uploaded_file_ids = []
        for pdf_bytes in b:
            file_object = self.client.files.create(
                file=("analise.pdf", pdf_bytes), # O nome do ficheiro é temporário
                purpose="user_data"
            )
            uploaded_file_ids.append(file_object.id)
            logging.info(f"Ficheiro PDF enviado para a OpenAI com o ID: {file_object.id}")
        file_references = " ".join([f"file:{file_id}" for file_id in uploaded_file_ids])            

        schema_dict = AnaliseInteligente.model_json_schema()
        # 2. Formata o dicionário como uma string JSON com indentação
        schema_json_string = json.dumps(schema_dict, indent=2, ensure_ascii=False)
            

        system_prompt = f"""Você é um assistente de análise de documentos. Analise o contexto fornecido e responda estritamente no formato JSON, seguindo o esquema: {schema_json_string}"""
        user_prompt = f"Critério de análise: '{prompt}'.\n\nContexto dos documentos:\n{file_references}"

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                temperature=0,
                text_format=AnaliseInteligente,
            )
            
            # 4. Extrai o texto da resposta e valida
            response_text = response.output_parsed
            if not response_text:
                raise ValueError("A API da OpenAI (responses) retornou uma resposta vazia.")
            
            # 5. Converte o texto JSON para um dicionário Python
            return json.loads(response_text.model_dump_json())
            
        except (APIConnectionError, RateLimitError) as e:
            logging.error(f"Erro de conexão ou limite de taxa da API OpenAI: {e}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar o JSON da OpenAI. Resposta recebida: {response_text}")
            raise ValueError("A API da OpenAI retornou um JSON inválido.") from e
        except Exception as e:
            logging.error(f"Erro inesperado na OpenAI (responses): {e}")
            raise
   
# --- Handler Específico para o Gemini (principal) ---
class GeminiHandler:
    def __init__(self, client: genai.Client, model: str):
        self.client = client
        self.model = model

    def get_structured_analysis(self, b: List[bytes], prompt: str) -> dict:
        tentativas = 4
        for t in range(tentativas):
            logging.warning(f"------------------API Gemini: Iniciando tentativa {t+1}/{tentativas} com o modelo {self.model}.------------------")

            parts = []
            for pdf_bytes in b:
                parts.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))

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
        raise

# --- Classe Principal do Orquestrador ---
class GenerativeAI:
    def __init__(self):
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.gemini_handler = GeminiHandler(self.gemini_client, "gemini-2.5-flash")

        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.openai_handler = OpenAIHandler(self.openai_client, "gpt-4o-mini")

    def get_structured_analysis(self, b: List[bytes], prompt: str) -> dict:
        """
        Tenta gerar uma análise estruturada usando os modelos Gemini.
        Se todos falharem, recorre à OpenAI como fallback.
        """
        # 1. Tentar com o handler do Gemini
        try:
            result = self.gemini_handler.get_structured_analysis(b, prompt)
            logging.info(f"Sucesso com o modelo Gemini.")
            return result
        except:
            # 2. Se falhar, usar o fallback da OpenAI
            logging.warning(f"Ativando fallback para OpenAI.")
            try:
                result = self.openai_handler.get_structured_analysis(b, prompt)
                return result
            except Exception as e:
                logging.critical(f"FALLBACK DA OPENAI TAMBÉM FALHOU: {e}")
                # Se ambos os serviços falharem, propaga uma exceção final
                raise ValueError("Ambos os serviços de IA (Gemini e OpenAI) estão indisponíveis.") from e

    @staticmethod
    def lerPDF(files: List) -> List[bytes]:
        """
        Converte uma lista de arquivos PDF em uma lista de 'parts' para as APIs.
        Como método estático, não precisa de uma instância da classe para ser chamado.
        """
        b = []
        for pdf in files:
            try:
                # O ficheiro temporário é apagado automaticamente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    pdf.save(tmp.name)
                    # Usamos from_uri para que a biblioteca faça a gestão do ficheiro
                    #parts.append(types.Part.from_bytes(data=tmp.read(), mime_type="application/pdf"))
                    b.append(tmp.read())
            except Exception as e:
                raise IOError(f"Falha ao ler o ficheiro PDF '{pdf.filename}': {e}")
            finally:
                # Garante que o ficheiro temporário seja sempre apagado
                if 'tmp' in locals() and os.path.exists(tmp.name):
                    os.remove(tmp.name)
        return b