from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os  # For path checking

# Initialize the database
db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the Flask app
    db.init_app(app)

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .models import File
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    
    # Ensure the database is created
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
        print(f' ! Created Database at {db_path}')

    return app
