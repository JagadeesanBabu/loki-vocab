import time
from werkzeug.security import check_password_hash
from database.models import User
import logging 
import os, glob
logger = logging.getLogger(__name__)

def authenticate_user(username, password) -> User:
    if username == "loke" and password == "latha":
        return User(id="1", username="loke", password="latha")
    elif username == "adarsh" and password == "sridhar":
        return User(id="2", username="adarsh", password="sridhar")
    return None

def load_user(user_id):
    return User.get(user_id)

def clear_session_files() -> None:
    session_folder = os.path.join(os.path.dirname(__file__), '..', 'flask_session')
    if not os.path.exists(session_folder):
        logger.debug(f"Session folder {session_folder} does not exist.")
        return

    for file in glob.glob(os.path.join(session_folder, '*')):
        try:
            os.remove(file)
            logger.debug(f"Deleted session file: {file}")
        except Exception as e:
            logger.error(f"Error deleting file {file}: {e}")

    # Add a delay to check if new files are being created
    #time.sleep(2)
    remaining_files = glob.glob(os.path.join(session_folder, '*'))
    if remaining_files:
        logger.info(f"New session files created: {remaining_files}")
    else:
        logger.info("All session files cleared.")