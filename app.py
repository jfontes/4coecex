import os
from flask      import Flask
from config     import *
from extensions import db
from routes     import main_bp
from waitress   import serve

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # inicializa o SQLAlchemy
    db.init_app(app)

    # registra rotas (ou blueprints)
    app.register_blueprint(main_bp)

    return app

app = create_app()

if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        # troque pelo IP que você quer expor
        SERVE_HOST = '192.168.226.216'
        SERVE_PORT = 5000
        serve(app, host=SERVE_HOST, port=SERVE_PORT)
    else:
        # desenvolvimento: Flask debug em localhost
        app.run(host='127.0.0.1', port=80, debug=True)
        