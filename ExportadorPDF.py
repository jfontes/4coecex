from docx2pdf import convert
import os

class ExportadorPDF:
    def __init__(self, caminho_modelo_docx: str):
        self.modelo_docx = caminho_modelo_docx

    def gerar_pdf(self, caminho_docx_temp: str) -> str:
        try:
            pasta = os.path.dirname(caminho_docx_temp)
            nome = os.path.splitext(os.path.basename(caminho_docx_temp))[0] + ".pdf"
            pdf_path = os.path.join(pasta, nome)
            convert(caminho_docx_temp, pdf_path)
            return pdf_path
        except FileNotFoundError as e:
            raise RuntimeError(f"Arquivo não encontrado: {e}")
        except RuntimeError as e:
            raise RuntimeError(f"Erro de execução: {e}")
        except Exception as e:
            raise RuntimeError(f"Erro inesperado ao gerar PDF: {e}")
