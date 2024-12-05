import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from services.dashboard_service import DashboardService
from database.models import WordCount

class TestDashboardService(unittest.TestCase):

    @patch('services.dashboard_service.WordCount.get_unique_dates')
    @patch('services.dashboard_service.WordCount.get_unique_users')
    @patch('services.dashboard_service.WordCount.get_daily_incorrect_counts_by_user')
    def test_get_incorrect_counts_by_user(self, mock_get_daily_incorrect_counts_by_user, mock_get_unique_users, mock_get_unique_dates):
        # Mock data
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        mock_get_unique_dates.return_value = [start_date + timedelta(days=i) for i in range(31)]
        mock_get_unique_users.return_value = ['user1', 'user2']
        mock_get_daily_incorrect_counts_by_user.return_value = {
            (start_date, 'user1'): 5,
            (start_date + timedelta(days=1), 'user2'): 3
        }

        result = DashboardService.get_incorrect_counts_by_user(start_date, end_date)

        self.assertEqual(len(result), 62)  # 31 days * 2 users
        self.assertEqual(result[0]['total_incorrect_count'], 5)
        self.assertEqual(result[1]['total_incorrect_count'], 0)

    @patch('services.dashboard_service.WordCount.get_unique_dates')
    @patch('services.dashboard_service.WordCount.get_unique_users')
    @patch('services.dashboard_service.WordCount.get_daily_correct_counts_by_user')
    def test_get_correct_counts_by_user(self, mock_get_daily_correct_counts_by_user, mock_get_unique_users, mock_get_unique_dates):
        # Mock data
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        mock_get_unique_dates.return_value = [start_date + timedelta(days=i) for i in range(31)]
        mock_get_unique_users.return_value = ['user1', 'user2']
        mock_get_daily_correct_counts_by_user.return_value = {
            (start_date, 'user1'): 10,
            (start_date + timedelta(days=1), 'user2'): 7
        }

        result = DashboardService.get_correct_counts_by_user(start_date, end_date)

        self.assertEqual(len(result), 62)  # 31 days * 2 users
        self.assertEqual(result[0]['total_correct_count'], 10)
        self.assertEqual(result[1]['total_correct_count'], 0)

if __name__ == '__main__':
    unittest.main()
