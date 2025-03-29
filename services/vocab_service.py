from difflib import SequenceMatcher
import json
import random
import re
from flask import session
from database.models import WordCount, WordData
from services.auth_service import clear_session_files
from services.optimization_service import OpenAIOptimizer, GoogleSheetsOptimizer, PersistentCache
import logging
logger = logging.getLogger(__name__)


def reset_score():
    """Resets the user's score."""
    clear_session_files()
    session['score'] = {'correct': 0, 'incorrect': 0}
    session.modified = True

async def get_next_question(unlearned_words):
    """Fetches the next question with options."""
    word = random.choice(unlearned_words)
    
    # First check if word exists in our database
    if WordData.word_exists(word):
        logger.info(f"Word '{word}' found in database")
        correct_answer = WordData.get_correct_answer(word)
        incorrect_options = json.loads(WordData.get_incorrect_options(word))
        
        # Queue update to Google Sheets in background
        GoogleSheetsOptimizer.queue_update(word, correct_answer)
    else:
        # Use optimized OpenAI service to fetch word data
        try:
            word_data = await OpenAIOptimizer.fetch_word_data(word)
            if not word_data:
                logger.error(f"Failed to fetch word data for '{word}'")
                # Try another word
                remaining_words = [w for w in unlearned_words if w != word]
                if not remaining_words:
                    logger.error("No more words available")
                    return None
                return await get_next_question(remaining_words)
            
            # Save to database
            word_obj = WordData(
                word=word,
                definition=word_data['definition'],
                incorrect_options=json.dumps(word_data['incorrect_options'])
            )
            word_obj.add_word_data()
            
            correct_answer = word_data['definition']
            incorrect_options = word_data['incorrect_options']
            
            # Queue update to Google Sheets in background
            GoogleSheetsOptimizer.queue_update(word, correct_answer)
            
        except Exception as e:
            logger.error(f"Error fetching word data: {e}")
            # Try another word
            remaining_words = [w for w in unlearned_words if w != word]
            if not remaining_words:
                logger.error("No more words available")
                return None
            return await get_next_question(remaining_words)

    options = incorrect_options + [correct_answer]
    random.shuffle(options)

    return {
        'word': word,
        'correct_answer': correct_answer,
        'options': options
    }

def normalize_text(text):
    """Removes special characters, extra spaces, and normalizes case."""
    return re.sub(r'\s+', ' ', text.strip().lower())

def text_similarity(a, b):
    """Returns a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

async def check_answer(user_answer, word, correct_answer, threshold=0.9):
    """Checks the user's answer and updates the score."""
    # Normalize answers
    user_answer = normalize_text(user_answer)
    correct_answer = normalize_text(correct_answer)

    # Check similarity
    similarity_ratio = text_similarity(user_answer, correct_answer)
    logger.info(f"Similarity ratio: {similarity_ratio} and threshold: {threshold}")
    
    # Determine if answer is correct
    is_correct = similarity_ratio >= threshold

    similar_words = []
    if is_correct:
        session['score']['correct'] += 1
        result_message = f"Correct! The meaning of '{word}' is '{correct_answer}'."
        answer_status = "correct"
        # Increment word count
        WordCount.increment_word_count(word)
        
        # Fetch similar words using optimized service
        try:
            word_data = await OpenAIOptimizer.fetch_word_data(word)
            similar_words = word_data.get('similar_words', [])
        except Exception as e:
            logger.error(f"Error fetching similar words: {e}")
            similar_words = []
    else:
        session['score']['incorrect'] += 1
        result_message = f"Incorrect. The correct meaning of '{word}' is '{correct_answer}'."
        answer_status = "incorrect"
        WordCount.increment_incorrect_count(word)
        
        if 'incorrect_answers' not in session:
            session['incorrect_answers'] = []
        session['incorrect_answers'].append({
            'word': word,
            'user_answer': user_answer,
            'correct_answer': correct_answer
        })

    # Ensure session is saved
    session.modified = True

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
