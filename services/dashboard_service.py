import datetime
from itertools import product
from datetime import datetime, date
from database.models import WordCount
import logging
logger = logging.getLogger(__name__)

class DashboardService:
    @classmethod
    def _get_date_user_combinations(cls, start_date, end_date) -> list:
        """
        Generate all combinations of unique dates and users for the given date range.
        Ensures that the format of dates and users matches the database keys.
        """
        # Get unique dates and users from the database
        unique_dates = WordCount.get_unique_dates(start_date, end_date)
        unique_users = WordCount.get_unique_users(start_date, end_date)

        # Ensure dates are strings and users are formatted correctly
        dates = [d.strftime("%Y-%m-%d") if isinstance(d, date) else str(d) for d in unique_dates]
        users = [str(user) for user in unique_users]

        # Generate all combinations of dates and users
        date_user_combinations = [{"date": date, "user": user} for date, user in product(dates, users)]
        logger.debug(f"Date user combinations: {date_user_combinations}")
        # print(f"Date user combinations: {date_user_combinations}")
        return date_user_combinations

    @classmethod
    def get_incorrect_counts_by_user(cls, start_date, end_date) -> list:
        """
        Retrieve and process daily incorrect counts for each user within the date range.
        Fills missing data with zeros for combinations of date and user not in the database.
        """
        date_user_combinations = cls._get_date_user_combinations(start_date, end_date)

        # Get actual incorrect counts from the database
        actual_counts: dict = WordCount.get_daily_incorrect_counts_by_user(start_date, end_date)

        logger.debug(f"Actual incorrect counts: {actual_counts}")

        # Fill missing data with zeros
        result_incorrect_count_by_user_by_date = []
        for entry in date_user_combinations:
            date_key = datetime.strptime(entry["date"], "%Y-%m-%d").date() if isinstance(entry["date"], str) else entry["date"]
            user_key = entry["user"]
            # Look up the actual count using the date and user as a key
            actual_count = actual_counts.get((date_key, user_key), 0)
            key = (entry["date"], entry["user"])
            result_incorrect_count_by_user_by_date.append({
                "date": entry["date"],
                "user": entry["user"],
                "total_incorrect_count": int(actual_count) # Use tuple keys to match `actual_counts`
            })
        logger.debug(f"Result incorrect count by user by date: {result_incorrect_count_by_user_by_date}")
        # Sort the results by date in ascending order
        result_incorrect_count_by_user_by_date = sorted(result_incorrect_count_by_user_by_date, key=lambda x: x["date"])
        return result_incorrect_count_by_user_by_date

    @classmethod
    def get_correct_counts_by_user(cls, start_date, end_date) -> list:
        """
        Retrieve and process daily correct counts for each user within the date range.
        Fills missing data with zeros for combinations of date and user not in the database.
        """
        date_user_combinations = cls._get_date_user_combinations(start_date, end_date)

        # Get actual correct counts from the database
        actual_counts: dict = WordCount.get_daily_correct_counts_by_user(start_date, end_date)

        logger.debug(f"Actual correct counts: {actual_counts}")

        result_correct_count_by_user_by_date = []

        for entry in date_user_combinations:
            date_key = datetime.strptime(entry["date"], "%Y-%m-%d").date() if isinstance(entry["date"], str) else entry["date"]
            user_key = entry["user"]
            # Look up the actual count using the date and user as a key
            actual_count = actual_counts.get((date_key, user_key), 0)
            key = (entry["date"], entry["user"])
            result_correct_count_by_user_by_date.append({
                "date": entry["date"],
                "user": entry["user"],
                "total_correct_count": int(actual_count)  # Use tuple keys to match `actual_counts`
            })
        logger.debug(f"Result correct count by user by date: {result_correct_count_by_user_by_date}")
        # Sort the results by date in ascending order
        result_correct_count_by_user_by_date = sorted(result_correct_count_by_user_by_date, key=lambda x: x["date"])
        return result_correct_count_by_user_by_date