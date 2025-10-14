import os
from urllib.parse import quote_plus

SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # type: ignore
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # type: ignore

# Validação das chaves de API
if not GEMINI_API_KEY:
    raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não está definida.")
if not OPENAI_API_KEY:
    raise ValueError("A variável de ambiente 'OPENAI_API_KEY' não está definida.")
    
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

# Monta o ODBC_CONNECT
odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.20.12.219;"
    "DATABASE=atos;"
    "UID=sis.atos;"
    "PWD=sisatos@TCEAC@2025;"
    "Trusted_Connection=no;"
)

ODBC_CONNECT = quote_plus(odbc_str)

SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={ODBC_CONNECT}"

SQLALCHEMY_TRACK_MODIFICATIONS = False

if not os.path.exists(LIBREOFFICE_PATH):
    # Você pode levantar um erro ou simplesmente imprimir um aviso
    print(f"AVISO: O caminho para o LibreOffice não foi encontrado em '{LIBREOFFICE_PATH}'. A conversão para PDF pode falhar.")