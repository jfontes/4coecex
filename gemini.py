from google import genai
from google.genai import types
from config import GEMINI_API_KEY
import tempfile, os, time, json
from typing import List
from pydantic import BaseModel

class CargoFundamento(BaseModel):
    Cargo: str
    Fundamento_legal: str

class Gemini:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.api_key = GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("A chave GOOGLE_API_KEY não está definida.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = model_name

    def get(self, conteudo: str, pergunta: str) -> str:
        prompt = [
            {"role": "user", "parts": [{"text": str(conteudo)}]},
            {"role": "user", "parts": [{"text": pergunta}]},
        ]
        tentativas = 5
        for t in range(tentativas):
            print(f"------------------INICIANDO TENTATIVA {t+1}/{tentativas}------------------")
            try:
                resposta = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                return resposta.text
            except Exception as e:
                print(e.message)
                time.sleep(2 ** t)
        print(e.message)
        raise ValueError(f"Tentativas esgotadas, IA sobrecarregada.")
        
    def getAnalise(self, parts: List[types.Part], pergunta: str) -> str:
        tentativas = 5
        for t in range(tentativas):
            print(f"------------------INICIANDO TENTATIVA {t+1}/{tentativas}------------------")
            try:
                resposta = self.client.models.generate_content(
                    model=self.model,
                    contents=[parts, pergunta],
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                return resposta.text
            except Exception as e:
                print(e.message)
                time.sleep(2 ** t)
        print(e.message)
        raise ValueError(f"Tentativas esgotadas, IA sobrecarregada.")

    def lerPDF(self, files) -> List[types.Part]:
        """
        Converte uma lista de arquivos PDF (FileStorage) em uma lista de `types.Part` para a API Gemini.
        Usa arquivos temporários que são limpos automaticamente.
        """
        parts = []
        for pdf in files:
            try:
                # O arquivo temporário é excluído automaticamente ao sair do bloco 'with'
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    pdf.save(tmp.name)
                    #tmp.seek(0) # Volta ao início do arquivo para leitura
                    #part = types.Part.from_bytes(data=tmp.read_bytes(), mime_type="application/pdf")
                    parts.append(types.Part.from_bytes(data=tmp.read(), mime_type="application/pdf"))
            except Exception as e:
                raise IOError(f"Falha ao ler o arquivo PDF '{pdf.filename}': {e}")
            finally:
                try:
                    os.remove(tmp.name)
                except Exception:
                    pass
        return parts
        
    
    def extrairCargoFundamentoLegal(self, conteudo: str) -> dict:
        prompt = [
            {"role": "user", "parts": [{"text": str(conteudo)}]},
            {"role": "user", "parts": [{"text": "Extraia o cargo e o fundamento legal considerando: Cargo da pessoa (somente o nome, classe e referência, sem comentários) e Fundamento legal contendo todos os artigos e leis que fundamentam o registro (sem qualquer outro comentário)."}]},
        ]
        tentativas = 5
        for t in range(tentativas):
            print(f"------------------INICIANDO TENTATIVA {t+1}/{tentativas}------------------")
            try:
                resposta = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "response_schema": CargoFundamento,
                        },
                )
                r = json.loads(resposta.text)
                cargo_fundamento = []
                cargo_fundamento.append(r.get("Cargo") or "")
                cargo_fundamento.append(r.get("Fundamento_legal") or "")
                return cargo_fundamento
            except Exception as e:
                print(e.message)
                time.sleep(2 ** t)
        print(e.message)
        raise ValueError(f"Tentativas esgotadas, IA sobrecarregada.")
