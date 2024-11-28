import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
from database.models import WordData, WordCount
from services.vocab_service import reset_score, get_next_question, check_answer, get_summary
from services.google_sheet_service import GoogleSheetsService
from config import Config

vocab_game_blueprint = Blueprint('vocab_game_blueprint', __name__)

@vocab_game_blueprint.route('/reset', methods=['GET'])
@login_required
def reset_score_route():
    reset_score()
    return redirect(url_for('vocab_game_blueprint.vocab_game'))

@vocab_game_blueprint.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    today = datetime.date.today() + datetime.timedelta(days=1)
    one_month_ago = today - datetime.timedelta(days=30)

    # Query total counts per day for the last 30 days
    print(f"Querying daily counts from {one_month_ago} to {today}")
    daily_correct_counts_records_by_user = WordCount.get_daily_correct_counts_by_user(one_month_ago, today)
    daily_incorrect_counts_records = WordCount.get_daily_incorrect_counts(one_month_ago, today)
    daily_incorrect_counts_records_by_user = WordCount.get_daily_incorrect_counts_by_user(one_month_ago, today)


    # Extract the date and count values from the query result
    dates = list({a.date for a in daily_correct_counts_records_by_user})
    counts = [record.total_count for record in daily_correct_counts_records_by_user]
    incorrect_counts = [record.total_incorrect_count for record in daily_incorrect_counts_records]
    correct_counts_by_loke = [b for a,b,c in daily_correct_counts_records_by_user if c == 'loke']
    correct_counts_by_adarsh = [b for a,b,c in daily_correct_counts_records_by_user if c == 'adarsh']
    incorrect_counts_by_loke = [c for a,b,c in daily_incorrect_counts_records_by_user if b == 'loke']
    incorrect_counts_by_adarsh = [c for a,b,c in daily_incorrect_counts_records_by_user if b == 'adarsh']

    limit_reached = request.args.get('limit_reached', 'false').lower() == 'true'
    # Capitalize the first letter of the username
    logged_user = current_user.username
    logged_user = logged_user[0].upper() + logged_user[1:]
    print(f"Dates: {dates} Counts: {counts}") 
    print(f"Correct Counts by Loke: {correct_counts_by_loke}")
    print(f"Correct Counts by Adarsh: {correct_counts_by_adarsh}")
    print(f"Incorrect Counts by user: {incorrect_counts_by_loke}")
    print(f"Incorrect Counts by user: {incorrect_counts_by_adarsh}")


    """Displays the user's progress."""
    words = WordCount.query.all()
    total_words = WordCount.get_total_words
    total_counts = WordCount.get_total_counts()
    learnt_words = WordCount.get_learnt_words()
    word_labels = [word.word for word in words]
    word_counts = [word.count for word in words]
    return render_template(
        'dashboard.html',
        total_words=total_words,
        total_counts=total_counts,
        learnt_words=learnt_words,
        word_labels=word_labels,
        word_counts=word_counts,
        dates=dates,
        counts=counts,
        incorrect_counts=incorrect_counts,
        incorrect_counts_by_user_adarsh=incorrect_counts_by_adarsh,
        incorrect_counts_by_user_loke=incorrect_counts_by_loke,
        correct_counts_by_user_loke=correct_counts_by_loke,
        correct_counts_by_user_adarsh=correct_counts_by_adarsh,
        limit_reached=limit_reached,
        logged_user=logged_user

    )

@vocab_game_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def vocab_game():
    """Handles the vocabulary game logic."""
    if 'score' not in session:
        session['score'] = {'correct': 0, 'incorrect': 0}
    # Check if the user has attempted 50 questions from the DB and redirect to dashboard saying you have reached the limit
    todays_user_word_count = WordCount.get_todays_user_word_count()
    print(f"Today's user word count: {str(todays_user_word_count)}")
    if todays_user_word_count >= 150:
        return redirect(url_for('vocab_game_blueprint.dashboard', limit_reached=True))

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
            show_next_question=True
        )
    else:
        # GET request: Initialize a new question
        service_account_file_info = Config.GOOGLE_CREDENTIALS_JSON
        spreadsheet_id = Config.SPREADSHEET_ID
        sheets_service = GoogleSheetsService(service_account_file_info, spreadsheet_id)

        # Load all words if its not already loaded
        if 'all_words' not in session:
            all_words = sheets_service.load_words()
            session['all_words'] = all_words
        else:
            all_words = session['all_words']
        
        # Exclude words that have been presented more than 10 times

        unlearned_words = WordData.get_unlearned_words(all_words, max_count=10)
        
        if not unlearned_words:
            # If all words are learned
            return render_template(
                'vocab_game.html',
                word='',
                options=[],
                result='Congratulations! You have learned all the words.',
                answer_status='',
                score=session['score'],
                show_next_question=False
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
            show_next_question=False
        )

@vocab_game_blueprint.route('/summary', methods=['GET'])
@login_required
def summary():
    summary_data = get_summary()
    return render_template('summary.html', summary=summary_data)
