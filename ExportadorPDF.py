import os
import subprocess
from config import LIBREOFFICE_PATH

class ExportadorPDF:
    def __init__(self, caminho_modelo_docx: str):
        self.modelo_docx = caminho_modelo_docx

    def gerar_pdf(self, caminho_docx_temp: str) -> str:
        # A exceção agora será capturada aqui, dentro do método.
        try:
            pasta = os.path.dirname(caminho_docx_temp)
            
            # Chamamos a função de conversão. 
            # Se ela falhar, vai levantar um RuntimeError com detalhes.
            pdf_path = convert_with_libreoffice(caminho_docx_temp, pasta)
            
            # Verificação extra: confirma se o arquivo PDF realmente foi criado.
            if not os.path.exists(pdf_path):
                raise RuntimeError(f"A conversão foi concluída sem erros, mas o arquivo PDF não foi encontrado em '{pdf_path}'. Verifique as permissões da pasta temporária.")

            return pdf_path

        except Exception as e:
            # Re-levanta a exceção para que o Flask a capture e mostre o erro detalhado.
            raise RuntimeError(f"Erro detalhado ao tentar gerar o PDF: {e}")


def convert_with_libreoffice(input_file: str, output_folder: str) -> str:
    """
    Converte um arquivo .docx para .pdf chamando o LibreOffice diretamente,
    que é a abordagem mais estável para Windows.
    """
    try:
        # Caminho para o executável principal do LibreOffice
        soffice_path = LIBREOFFICE_PATH

        # Comando para conversão direta
        command = [
            soffice_path,
            '--headless',      # Executa sem interface gráfica
            '--convert-to', 'pdf',
            '--outdir', output_folder, # Pasta onde o PDF será salvo
            input_file         # Arquivo de entrada .docx
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if process.returncode != 0:
            error_message = (
                f"A conversão direta com LibreOffice falhou com o código {process.returncode}.\n"
                f"--- Comando ---\n{' '.join(command)}\n"
                f"--- Erro (stderr) ---\n{process.stderr}\n"
                f"--- Saída (stdout) ---\n{process.stdout}"
            )
            raise RuntimeError(error_message)
        
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        expected_pdf_path = os.path.join(output_folder, f"{base_name}.pdf")
        return expected_pdf_path

    except FileNotFoundError:
        raise RuntimeError(f"O executável do LibreOffice não foi encontrado em '{soffice_path}'. Verifique o caminho.")
    except Exception as e:
        raise e