import random
import json
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import gspread
from google.oauth2.service_account import Credentials
import openai
import sqlite3
from openai.error import RateLimitError, OpenAIError
from flask import Blueprint, session, redirect, url_for, render_template
from flask_login import login_required
import glob
# ChatGPT 4o mini model
model = "gpt-4o-mini-2024-07-18"
import os


# Load env variables for Local environment local.env

from dotenv import load_dotenv
# check if local.env exists
if os.path.exists('local.env'):
    load_dotenv('local.env')

# Google Sheets Setup
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_info(
    json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON')),
    scopes=SCOPE
)
gc = gspread.authorize(credentials)
SPREADSHEET_ID = '1e5tZWB7rR7YfDSlBd6E5vBmM1GnxB6Emxj13JL4j8PE'  # Replace with your Google Sheets ID
worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1

def load_words_from_sheet():
    values = worksheet.col_values(1)
    words = values[1:]  # Adjust index if no header
    print(f"Loaded {len(words)} words from Google Sheets.")
    return words

# OpenAI Setup
openai.api_key = os.getenv('OPENAI_API_KEY')

# exit if no API key
if not openai.api_key:
    print("OpenAI API key not found. Please set it in the environment variable")
    exit()

# Database Setup
conn = sqlite3.connect('vocab_game.db', check_same_thread=False)
cursor = conn.cursor()

# Create Tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS word_counts (
        word TEXT PRIMARY KEY,
        count INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS word_data (
        word TEXT PRIMARY KEY,
        definition TEXT,
        incorrect_options TEXT
    )
