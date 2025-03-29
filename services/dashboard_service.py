import datetime
from itertools import product
from datetime import datetime, date, timedelta
from sqlalchemy import func
from database.models import WordCount, MathProblemCount
from database.db import db
from services.optimization_service import MathSheetsOptimizer
import logging
logger = logging.getLogger(__name__)

class DashboardService:
    @classmethod
    def _get_date_user_combinations(cls, start_date, end_date) -> list:
        """
        Generate all combinations of unique dates and users for the given date range.
        Ensures that the format of dates and users matches the database keys.
        """
        # Get unique dates and users from both word counts and math problem counts
        word_dates = WordCount.get_unique_dates(start_date, end_date)
        math_dates = MathProblemCount.get_unique_dates(start_date, end_date)
        word_users = WordCount.get_unique_users(start_date, end_date)
        math_users = MathProblemCount.get_unique_users(start_date, end_date)

        # Combine unique dates and users
        unique_dates = list(set(word_dates + math_dates))
        unique_users = list(set(word_users + math_users))

        # Ensure dates are strings and users are formatted correctly
        dates = [d.strftime("%Y-%m-%d") if isinstance(d, date) else str(d) for d in unique_dates]
        users = [str(user) for user in unique_users]

        # Generate all combinations of dates and users
        date_user_combinations = [{"date": date, "user": user} for date, user in product(dates, users)]
        logger.debug(f"Date user combinations: {date_user_combinations}")
        return date_user_combinations

    @classmethod
    def get_incorrect_counts_by_user(cls, user, start_date, end_date) -> list:
        """
        Retrieve and process daily incorrect counts for a specific user within the date range.
        Combines both word and math problem incorrect counts.
        """
        # Get word counts from database
        word_counts = WordCount.get_daily_incorrect_counts_by_user(start_date, end_date)
        
        # Get math counts from Google Sheets
        math_stats = MathSheetsOptimizer.get_math_stats(user, start_date, end_date)
        
        logger.debug(f"Word incorrect counts: {word_counts}")
        logger.debug(f"Math incorrect counts: {math_stats['daily_incorrect']}")

        # Fill missing data with zeros
        result = []
        current_date = start_date
        day_index = 0
        while current_date <= end_date:
            date_key = current_date.date()
            
            # Get word count for this day
            word_count = word_counts.get((date_key, user), 0)
            
            # Get math count for this day
            math_count = math_stats['daily_incorrect'][day_index] if day_index < len(math_stats['daily_incorrect']) else 0
            
            # Combine the counts
            total_count = word_count + math_count
            result.append(total_count)
            
            current_date += timedelta(days=1)
            day_index += 1
        
        return result

    @classmethod
    def get_correct_counts_by_user(cls, user, start_date, end_date) -> list:
        """
        Retrieve and process daily correct counts for a specific user within the date range.
        Combines both word and math problem correct counts.
        """
        # Get word counts from database
        word_counts = WordCount.get_daily_correct_counts_by_user(start_date, end_date)
        
        # Get math counts from Google Sheets
        math_stats = MathSheetsOptimizer.get_math_stats(user, start_date, end_date)
        
        logger.debug(f"Word correct counts: {word_counts}")
        logger.debug(f"Math correct counts: {math_stats['daily_correct']}")

        # Fill missing data with zeros
        result = []
        current_date = start_date
        day_index = 0
        while current_date <= end_date:
            date_key = current_date.date()
            
            # Get word count for this day
            word_count = word_counts.get((date_key, user), 0)
            
            # Get math count for this day
            math_count = math_stats['daily_correct'][day_index] if day_index < len(math_stats['daily_correct']) else 0
            
            # Combine the counts
            total_count = word_count + math_count
            result.append(total_count)
            
            current_date += timedelta(days=1)
            day_index += 1
        
        return result

    @classmethod
    def get_math_stats_by_category(cls, user, start_date, end_date):
        """Get math statistics grouped by category for a specific user."""
        math_stats = MathSheetsOptimizer.get_math_stats(user, start_date, end_date)
        return math_stats['by_category']

    @classmethod
    def get_math_stats_by_difficulty(cls, user, start_date, end_date):
        """Get math statistics grouped by difficulty for a specific user."""
        math_stats = MathSheetsOptimizer.get_math_stats(user, start_date, end_date)
        return math_stats['by_difficulty']