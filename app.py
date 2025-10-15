import os
from flask                  import Flask, render_template
from config                 import *
from extensions             import db, login_manager
from models                 import User
from routes                 import main_bp
from admin_routes           import admin_bp
from criterio_routes        import criterio_bp
from classe_routes          import classe_bp
from groupo_routes          import grupo_bp
from tipo_documento_routes  import tipo_documento_bp
from commands               import register_commands
from waitress               import serve


def create_app():
    app = Flask(__name__)
    
    # Usar configuração de produção se estiver em container
    if os.environ.get('FLASK_ENV') == 'production' or os.path.exists('/.dockerenv'):
        app.config.from_object('config_production')
    else:
        import config
        app.config.from_object('config')

    # inicializa o SQLAlchemy
    db.init_app(app)
    login_manager.init_app(app)

    # registra rotas (ou blueprints)
    app.register_blueprint(main_bp)
    app.register_blueprint(criterio_bp)
    app.register_blueprint(classe_bp)
    app.register_blueprint(grupo_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tipo_documento_bp)


    # Registra comandos CLI (ex: flask init-db)
    register_commands(app)

    return app

# Função para carregar o utilizador a partir da sessão em cada requisição
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message=str(error)), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message="Página não encontrada."), 404

@app.errorhandler(Exception)
def generic_error(error):
    return render_template('error.html', error_message=str(error)), 500

# Health check endpoint para monitoramento
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'atos'}, 200

if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        # Produção: usando Waitress com acesso de rede
        # Use 0.0.0.0 para permitir acesso do proxy reverso
        SERVE_HOST = '0.0.0.0'
        SERVE_PORT = 5000
        serve(app, host=SERVE_HOST, port=SERVE_PORT, threads=8)
    else:
        # Desenvolvimento: Flask debug com acesso de rede
        # Use 0.0.0.0 para permitir acesso de outros dispositivos na rede
        app.run(host='0.0.0.0', port=5000, debug=True)
        