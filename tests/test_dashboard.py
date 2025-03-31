import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from services.dashboard_service import DashboardService

class TestDashboardService(unittest.TestCase):

    @patch('services.dashboard_service.WordCount.get_unique_dates')
    @patch('services.dashboard_service.WordCount.get_unique_users')
    @patch('services.dashboard_service.WordCount.get_daily_correct_counts_by_user')
    def test_get_correct_counts_by_user(self, mock_get_daily_correct_counts_by_user, mock_get_unique_users, mock_get_unique_dates):
        mock_get_unique_dates.return_value = [datetime(2023, 9, 1).date(), datetime(2023, 9, 2).date()]
        mock_get_unique_users.return_value = ['user1', 'user2']
        mock_get_daily_correct_counts_by_user.return_value = {
            (datetime(2023, 9, 1).date(), 'user1'): 5,
            (datetime(2023, 9, 2).date(), 'user2'): 3
        }

        start_date = datetime(2023, 9, 1).date()
        end_date = datetime(2023, 9, 2).date()
        result = DashboardService.get_correct_counts_by_user(start_date, end_date)

        expected_result = [
            {'date': '2023-09-01', 'user': 'user1', 'total_correct_count': 5},
            {'date': '2023-09-01', 'user': 'user2', 'total_correct_count': 0},
            {'date': '2023-09-02', 'user': 'user1', 'total_correct_count': 0},
            {'date': '2023-09-02', 'user': 'user2', 'total_correct_count': 3}
        ]

        self.assertEqual(result, expected_result)

    @patch('services.dashboard_service.WordCount.get_unique_dates')
    @patch('services.dashboard_service.WordCount.get_unique_users')
    @patch('services.dashboard_service.WordCount.get_daily_incorrect_counts_by_user')
    def test_get_incorrect_counts_by_user(self, mock_get_daily_incorrect_counts_by_user, mock_get_unique_users, mock_get_unique_dates):
        mock_get_unique_dates.return_value = [datetime(2023, 9, 1).date(), datetime(2023, 9, 2).date()]
        mock_get_unique_users.return_value = ['user1', 'user2']
        mock_get_daily_incorrect_counts_by_user.return_value = {
            (datetime(2023, 9, 1).date(), 'user1'): 2,
            (datetime(2023, 9, 2).date(), 'user2'): 4
        }

        start_date = datetime(2023, 9, 1).date()
        end_date = datetime(2023, 9, 2).date()
        result = DashboardService.get_incorrect_counts_by_user(start_date, end_date)

        expected_result = [
            {'date': '2023-09-01', 'user': 'user1', 'total_incorrect_count': 2},
            {'date': '2023-09-01', 'user': 'user2', 'total_incorrect_count': 0},
            {'date': '2023-09-02', 'user': 'user1', 'total_incorrect_count': 0},
            {'date': '2023-09-02', 'user': 'user2', 'total_incorrect_count': 4}
        ]

        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
