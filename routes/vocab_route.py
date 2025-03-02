import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
from database.models import WordData, WordCount
from services.vocab_service import reset_score, get_next_question, check_answer, get_summary
from services.google_sheet_service import GoogleSheetsService
from config import Config
import logging
logger = logging.getLogger(__name__)

vocab_game_blueprint = Blueprint('vocab_game_blueprint', __name__)

@vocab_game_blueprint.route('/reset', methods=['GET'])
@login_required
def reset_score_route():
    reset_score()
    return redirect(url_for('vocab_game_blueprint.vocab_game'))

@vocab_game_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def vocab_game():
    """Handles the vocabulary game logic."""
    if 'score' not in session:
        session['score'] = {'correct': 0, 'incorrect': 0}
    # Check if the user has attempted 50 questions from the DB and redirect to dashboard saying you have reached the limit
    todays_user_word_count = WordCount.get_todays_user_word_count()
    logger.info(f"Today's user word count: {str(todays_user_word_count)}")
    if todays_user_word_count >= 120:
        return redirect(url_for('dashboard_blueprint.dashboard', limit_reached=True))

    if request.method == 'POST':
        # Retrieve session data
        word = session.get('word')
        correct_answer = session.get('correct_answer')
        options = session.get('options')

        if not word or not correct_answer or not options:
            return redirect(url_for('vocab_game_blueprint.vocab_game'))

        # Get the user's answer
        user_answer = request.form['answer'].strip()

        # Check the user's answer
        result_data = check_answer(user_answer, word, correct_answer)
        session['score'] = result_data['updated_score']

        # Mark the session as modified to save changes
        session.modified = True

        # Render the response for the current answer
        return render_template(
            'vocab_game.html',
            word=word,
            options=options,
            result=result_data['result_message'],
            correct_answer=result_data['correct_answer'],
            answer_status=result_data['answer_status'],
            score=session['score'],
            show_next_question=True,
            similar_words=result_data.get('similar_words', [])
        )
    else:
        # GET request: Initialize a new question
        service_account_file_info = Config.GOOGLE_CREDENTIALS_JSON
        spreadsheet_id = Config.SPREADSHEET_ID
        sheets_service = GoogleSheetsService(service_account_file_info, spreadsheet_id)

        # Always reload words from Google Sheets to get latest updates
        all_words = sheets_service.load_words()
        
        # Log the words loaded from Google Sheets
        logger.info(f"Loaded {len(all_words)} words from Google Sheets")
        
        # For debugging, log the first few words if available
        if all_words and len(all_words) > 0:
            sample = all_words[:min(5, len(all_words))]
            logger.info(f"Sample words: {sample}")
            
        session['all_words'] = all_words
        
        # Exclude words that have been presented more than 10 times

        unlearned_words = WordData.get_unlearned_words(all_words, max_count=1)
        logger.info(f"Found {len(unlearned_words)} unlearned words")
        
        # If no unlearned words, just use all words (this means all have been seen at least once)
        if not unlearned_words and all_words:
            logger.info("No unlearned words found, using all available words instead")
            unlearned_words = all_words
            
        if not unlearned_words:
            # If all words are learned and no words available at all
            logger.error("No words available at all. This should not happen with our default words.")
            return render_template(
                'vocab_game.html',
                word='',
                options=[],
                result='Congratulations! You have learned all the words.',
                answer_status='',
                score=session['score'],
                show_next_question=False,
                similar_words=[]
            )

        # Generate the next question
        question_data = get_next_question(unlearned_words)
        session['word'] = question_data['word']
        session['correct_answer'] = question_data['correct_answer']
        session['options'] = question_data['options']

        # Render the question page
        return render_template(
            'vocab_game.html',
            word=question_data['word'],
            options=question_data['options'],
            result="",
            answer_status="",
            score=session['score'],
            show_next_question=False,
            similar_words=[]
        )

@vocab_game_blueprint.route('/get_similar_words', methods=['POST'])
@login_required
def get_similar_words():
    from flask import jsonify
    from services.openai_service import fetch_similar_words
    word = request.form.get('word')
    if not word:
        return jsonify({'error': 'No word provided'}), 400
    
    similar_words = fetch_similar_words(word, num_words=4)
    return jsonify({'similar_words': similar_words})

@vocab_game_blueprint.route('/summary', methods=['GET'])
@login_required
def summary():
    summary_data = get_summary()
    return render_template('summary.html', summary=summary_data)
