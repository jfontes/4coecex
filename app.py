import os
from flask      import Flask, render_template
from config     import *
from extensions import db
from routes     import main_bp
from waitress   import serve
from criterio_routes import criterio_bp
from classe_routes import classe_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # inicializa o SQLAlchemy
    db.init_app(app)

    # registra rotas (ou blueprints)
    app.register_blueprint(main_bp)
    app.register_blueprint(criterio_bp)
    app.register_blueprint(classe_bp)

    return app

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

if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        # troque pelo IP que você quer expor
        SERVE_HOST = '192.168.226.216'
        SERVE_PORT = 5000
        serve(app, host=SERVE_HOST, port=SERVE_PORT, threads=8)
    else:
        # desenvolvimento: Flask debug em localhost
        app.run(host='127.0.0.1', port=80, debug=True)
        