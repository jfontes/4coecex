from docxtpl import DocxTemplate
import io, os

class PreencheDocumentoWord:
    def __init__(self, caminho_modelo:str):
        if not os.path.isfile(caminho_modelo):
            raise FileNotFoundError(f"Modelo não encontrado: {caminho_modelo}")
        self.caminho_modelo = caminho_modelo
        self._context = {}

    def substituir_campos(self, dados: dict):
        self._context = dados or {}

    def gerar_bytes(self) -> bytes:
        buffer = io.BytesIO()
        tpl = DocxTemplate(self.caminho_modelo)
        tpl.render(self._context)
        tpl.save(buffer)
        buffer.seek(0)
        return buffer.read()