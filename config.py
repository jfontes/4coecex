import os, json
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # type: ignore
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT") 

PROJECT_ID = (
    os.getenv("GCP_PROJECT_ID")
    or os.getenv("GOOGLE_CLOUD_PROJECT")  # opcional: mantém compatibilidade se definido
    or json.load(open(GOOGLE_APPLICATION_CREDENTIALS, "r", encoding="utf-8")).get("project_id")
)

if not PROJECT_ID:
    raise ValueError("Não foi possível determinar o PROJECT_ID. Defina GCP_PROJECT_ID ou inclua 'project_id' no JSON.")

if not OPENAI_API_KEY:
    raise ValueError("A variável de ambiente 'OPENAI_API_KEY' não está definida.")

if not GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    raise ValueError("Defina GOOGLE_APPLICATION_CREDENTIALS apontando para o arquivo JSON da conta de serviço.")

if not os.path.exists(LIBREOFFICE_PATH):
    # Você pode levantar um erro ou simplesmente imprimir um aviso
    print(f"AVISO: O caminho para o LibreOffice não foi encontrado em '{LIBREOFFICE_PATH}'. A conversão para PDF pode falhar.")

# Monta o ODBC_CONNECT
#odbc_str = (
#    "DRIVER={ODBC Driver 17 for SQL Server};"
#    "SERVER=172.20.12.219;"
#    "DATABASE=ATOS;"
#    "UID=sis.atos;"
#    "PWD=sisatos@TCEAC@2025;"
#    "Trusted_Connection=no;"
#)

odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-IUGBE2R;"
    "DATABASE=atos;"
    "Trusted_Connection=yes;"
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