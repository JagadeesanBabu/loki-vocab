# app.py
from flask import Flask, render_template
from flask_login import  login_required
from login import login_blueprint, login_manager, bcrypt
from vocab_game import vocab_game_blueprint 

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key

# Initialize extensions
bcrypt.init_app(app)
login_manager.init_app(app)

# Register the login blueprint
app.register_blueprint(login_blueprint)
app.register_blueprint(vocab_game_blueprint)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
