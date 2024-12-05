import unittest
from unittest.mock import patch, MagicMock
from services.google_sheet_service import GoogleSheetsService

class TestGoogleSheetsService(unittest.TestCase):

    @patch('services.google_sheet_service.gspread.authorize')
    @patch('services.google_sheet_service.Credentials.from_service_account_info')
    def setUp(self, mock_from_service_account_info, mock_authorize):
        self.mock_gc = MagicMock()
        mock_authorize.return_value = self.mock_gc
        self.mock_worksheet = MagicMock()
        self.mock_gc.open_by_key.return_value.sheet1 = self.mock_worksheet

        self.service_account_info = '{"type": "service_account", "project_id": "test_project"}'
        self.spreadsheet_id = 'test_spreadsheet_id'
        self.service = GoogleSheetsService(self.service_account_info, self.spreadsheet_id)

    def test_load_words(self):
        self.mock_worksheet.col_values.return_value = ['Header', 'word1', 'word2', 'word3']
        words = self.service.load_words()
        self.assertEqual(words, ['word1', 'word2', 'word3'])

    def test_load_words_empty(self):
        self.mock_worksheet.col_values.return_value = ['Header']
        words = self.service.load_words()
        self.assertEqual(words, [])

    def test_load_words_exception(self):
        self.mock_worksheet.col_values.side_effect = Exception("Test exception")
        words = self.service.load_words()
        self.assertEqual(words, [])

if __name__ == '__main__':
    unittest.main()
