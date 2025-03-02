import logging
from flask import Flask
from flask_migrate import Migrate, upgrade
from flask_session import Session
from flask_login import LoginManager
from config import Config
from database.models import User
from routes.login_route import login_blueprint
from routes.vocab_route import vocab_game_blueprint
from routes.dashboard_route import dashboard_blueprint
from routes.math_route import math_game_blueprint
# Intialize database SQLAlchemy
from database.db import init_db
from database import db
from services.auth_service import clear_session_files

# Set up Debug logging if its local environment else INFO logging for Heroku
import os
# check it the OS is mac
is_mac = os.uname().sysname == 'Darwin'
log_level = logging.INFO
if is_mac == True:
    log_level = logging.DEBUG

logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"Setting log level to {log_level}")

app = Flask(__name__)
app.config.from_object(Config)

# Delete the session files
# Initialize session and login manager
clear_session_files()
Session(app)
# Initialize SQLAlchemy
init_db(app)
# Initialize Flask-Migrate
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_blueprint.login'




# # Automatically apply migrations
# with app.app_context():
#     try:
#         upgrade()
#         print("Database migrations applied successfully.")
#     except Exception as e:
#         print(f"Error applying migrations: {e}")
        
# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)  # Implement the get method in your User model

# Register Blueprints
app.register_blueprint(login_blueprint)
app.register_blueprint(vocab_game_blueprint)
app.register_blueprint(dashboard_blueprint)
app.register_blueprint(math_game_blueprint, url_prefix='/math')

# # Initialize database
# init_db(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
