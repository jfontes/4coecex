from docx2pdf import convert
import os

class ExportadorPDF:
    def __init__(self, caminho_modelo_docx: str):
        self.modelo_docx = caminho_modelo_docx

    def gerar_pdf(self, caminho_docx_temp: str) -> str:
        if not os.path.exists(caminho_docx_temp):
            raise FileNotFoundError("DOCX de entrada não encontrado.")
        pasta = os.path.dirname(caminho_docx_temp)
        nome = os.path.splitext(os.path.basename(caminho_docx_temp))[0] + ".pdf"
        pdf_path = os.path.join(pasta, nome)
        convert(caminho_docx_temp, pdf_path)
        if not os.path.exists(pdf_path):
            raise RuntimeError("Falha na conversão DOCX→PDF.")
        return pdf_path
