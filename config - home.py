import os
from urllib.parse import quote_plus

# Secret key
SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
# Gemini API Key
GEMINI_API_KEY = "AIzaSyAaMg0T6NIoSYV_8_3leJd9mjkwA2Of_A0"
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

# Monta o ODBC_CONNECT
odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-IUGBE2R;"
    "DATABASE=certificador;"
    "Trusted_Connection=yes;"
)

ODBC_CONNECT = quote_plus(odbc_str)

SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={ODBC_CONNECT}"

SQLALCHEMY_TRACK_MODIFICATIONS = False

if not os.path.exists(LIBREOFFICE_PATH):
    # Você pode levantar um erro ou simplesmente imprimir um aviso
    print(f"AVISO: O caminho para o LibreOffice não foi encontrado em '{LIBREOFFICE_PATH}'. A conversão para PDF pode falhar.")