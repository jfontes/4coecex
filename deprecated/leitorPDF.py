import pdfplumber
import easyocr
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import os, logging, tempfile

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("leitor_pdf.log"),
        logging.StreamHandler()
    ]
)

class LeitorPDF:
    def __init__(self):
        logging.info("Inicializando LeitorPDF")

    def __is_scanned_pdf(self, caminho_pdf):
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                text = ''.join(page.extract_text() or '' for page in pdf.pages)
            is_scanned = len(text.strip()) == 0
            logging.info(f"PDF {'escaneado' if is_scanned else 'digital'} detectado.")
            return is_scanned
        except Exception as e:
            logging.error(f"Erro ao verificar se o PDF é escaneado: {e}")
            raise

    def __extract_text_with_easyocr(self, caminho_pdf):
        try:
            doc = fitz.open(caminho_pdf)
            reader = easyocr.Reader(['pt'])
            texto = ''
            for i, page in enumerate(doc):
                logging.info(f"Processando página {i+1} com OCR...")
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                results = reader.readtext(np.array(img))
                texto += '\n'.join([res[1] for res in results]) + '\n'
            logging.info("Extração com OCR concluída.")
            return texto
        except Exception as e:
            logging.error(f"Erro na extração com EasyOCR: {e}")
            raise

    def extrair_texto(self, caminho_pdf):
        if not os.path.exists(caminho_pdf):
            logging.error("Arquivo não encontrado.")
            raise FileNotFoundError("Arquivo não encontrado.")

        try:
            if self.__is_scanned_pdf(caminho_pdf):
                return self.__extract_text_with_easyocr(caminho_pdf)
            else:
                with pdfplumber.open(caminho_pdf) as pdf:
                    texto = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
                logging.info("Extração de texto digital concluída.")
                return texto
        except Exception as e:
            logging.error(f"Erro ao extrair texto do PDF: {e}")

    def extrair_textos(self, files):
        textos = []
        for storage in files:
            # salva temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                storage.save(tmp.name)
                tmp_path = tmp.name

            try:
                txt = None
                # tenta usar LeitorPDF se existir no projeto
                try:
                    # ajuste conforme a sua classe (método estático ou instância)
                    txt = self.extrair_texto(tmp_path)
                except Exception:
                    txt = None

                # fallback com pdfplumber
                if not txt:
                    try:
                        import pdfplumber
                        pages = []
                        with pdfplumber.open(tmp_path) as pdf:
                            for p in pdf.pages:
                                pages.append(p.extract_text() or "")
                        txt = "\n".join(pages).strip()
                    except Exception:
                        txt = ""

                textos.append(txt or "")
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        texto_final = "\n\n".join(t for t in textos if t).strip()
        if not texto_final:
            texto_final = "Nenhum texto extraído dos PDFs enviados."

        return texto_final
