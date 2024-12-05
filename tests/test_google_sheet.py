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

    @patch('services.google_sheet_service.gspread.authorize')
    @patch('services.google_sheet_service.Credentials.from_service_account_info')
    def test_authorize(self, mock_from_service_account_info, mock_authorize):
        mock_gc = MagicMock()
        mock_authorize.return_value = mock_gc
        service = GoogleSheetsService(self.service_account_info, self.spreadsheet_id)
        self.assertEqual(service.gc, mock_gc)

    @patch('services.google_sheet_service.gspread.authorize')
    @patch('services.google_sheet_service.Credentials.from_service_account_info')
    def test_get_worksheet(self, mock_from_service_account_info, mock_authorize):
        mock_gc = MagicMock()
        mock_authorize.return_value = mock_gc
        mock_worksheet = MagicMock()
        mock_gc.open_by_key.return_value.sheet1 = mock_worksheet
        service = GoogleSheetsService(self.service_account_info, self.spreadsheet_id)
        self.assertEqual(service.worksheet, mock_worksheet)

if __name__ == '__main__':
    unittest.main()
