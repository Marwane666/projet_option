from flask import Flask
from config import Config
from app.routes import main
from app.extensions import mongo

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialiser les extensions
    mongo.init_app(app)

    # Enregistrer les blueprints (routes)
    app.register_blueprint(main,url_prefix='/')

    return app
