import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # type: ignore
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT") # type: ignore
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # type: ignore

# Validação das chaves de API
if not GOOGLE_CLOUD_PROJECT:
    raise ValueError("A variável de ambiente 'GOOGLE_CLOUD_PROJECT' não está definida.")
if not OPENAI_API_KEY:
    raise ValueError("A variável de ambiente 'OPENAI_API_KEY' não está definida.")
    
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

# Monta o ODBC_CONNECT
odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.20.12.219;"
    "DATABASE=ATOS;"
    "UID=sis.atos;"
    "PWD=sisatos@TCEAC@2025;"
    "Trusted_Connection=no;"
)

ODBC_CONNECT = quote_plus(odbc_str)

SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={ODBC_CONNECT}"

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações do Active Directory / LDAP
LDAP_DOMAIN = os.environ.get('LDAP_DOMAIN') or "tceac"
LDAP_HOST = os.environ.get('LDAP_HOST') or "172.20.12.86"
LDAP_PORT = int(os.environ.get('LDAP_PORT') or 389)
LDAP_DN = os.environ.get('LDAP_DN') or "ou=TribunalContas,dc=tceac,dc=local"
LDAP_ATTRIBUTE_FOR_USER = "sAMAccountName"
LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'false').lower() == 'true'

if not os.path.exists(LIBREOFFICE_PATH):
    # Você pode levantar um erro ou simplesmente imprimir um aviso
    print(f"AVISO: O caminho para o LibreOffice não foi encontrado em '{LIBREOFFICE_PATH}'. A conversão para PDF pode falhar.")