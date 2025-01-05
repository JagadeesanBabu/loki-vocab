import json
import gspread
from google.oauth2.service_account import Credentials
import logging
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self, service_account_info, spreadsheet_id):
        self.service_account_info = json.loads(service_account_info)
        self.spreadsheet_id = spreadsheet_id
        self.gc = self._authorize()
        self.worksheet = self._get_worksheet()

    def _authorize(self):
        """Authorize the Google Sheets API client."""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(
            self.service_account_info, scopes=scope
        )
        return gspread.authorize(credentials)

    def _get_worksheet(self):
        """Get the first worksheet of the spreadsheet."""
        return self.gc.open_by_key(self.spreadsheet_id).sheet1

    def load_words(self):
        """Load words from the first column of the Google Sheet."""
        try:
            values = self.worksheet.col_values(1)  # Get all values in column 1
            words = values[1:]  # Skip the header row
            return words
        except Exception as e:
            logger.error(f"Error loading words from Google Sheets: {e}")
            return []