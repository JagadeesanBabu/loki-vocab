from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_login import LoginManager
from config import Config
from database.models import User
from routes.login_route import login_blueprint
from routes.vocab_route import vocab_game_blueprint
# Intialize database SQLAlchemy
from database.db import init_db
from database import db
from services.auth_service import clear_session_files

app = Flask(__name__)
app.config.from_object(Config)

# Delete the session files
# Initialize session and login manager
clear_session_files()
Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_blueprint.login'

# Initialize SQLAlchemy
init_db(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)  # Implement the get method in your User model

# Register Blueprints
app.register_blueprint(login_blueprint)
app.register_blueprint(vocab_game_blueprint)

# # Initialize database
# init_db(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
