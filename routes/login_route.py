# This file contains the login route for the application
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from services.auth_service import authenticate_user
from services.auth_service import clear_session_files

login_blueprint = Blueprint('login_blueprint', __name__)

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for('login_blueprint.select_quiz'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@login_blueprint.route('/select')
@login_required
def select_quiz():
    return render_template('select_quiz.html')

# Logout route
@login_blueprint.route('/logout')
@login_required
def logout():
    session.clear()
    clear_session_files()
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login_blueprint.login'))
