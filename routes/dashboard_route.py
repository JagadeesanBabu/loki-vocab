from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.models import WordCount, MathProblemCount
from services.dashboard_service import DashboardService
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

dashboard_blueprint = Blueprint('dashboard_blueprint', __name__)

@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
    # Get the date range for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Get unique dates for the period
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Get correct and incorrect counts for both users
    correct_counts_by_user_loke = DashboardService.get_correct_counts_by_user('loke', start_date, end_date)
    correct_counts_by_user_adarsh = DashboardService.get_correct_counts_by_user('adarsh', start_date, end_date)
    incorrect_counts_by_user_loke = DashboardService.get_incorrect_counts_by_user('loke', start_date, end_date)
    incorrect_counts_by_user_adarsh = DashboardService.get_incorrect_counts_by_user('adarsh', start_date, end_date)

    # Get math statistics by category
    math_category_stats = {
        'loke': DashboardService.get_math_stats_by_category('loke', start_date, end_date),
        'adarsh': DashboardService.get_math_stats_by_category('adarsh', start_date, end_date)
    }

    # Get math statistics by difficulty
    math_difficulty_stats = {
        'loke': DashboardService.get_math_stats_by_difficulty('loke', start_date, end_date),
        'adarsh': DashboardService.get_math_stats_by_difficulty('adarsh', start_date, end_date)
    }

    # Get unique categories and difficulties
    categories = sorted(set(
        list(math_category_stats['loke'].keys()) +
        list(math_category_stats['adarsh'].keys())
    ))
    difficulties = sorted(set(
        list(math_difficulty_stats['loke'].keys()) +
        list(math_difficulty_stats['adarsh'].keys())
    ))

    limit_reached = request.args.get('limit_reached', 'false').lower() == 'true'
    # Capitalize the first letter of the username
    logged_user = current_user.username
    logged_user = logged_user[0].upper() + logged_user[1:]

    return render_template(
        'dashboard.html',
        dates=dates,
        correct_counts_by_user_loke=correct_counts_by_user_loke,
        correct_counts_by_user_adarsh=correct_counts_by_user_adarsh,
        incorrect_counts_by_user_loke=incorrect_counts_by_user_loke,
        incorrect_counts_by_user_adarsh=incorrect_counts_by_user_adarsh,
        limit_reached=limit_reached,
        logged_user=logged_user,
        categories=categories,
        difficulties=difficulties,
        math_category_stats=math_category_stats,
        math_difficulty_stats=math_difficulty_stats
    )