import os
from urllib.parse import quote_plus

# Secret key
SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# LibreOffice Path (configurado para container)
LIBREOFFICE_PATH = os.environ.get('LIBREOFFICE_PATH', '/usr/lib/libreoffice/program/soffice')

# Configuração do banco de dados usando variáveis de ambiente
DB_SERVER = os.environ.get('DB_SERVER', '172.20.12.219')
DB_NAME = os.environ.get('DB_NAME', 'ATOS')
DB_USER = os.environ.get('DB_USER', 'sis.atos')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'sisatos@TCEAC@2025')

# Monta o ODBC_CONNECT
odbc_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    f"Trusted_Connection=no;"
)

ODBC_CONNECT = quote_plus(odbc_str)
SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={ODBC_CONNECT}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de produção
FLASK_ENV = 'production'
DEBUG = False

# Configurações de logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.environ.get('LOG_FILE', '/app/logs/app.log')

# Configurações de upload
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
UPLOAD_FOLDER = '/app/temp'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}

# Configurações de sessão
PERMANENT_SESSION_LIFETIME = 3600  # 1 hora

# Verificar se o LibreOffice está disponível
if not os.path.exists(LIBREOFFICE_PATH):
    print(f"AVISO: O caminho para o LibreOffice não foi encontrado em '{LIBREOFFICE_PATH}'. A conversão para PDF pode falhar.")
