import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from services.math_service import get_next_math_problem, check_math_answer, reset_math_score, get_math_summary
import logging
logger = logging.getLogger(__name__)

math_game_blueprint = Blueprint('math_game_blueprint', __name__)

@math_game_blueprint.route('/reset', methods=['GET'])
@login_required
def reset_score_route():
    reset_math_score()
    return redirect(url_for('math_game_blueprint.math_game'))

@math_game_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def math_game():
    """Handles the math word problems game logic."""
    if 'math_score' not in session:
        session['math_score'] = {'correct': 0, 'incorrect': 0}
    
    # Check for daily limit (you can adjust as needed)
    max_daily_problems = 50
    todays_problem_count = session.get('math_problems_today', 0)
    if todays_problem_count >= max_daily_problems:
        return redirect(url_for('dashboard_blueprint.dashboard', limit_reached=True))

    if request.method == 'POST':
        # Retrieve session data
        problem = session.get('math_problem')
        correct_answer = session.get('math_correct_answer')
        
        if not problem or correct_answer is None:
            return redirect(url_for('math_game_blueprint.math_game'))

        # Get the user's answer
        user_answer = request.form.get('answer', '').strip()
        
        # Try to convert to number if possible
        try:
            user_answer = float(user_answer)
            # If it's a whole number, convert to int for cleaner display
            if user_answer.is_integer():
                user_answer = int(user_answer)
        except ValueError:
            # Keep as string if not a number
            pass

        # Check the user's answer
        result_data = check_math_answer(user_answer, problem, correct_answer)
        session['math_score'] = result_data['updated_score']
        
        # Increment the daily problem count if not already done for this problem
        if session.get('last_problem_id') != problem['id']:
            session['math_problems_today'] = todays_problem_count + 1
            session['last_problem_id'] = problem['id']

        # Mark the session as modified to save changes
        session.modified = True

        # Render the response for the current answer
        return render_template(
            'math_game.html',
            problem=problem,
            result=result_data['result_message'],
            user_answer=user_answer,
            correct_answer=result_data['correct_answer'],
            answer_status=result_data['answer_status'],
            score=session['math_score'],
            show_next_question=True,
            explanation=result_data.get('explanation', '')
        )
    else:
        # GET request: Initialize a new problem
        
        # Generate the next problem
        problem_data = get_next_math_problem()
        session['math_problem'] = problem_data['problem']
        session['math_correct_answer'] = problem_data['correct_answer']

        # Render the question page
        return render_template(
            'math_game.html',
            problem=problem_data['problem'],
            result="",
            answer_status="",
            score=session['math_score'],
            show_next_question=False,
            explanation=""
        )

@math_game_blueprint.route('/summary', methods=['GET'])
@login_required
def summary():
    summary_data = get_math_summary()
    return render_template('math_summary.html', summary=summary_data)