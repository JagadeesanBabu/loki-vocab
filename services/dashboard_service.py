import datetime
from itertools import product
from datetime import datetime, date, timedelta
from sqlalchemy import func
from database.models import WordCount, MathProblemCount
from database.db import db
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
        # Get actual incorrect counts from both tables
        word_counts = WordCount.get_daily_incorrect_counts_by_user(start_date, end_date)
        math_counts = MathProblemCount.get_daily_incorrect_counts_by_user(start_date, end_date)

        logger.debug(f"Actual word incorrect counts: {word_counts}")
        logger.debug(f"Actual math incorrect counts: {math_counts}")

        # Fill missing data with zeros
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_key = current_date.date()
            
            # Look up the actual counts using the date and user as a key
            word_count = word_counts.get((date_key, user), 0)
            math_count = math_counts.get((date_key, user), 0)
            
            # Combine the counts
            total_count = word_count + math_count
            result.append(total_count)
            
            current_date += timedelta(days=1)
        
        return result

    @classmethod
    def get_correct_counts_by_user(cls, user, start_date, end_date) -> list:
        """
        Retrieve and process daily correct counts for a specific user within the date range.
        Combines both word and math problem correct counts.
        """
        # Get actual correct counts from both tables
        word_counts = WordCount.get_daily_correct_counts_by_user(start_date, end_date)
        math_counts = MathProblemCount.get_daily_correct_counts_by_user(start_date, end_date)

        logger.debug(f"Actual word correct counts: {word_counts}")
        logger.debug(f"Actual math correct counts: {math_counts}")

        # Fill missing data with zeros
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_key = current_date.date()
            
            # Look up the actual counts using the date and user as a key
            word_count = word_counts.get((date_key, user), 0)
            math_count = math_counts.get((date_key, user), 0)
            
            # Combine the counts
            total_count = word_count + math_count
            result.append(total_count)
            
            current_date += timedelta(days=1)
        
        return result

    @classmethod
    def get_math_stats_by_category(cls, user, start_date, end_date):
        """Get math statistics grouped by category for a specific user."""
        stats = db.session.query(
            MathProblemCount.category,
            func.sum(MathProblemCount.count).label('correct_count'),
            func.sum(MathProblemCount.incorrect_count).label('incorrect_count')
        ).filter(
            MathProblemCount.updated_by == user,
            MathProblemCount.created_at >= start_date,
            MathProblemCount.created_at < end_date
        ).group_by(
            MathProblemCount.category
        ).all()

        return {
            stat.category: {
                'correct': stat.correct_count or 0,
                'incorrect': stat.incorrect_count or 0
            }
            for stat in stats
        }

    @classmethod
    def get_math_stats_by_difficulty(cls, user, start_date, end_date):
        """Get math statistics grouped by difficulty for a specific user."""
        stats = db.session.query(
            MathProblemCount.difficulty,
            func.sum(MathProblemCount.count).label('correct_count'),
            func.sum(MathProblemCount.incorrect_count).label('incorrect_count')
        ).filter(
            MathProblemCount.updated_by == user,
            MathProblemCount.created_at >= start_date,
            MathProblemCount.created_at < end_date
        ).group_by(
            MathProblemCount.difficulty
        ).all()

        return {
            stat.difficulty: {
                'correct': stat.correct_count or 0,
                'incorrect': stat.incorrect_count or 0
            }
            for stat in stats
        }