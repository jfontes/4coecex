from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

# Inicializa o Flask-Login
login_manager = LoginManager()
# Define a rota para a qual utilizadores não autenticados serão redirecionados
login_manager.login_view = 'admin.login'
# Mensagem exibida ao tentar aceder a uma página protegida
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

