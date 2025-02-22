import os
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.debug(f"Loading environment variables from .env file")
# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), 'local.env')
if os.path.exists(dotenv_path):
    logger.debug(f"Loading environment variables from {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    logger.debug(f"{dotenv_path} file not found")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = './flask_session/'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vocab_game.db'
    # if its heroku environment then use jawsdb
    if os.environ.get('HEROKU') == 'True':
        logger.debug(f"Using JAWSDB")
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://a9n3nwpru670wwuc:k90kyttze1hgam10@cxmgkzhk95kfgbq4.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/lfp0yym72x1n2sqs'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # OpenAI API key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
