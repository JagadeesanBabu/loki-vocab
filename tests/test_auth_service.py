import os
import unittest
from unittest.mock import patch, MagicMock
from services.auth_service import authenticate_user, clear_session_files
from database.models import User

class TestAuthService(unittest.TestCase):

    def test_authenticate_user_valid(self):
        user = authenticate_user("loke", "latha")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "loke")

        user = authenticate_user("adarsh", "sridhar")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "adarsh")

    def test_authenticate_user_invalid(self):
        user = authenticate_user("invalid", "user")
        self.assertIsNone(user)

    @patch('services.auth_service.os.path.exists')
    @patch('services.auth_service.glob.glob')
    @patch('services.auth_service.os.remove')
    def test_clear_session_files(self, mock_remove, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = ['file1', 'file2']

        clear_session_files()

        mock_remove.assert_any_call('file1')
        mock_remove.assert_any_call('file2')
        self.assertEqual(mock_remove.call_count, 2)

    @patch('services.auth_service.os.path.exists')
    @patch('services.auth_service.glob.glob')
    @patch('services.auth_service.os.remove')
    def test_clear_session_files_no_folder(self, mock_remove, mock_glob, mock_exists):
        mock_exists.return_value = False

        clear_session_files()

        mock_remove.assert_not_called()
        mock_glob.assert_not_called()

if __name__ == '__main__':
    unittest.main()