''')
conn.commit()

def get_meaning(word):
    # Check cache
    cursor.execute('SELECT definition FROM word_data WHERE word = ?', (word,))
    result = cursor.fetchone()
    if result and result[0]:
        print(f"Retrieved definition for '{word}' from cache.")
        return result[0]
    print(f"Fetching definition for '{word}' from OpenAI API.")
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": f"Define the word '{word}'."}
            ],
            temperature=0.5,
            max_tokens=100,
            n=1,
            stop=None,
        )
        definition = response['choices'][0]['message']['content'].strip()
        # Cache the definition
        cursor.execute('''
            INSERT INTO word_data(word, definition)
            VALUES(?, ?)
            ON CONFLICT(word) DO UPDATE SET definition=excluded.definition
        ''', (word, definition))
        conn.commit()
        return definition
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        return "Definition not available due to API rate limit."
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return "Definition not available due to API error."
    except Exception as e:
        print(f"Error fetching meaning: {e}")
        return "Definition not available."

def get_incorrect_options(word, correct_definition, num_options=3):
    # Check cache
    cursor.execute('SELECT incorrect_options FROM word_data WHERE word = ?', (word,))
    result = cursor.fetchone()
    if result and result[0]:
        incorrect_definitions = json.loads(result[0])
        return incorrect_definitions[:num_options]

    try:
        # prompt = f"Provide {num_options} plausible but incorrect definitions for the word '{word}' that are different from its actual meaning, without any introductions or extra explanations. Only list each incorrect definition on a new line."
        prompt = (
        f"Provide {num_options} brief, plausible, and incorrect definitions for the word '{word}' that closely resemble "
        f"the style and structure of this correct definition: '{correct_definition}', but with a different meaning."
        f" Each incorrect definition should sound believable but describe the word inaccurately."
        )
        response = openai.ChatCompletion.create(
            model= model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60 * num_options,
            n=1,
            stop=None,
        )
        incorrect_definitions = response['choices'][0]['message']['content'].strip().split("\n")
        # Clean up the definitions
        incorrect_definitions = [defn.strip('-•1234567890. ').strip() for defn in incorrect_definitions if defn.strip()]
        # Cache the incorrect options
        cursor.execute('''
            INSERT INTO word_data(word, incorrect_options)
            VALUES(?, ?)
            ON CONFLICT(word) DO UPDATE SET incorrect_options=excluded.incorrect_options
        ''', (word, json.dumps(incorrect_definitions)))
        conn.commit()
        return incorrect_definitions[:num_options]
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        return ["Incorrect option not available due to API rate limit."] * num_options
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return ["Incorrect option not available due to API error."] * num_options
    except Exception as e:
        print(f"Error fetching incorrect options: {e}")
        return ["Incorrect option not available."] * num_options

def increment_word_count(word):
    cursor.execute('''
        INSERT INTO word_counts(word, count)
        VALUES(?, 1)
        ON CONFLICT(word) DO UPDATE SET count = count + 1
    ''', (word,))
    conn.commit()

def get_word_count(word):
    cursor.execute('SELECT count FROM word_counts WHERE word = ?', (word,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_unlearned_words(all_words, max_count=10):
    unlearned_words = []
    for word in all_words:
        count = get_word_count(word)
        if count < max_count:
            unlearned_words.append(word)
    return unlearned_words

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Initialize the server-side session extension
Session(app)




def clear_session_files():
    session_folder = app.config['SESSION_FILE_DIR']
    for file in glob.glob(os.path.join(session_folder, '*')):
        os.remove(file)


# Define vocab_game blueprint
vocab_game_blueprint = Blueprint('vocab_game_blueprint', __name__)

@vocab_game_blueprint.route('/reset', methods=['GET'])
@login_required
@app.route('/reset', methods=['GET'])
def reset_score():
    # Reset the score in the session without clearing the login session
    session.clear()
    clear_session_files()
    session['score'] = {'correct': 0, 'incorrect': 0}
    session['summary'] = []
    return redirect(url_for('vocab_game_blueprint.vocab_game'))



@vocab_game_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def vocab_game():
    if 'score' not in session:
        session['score'] = {'correct': 0, 'incorrect': 0}
    if 'summary' not in session:
        session['summary'] = []

    if request.method == 'POST':
        # Retrieve data from the session
        word = session.get('word')
        correct_answer = session.get('correct_answer')
        options = session.get('options')

        if not word or not correct_answer or not options:
            return redirect(url_for('vocab_game_blueprint.vocab_game'))

        # Get the user's answer
        user_answer = request.form['answer'].strip()

        # Debug information
        print(f"User Answer: {user_answer}")
        print(f"Correct Answer: {correct_answer}")
        print(f"Question: {word}")

        # Compare the user's answer with the correct answer
        if user_answer == correct_answer:
            result = f"Correct! The meaning of '{word}' is '{correct_answer}'."
            answer_status = "correct"
            session['score']['correct'] += 1
        else:
            result = f"Incorrect. The correct meaning of '{word}' is '{correct_answer}'."
            answer_status = "incorrect"
            session['score']['incorrect'] += 1

        # Store the question, user's answer, and correct answer in the session summary
        session['summary'].append({
            'word': word,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'status': answer_status
        })

        # Mark the session as modified to ensure changes are saved
        session.modified = True
        
        # Increment word count
        increment_word_count(word)

        # Render the response for the current answer
        return render_template(
            'vocab_game.html',
            word=word,
            options=options,
            result=result,
            correct_answer=correct_answer,
            answer_status=answer_status,
            score=session['score'],
            show_next_question=True,
            summary=session['summary']
        )
    else:
        # GET request: Initialize new question
        all_words = load_words_from_sheet()

        # Exclude words that have been presented more than 10 times
        unlearned_words = get_unlearned_words(all_words, max_count=10)

        if not unlearned_words:
            # If all words are learned
            return render_template(
                'vocab_game.html',
                word='',
                options=[],
                result='Congratulations! You have learned all the words.',
                answer_status='',
                score=session['score'],
                show_next_question=False,
                summary=session['summary']
            )

        word = random.choice(unlearned_words)
        correct_answer = get_meaning(word)
        # Generate incorrect options
        incorrect_options = get_incorrect_options(word, correct_answer, num_options=3)

        options = incorrect_options + [correct_answer]
        random.shuffle(options)

        # Store data in session
        session['word'] = word
        session['correct_answer'] = correct_answer
        session['options'] = options

        return render_template(
            'vocab_game.html',
            word=word,
            options=options,
            result="",
            answer_status="",
            score=session['score'],
            show_next_question=False,
            summary=session['summary']
        )
