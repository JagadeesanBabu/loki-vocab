import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.models import WordCount
from services.dashboard_service import DashboardService
import logging
logger = logging.getLogger(__name__)

dashboard_blueprint = Blueprint('dashboard_blueprint', __name__)

@dashboard_blueprint.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    today = datetime.date.today() + datetime.timedelta(days=1)
    one_month_ago = today - datetime.timedelta(days=30)

    # Query total counts per day for the last 30 days
    logger.debug(f"Querying daily counts from {one_month_ago} to {today}")
    # daily_correct_counts_records_by_user = WordCount.get_daily_correct_counts_by_user(one_month_ago, today)
    # daily_incorrect_counts_records = WordCount.get_daily_incorrect_counts(one_month_ago, today)
    # daily_incorrect_counts_records_by_user = WordCount.get_daily_incorrect_counts_by_user(one_month_ago, today)
    daily_correct_counts_records_by_user = DashboardService.get_correct_counts_by_user(one_month_ago, today)
    daily_incorrect_counts_records = DashboardService.get_incorrect_counts_by_user(one_month_ago, today)


    # Extract the date and count values from the query result
    # dates = list({a.date for a in daily_correct_counts_records_by_user})
    dates = list(dict.fromkeys([row.get("date") for row in daily_correct_counts_records_by_user]))
    # counts = [record.total_count for record in daily_correct_counts_records_by_user]
    # incorrect_counts = [record.total_incorrect_count for record in daily_incorrect_counts_records]
    # correct_counts_by_loke = [b for a,b,c in daily_correct_counts_records_by_user if c == 'loke']
    correct_counts_by_loke = [record.get("total_correct_count") for record in daily_correct_counts_records_by_user if record.get("user") == 'loke']
    # correct_counts_by_adarsh = [b for a,b,c in daily_correct_counts_records_by_user if c == 'adarsh']
    correct_counts_by_adarsh = [record.get("total_correct_count") for record in daily_correct_counts_records_by_user if record.get("user") == 'adarsh']
    # incorrect_counts_by_loke = [c for a,b,c in daily_incorrect_counts_records_by_user if b == 'loke']
    incorrect_counts_by_loke = [record.get("total_incorrect_count") for record in daily_incorrect_counts_records if record.get("user") == 'loke']
    # incorrect_counts_by_adarsh = [c for a,b,c in daily_incorrect_counts_records_by_user if b == 'adarsh']
    incorrect_counts_by_adarsh = [record.get("total_incorrect_count") for record in daily_incorrect_counts_records if record.get("user") == 'adarsh']

    limit_reached = request.args.get('limit_reached', 'false').lower() == 'true'
    # Capitalize the first letter of the username
    logged_user = current_user.username
    logged_user = logged_user[0].upper() + logged_user[1:]
    logger.debug(f"daily_correct_counts_records_by_user: {daily_correct_counts_records_by_user}")
    logger.debug(f"daily_incorrect_counts_records: {daily_incorrect_counts_records}")


    return render_template(
        'dashboard.html',
        dates=dates,
        incorrect_counts_by_user_adarsh=incorrect_counts_by_adarsh,
        incorrect_counts_by_user_loke=incorrect_counts_by_loke,
        correct_counts_by_user_loke=correct_counts_by_loke,
        correct_counts_by_user_adarsh=correct_counts_by_adarsh,
        limit_reached=limit_reached,
        logged_user=logged_user

    )