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
        self.worksheet = self._get_worksheet('Vocabulary')  # Default to vocabulary worksheet

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

    def _get_worksheet(self, sheet_name='Vocabulary'):
        """Get the specified worksheet of the spreadsheet."""
        spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
        
        # Try to get the specified worksheet
        try:
            return spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # If the worksheet doesn't exist, create it
            logger.info(f"Worksheet '{sheet_name}' not found. Creating it.")
            if sheet_name == 'Vocabulary':
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=5)
                # Add headers for vocabulary
                worksheet.update('A1:B1', [['Word', 'Definition']])
                return worksheet
            elif sheet_name == 'MathProblems':
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
                # Add headers for math problems
                worksheet.update('A1:H1', [['ID', 'Question', 'Answer', 'Category', 'Topic', 'Difficulty', 'Explanation', 'Created']])
                return worksheet
            else:
                # Generic worksheet
                return spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=5)

    def load_words(self):
        """Load words from the first column of the Vocabulary worksheet."""
        try:
            # Make sure we're using the Vocabulary worksheet
            self.worksheet = self._get_worksheet('Vocabulary')
            values = self.worksheet.col_values(1)  # Get all values in column 1
            words = values[1:]  # Skip the header row
            return words
        except Exception as e:
            logger.error(f"Error loading words from Google Sheets: {e}")
            return []
            
    def save_vocabulary_word(self, word, definition):
        """Save a vocabulary word and its definition to the vocabulary worksheet."""
        try:
            # Get the Vocabulary worksheet
            vocab_worksheet = self._get_worksheet('Vocabulary')
            
            # Check if the word already exists
            try:
                word_col = vocab_worksheet.col_values(1)
                if word in word_col:
                    # Word exists, update its definition
                    row_idx = word_col.index(word) + 1  # +1 because sheets are 1-indexed
                    vocab_worksheet.update_cell(row_idx, 2, definition)
                    logger.info(f"Updated definition for word '{word}' in Google Sheets")
                else:
                    # Word doesn't exist, append new row
                    vocab_worksheet.append_row([word, definition])
                    logger.info(f"Added new word '{word}' to Google Sheets")
                return True
            except ValueError:
                # Word not found, append it
                vocab_worksheet.append_row([word, definition])
                logger.info(f"Added new word '{word}' to Google Sheets")
                return True
                
        except Exception as e:
            logger.error(f"Error saving vocabulary word to Google Sheets: {e}")
            return False

    def save_math_problem(self, problem):
        """Save a math problem to the MathProblems worksheet."""
        try:
            # Get the MathProblems worksheet
            math_worksheet = self._get_worksheet('MathProblems')
            
            # Get current timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare the row data
            row_data = [
                problem.get('id', ''),
                problem.get('question', ''),
                str(problem.get('correct_answer', '')),
                problem.get('category', ''),
                problem.get('topic', ''),
                problem.get('difficulty', ''),
                problem.get('explanation', ''),
                timestamp
            ]
            
            # Append the row to the worksheet
            math_worksheet.append_row(row_data)
            logger.info(f"Saved math problem ID {problem.get('id')} to Google Sheets")
            return True
        except Exception as e:
            logger.error(f"Error saving math problem to Google Sheets: {e}")
            return False
            
    def load_math_problems(self):
        """Load all math problems from the MathProblems worksheet."""
        try:
            # Get the MathProblems worksheet
            math_worksheet = self._get_worksheet('MathProblems')
            
            # Get all values
            all_values = math_worksheet.get_all_values()
            
            # Skip header row
            if len(all_values) <= 1:  # Only header row or empty
                return []
                
            # Extract data and convert to list of dictionaries
            headers = all_values[0]
            problems = []
            
            for row in all_values[1:]:
                problem = {}
                for i, header in enumerate(headers):
                    if i < len(row):  # Ensure row has enough values
                        # Handle special types (convert numeric strings)
                        if header == 'ID':
                            try:
                                problem[header.lower()] = int(row[i])
                            except ValueError:
                                problem[header.lower()] = row[i]
                        elif header == 'Answer':
                            # Try to convert to numeric if possible
                            try:
                                if '.' in row[i]:
                                    problem['correct_answer'] = float(row[i])
                                else:
                                    problem['correct_answer'] = int(row[i])
                            except ValueError:
                                problem['correct_answer'] = row[i]
                        else:
                            # Map header names to expected problem keys
                            key = header.lower()
                            if key == 'question':
                                problem[key] = row[i]
                            elif key == 'explanation':
                                problem[key] = row[i]
                            elif key == 'category':
                                problem[key] = row[i]
                            elif key == 'topic':
                                problem[key] = row[i]
                            elif key == 'difficulty':
                                problem[key] = row[i]
                            # Ignore created timestamp in problem object
                
                if problem:  # Only add non-empty problems
                    problems.append(problem)
            
            return problems
        except Exception as e:
            logger.error(f"Error loading math problems from Google Sheets: {e}")
            return []