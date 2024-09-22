from flask import Flask
from .Database.models import db_connection
from .routes import main 

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config') 

    db_connection.init_app(app)

    app.register_blueprint(main) 

    return app
