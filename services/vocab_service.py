import json
import random
from flask import session
from database.models import WordCount, WordData
from services.auth_service import clear_session_files
from services.openai_service import fetch_definition, fetch_incorrect_options


def reset_score():
    """Resets the user's score."""
    clear_session_files()
    session['score'] = {'correct': 0, 'incorrect': 0}
    session.modified = True

def get_next_question(unlearned_words):
    """Fetches the next question with options."""
    word = random.choice(unlearned_words)
    # if the word is available in the DB, fetch the definition & incorrect options from the DB
    if not WordData.word_exists(word):
        correct_answer = fetch_definition(word)
        incorrect_options = fetch_incorrect_options(word, correct_answer, num_options=3)
        word_data = WordData(word=word, definition=correct_answer, incorrect_options=json.dumps(incorrect_options))
        word_data.add_word_data()
    else:
        print(f"Word '{word}' already exists in the database.")
        correct_answer = WordData.get_correct_answer(word)
        incorrect_options = json.loads(WordData.get_incorrect_options(word))  # Ensure incorrect_options is parsed as a list

    options = incorrect_options + [correct_answer]
    random.shuffle(options)

    return {
        'word': word,
        'correct_answer': correct_answer,
        'options': options
    }

def check_answer(user_answer, word, correct_answer):
    """Checks the user's answer and updates the score."""
    # trim and convert to lowercase for case-insensitive comparison
    user_answer = user_answer.strip().lower()
    correct_answer = correct_answer.strip().lower()
    
    is_correct = user_answer == correct_answer
    if is_correct:
        session['score']['correct'] += 1
        result_message = f"Correct! The meaning of '{word}' is '{correct_answer}'."
        answer_status = "correct"
    else:
        session['score']['incorrect'] += 1
        result_message = f"Incorrect. The correct meaning of '{word}' is '{correct_answer}'."
        answer_status = "incorrect"

    # Increment word count
    WordCount.increment_word_count(word)

    return {
        'result_message': result_message,
        'correct_answer': correct_answer,
        'answer_status': answer_status,
        'updated_score': session['score']
    }
