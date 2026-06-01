import os
from flask import Flask
from dotenv import load_dotenv

from .extensions import db, migrate

# Charger les variables du fichier .env depuis la racine
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration par défaut
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketflow.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ADMIN_RESET_TOKEN'] = os.environ.get("TICKETFLOW_ADMIN_RESET_TOKEN")
    
    if config_name:
        app.config.from_mapping(config_name)

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Enregistrement des Blueprints
    from .api.routes import api_bp
    from .frontend.routes import frontend_bp
    
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(frontend_bp)

    return app
