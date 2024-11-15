# login.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from vocab_game import session
from vocab_game import clear_session_files

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login_blueprint.login'  # Redirect to login page if unauthorized

# Sample user storage (for production, use a database)
users = {
    'loke': bcrypt.generate_password_hash('latha').decode('utf-8')  # 'test' is the password
}

# Define a User model
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)
    return None

# Blueprint for login functionality
login_blueprint = Blueprint('login_blueprint', __name__)

# Login route
@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and bcrypt.check_password_hash(users[username], password):
            user = User(username)
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('vocab_game_blueprint.vocab_game'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

# Logout route
@login_blueprint.route('/logout')
@login_required
def logout():
    session.clear()
    clear_session_files()
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login_blueprint.login'))
