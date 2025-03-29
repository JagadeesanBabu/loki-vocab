from difflib import SequenceMatcher
import json
import random
import re
from flask import session
from database.models import WordCount, WordData
from services.auth_service import clear_session_files
from services.openai_service import fetch_definition, fetch_incorrect_options, fetch_similar_words
import logging
logger = logging.getLogger(__name__)


def reset_score():
    """Resets the user's score."""
    clear_session_files()
    session['score'] = {'correct': 0, 'incorrect': 0}
    session.modified = True

def get_next_question(unlearned_words):
    """Fetches the next question with options."""
    from config import Config
    from services.google_sheet_service import GoogleSheetsService
    
    word = random.choice(unlearned_words)
    # hardcoding the word for testing
    # word = "defunct"
    
    # Check if we have Google Sheets service info in the session
    if 'sheet_service' not in session:
        service_account_file_info = Config.GOOGLE_CREDENTIALS_JSON
        spreadsheet_id = Config.SPREADSHEET_ID
        session['sheet_service'] = {'service_account_info': service_account_file_info, 'spreadsheet_id': spreadsheet_id}
    
    # if the word is available in the DB, fetch the definition & incorrect options from the DB
    if not WordData.word_exists(word):
        correct_answer = fetch_definition(word)
        incorrect_options = fetch_incorrect_options(word, correct_answer, num_options=3)
        word_data = WordData(word=word, definition=correct_answer, incorrect_options=json.dumps(incorrect_options))
        word_data.add_word_data()
        
        # Also save to Google Sheets
        try:
            service_info = session['sheet_service']
            sheets_service = GoogleSheetsService(
                service_info['service_account_info'], 
                service_info['spreadsheet_id']
            )
            sheets_service.save_vocabulary_word(word, correct_answer)
        except Exception as e:
            logger.error(f"Error saving vocabulary word to Google Sheets: {e}")
    else:
        logger.info(f"Word '{word}' already exists in the database.")
        correct_answer = WordData.get_correct_answer(word)
        incorrect_options = json.loads(WordData.get_incorrect_options(word))  # Ensure incorrect_options is parsed as a list
        
        # Still save to Google Sheets to ensure it's there
        try:
            service_info = session['sheet_service']
            sheets_service = GoogleSheetsService(
                service_info['service_account_info'], 
                service_info['spreadsheet_id']
            )
            sheets_service.save_vocabulary_word(word, correct_answer)
        except Exception as e:
            logger.error(f"Error saving vocabulary word to Google Sheets: {e}")

    options = incorrect_options + [correct_answer]
    random.shuffle(options)

    return {
        'word': word,
        'correct_answer': correct_answer,
        'options': options
    }

def normalize_text(text):
    """Removes special characters, extra spaces, and normalizes case."""
    return  re.sub(r'\s+', ' ', text.strip().lower())

def text_similarity(a, b):
    """Returns a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def check_answer(user_answer, word, correct_answer, threshold=0.9):
    """Checks the user's answer and updates the score."""
    from config import Config
    from services.google_sheet_service import GoogleSheetsService
    
    # trim and convert to lowercase for case-insensitive comparison
    user_answer = user_answer.strip().lower()
    correct_answer = correct_answer.strip().lower()

    # Normalize the user's answer and the correct answer
    user_answer_normalized = normalize_text(user_answer)
    correct_answer_normalized = normalize_text(correct_answer)

    # Check if the user's answer is similar to the correct answer
    similarity_ratio = text_similarity(user_answer_normalized, correct_answer_normalized)
    logger.info(f"Similarity ratio: {similarity_ratio} and threshold: {threshold}")
    logger.info(f"User answer: {user_answer_normalized} \nCorr answer: {correct_answer_normalized}")
    
    # Save the word to Google Sheets regardless of answer correctness
    try:
        # Check if we have Google Sheets service info in the session
        if 'sheet_service' not in session:
            service_account_file_info = Config.GOOGLE_CREDENTIALS_JSON
            spreadsheet_id = Config.SPREADSHEET_ID
            session['sheet_service'] = {'service_account_info': service_account_file_info, 'spreadsheet_id': spreadsheet_id}
        
        # Save word to Google Sheets
        service_info = session['sheet_service']
        sheets_service = GoogleSheetsService(
            service_info['service_account_info'], 
            service_info['spreadsheet_id']
        )
        sheets_service.save_vocabulary_word(word, correct_answer)
        logger.info(f"Saved word '{word}' to Google Sheets after answer check")
    except Exception as e:
        logger.error(f"Error saving vocabulary word to Google Sheets: {e}")
    
    # Check if the user's answer is close to the correct answer
    is_correct = similarity_ratio >= threshold

    similar_words = []
    if is_correct:
        session['score']['correct'] += 1
        result_message = f"Correct! The meaning of '{word}' is '{correct_answer}'."
        answer_status = "correct"
        # Increment word count
        WordCount.increment_word_count(word)
        # Fetch similar words
        similar_words = fetch_similar_words(word, num_words=4)
    else:
        session['score']['incorrect'] += 1
        result_message = f"Incorrect. The correct meaning of '{word}' is '{correct_answer}'."
        answer_status = "incorrect"
        WordCount.increment_incorrect_count(word)
        # Store the incorrect answer details to summarize in the summary page.
        if 'incorrect_answers' not in session:
            session['incorrect_answers'] = []
        session['incorrect_answers'].append({
            'word': word,
            'user_answer': user_answer,
            'correct_answer': correct_answer
        })

    return {
        'result_message': result_message,
        'correct_answer': correct_answer,
        'answer_status': answer_status,
        'updated_score': session['score'],
        'similar_words': similar_words
    }

def get_summary():
    """Aggregates the summary of right and wrong answers."""
    correct_answers = session['score']['correct']
    incorrect_answers = session['score']['incorrect']
    total_answers = correct_answers + incorrect_answers
    return {
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'total_answers': total_answers,
        'incorrect_answer_details': session.get('incorrect_answers', [])
    }
