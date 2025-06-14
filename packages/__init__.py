from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')

# Load configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Chapa Configuration
app.config['CHAPA_SECRET_KEY'] = os.getenv('CHAPA_SECRET_KEY')
app.config['CHAPA_PUBLIC_KEY'] = os.getenv('CHAPA_PUBLIC_KEY')
app.config['CHAPA_BASE_URL'] = 'https://api.chapa.co/v1'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = 'info'

# Import routes after db initialization
from packages import routes

# Create database if it doesn't exist
with app.app_context():
    db.create_all()
