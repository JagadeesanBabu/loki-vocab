import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from services.math_service import get_next_math_problem, check_math_answer, reset_math_score, get_math_summary
import asyncio
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
async def math_game():
    """Handles the math game logic."""
    if 'math_score' not in session:
        session['math_score'] = {'correct': 0, 'incorrect': 0}
    
    # Check for daily limit (you can adjust as needed)
    max_daily_problems = 50
    todays_problem_count = session.get('math_problems_today', 0)
    if todays_problem_count >= max_daily_problems:
        return redirect(url_for('dashboard_blueprint.dashboard', limit_reached=True))

    if request.method == 'POST':
        # Get user's answer and current problem
        user_answer = request.form.get('answer')
        current_problem = session.get('math_problem')

        if not user_answer or not current_problem:
            return redirect(url_for('math_game_blueprint.math_game'))

        try:
            # Convert user_answer to float if possible
            user_answer = float(user_answer) if user_answer.replace('.', '').isdigit() else user_answer
        except ValueError:
            # Keep as string if conversion fails
            pass

        # Check answer
        result_data = await check_math_answer(user_answer, current_problem)
        session['math_score'] = result_data['updated_score']
        
        # Increment the daily problem count if not already done for this problem
        if session.get('last_problem_id') != current_problem['id']:
            session['math_problems_today'] = todays_problem_count + 1
            session['last_problem_id'] = current_problem['id']

        # Mark the session as modified to save changes
        session.modified = True

        return render_template(
            'math_game.html',
            problem=current_problem,
            result=result_data['result_message'],
            answer_status=result_data['answer_status'],
            explanation=result_data.get('explanation', ''),
            score=session['math_score'],
            show_next_question=True
        )
    else:
        # Get next problem
        try:
            problem = await get_next_math_problem()
            if not problem:
                return render_template(
                    'math_game.html',
                    error="Error generating problem. Please try again.",
                    score=session.get('math_score', {'correct': 0, 'incorrect': 0})
                )

            # Store problem in session
            session['math_problem'] = problem
            session.modified = True

            return render_template(
                'math_game.html',
                problem=problem,
                score=session.get('math_score', {'correct': 0, 'incorrect': 0})
            )
        except Exception as e:
            logger.error(f"Error in math game: {e}")
            return render_template(
                'math_game.html',
                error="An error occurred. Please try again.",
                score=session.get('math_score', {'correct': 0, 'incorrect': 0})
            )

@math_game_blueprint.route('/summary', methods=['GET'])
@login_required
def summary():
    summary_data = get_math_summary()
    return render_template('math_summary.html', summary=summary_data)