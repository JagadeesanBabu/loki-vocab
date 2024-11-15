import time
from werkzeug.security import check_password_hash
from database.models import User

import os, glob

def authenticate_user(username, password):
    if username == "loke" and password == "latha":
        return User(id="1", username="loke", password="latha")
    return None

def load_user(user_id):
    return User.get(user_id)

def clear_session_files():
    session_folder = os.path.join(os.path.dirname(__file__), '..', 'flask_session')
    if not os.path.exists(session_folder):
        print(f"Session folder {session_folder} does not exist.")
        return

    for file in glob.glob(os.path.join(session_folder, '*')):
        try:
            os.remove(file)
            print(f"Deleted session file: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

    # Add a delay to check if new files are being created
    time.sleep(2)
    remaining_files = glob.glob(os.path.join(session_folder, '*'))
    if remaining_files:
        print(f"New session files created: {remaining_files}")
    else:
        print("All session files cleared.")