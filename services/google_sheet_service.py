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
                worksheet.update('A1:C1', [['Word', 'Definition', 'Last Updated']])
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
            # Trim inputs to avoid issues
            word = str(word).strip()
            definition = str(definition).strip()
            
            # Skip empty words or definitions
            if not word or not definition:
                logger.warning("Skipping empty word or definition")
                return False
                
            # Get the Vocabulary worksheet
            vocab_worksheet = self._get_worksheet('Vocabulary')
            
            # Add timestamp as third column
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if the word already exists
            try:
                word_col = vocab_worksheet.col_values(1)
                word_lower = word.lower()
                found = False
                
                # Case-insensitive search
                for i, existing_word in enumerate(word_col):
                    if existing_word and existing_word.lower() == word_lower:
                        # Word exists, update its definition
                        row_idx = i + 1  # +1 because sheets are 1-indexed
                        vocab_worksheet.update_cell(row_idx, 2, definition)
                        vocab_worksheet.update_cell(row_idx, 3, timestamp)
                        logger.info(f"Updated definition for word '{word}' in Google Sheets")
                        found = True
                        break
                
                if not found:
                    # Word doesn't exist, append new row
                    vocab_worksheet.append_row([word, definition, timestamp])
                    logger.info(f"Added new word '{word}' to Google Sheets")
                
                return True
            except ValueError:
                # Word not found, append it
                vocab_worksheet.append_row([word, definition, timestamp])
                logger.info(f"Added new word '{word}' to Google Sheets")
                return True
                
        except Exception as e:
            logger.error(f"Error saving vocabulary word to Google Sheets: {e}")
            return False

    def save_math_problem(self, problem):
        """Save a math problem to the MathProblems worksheet."""
        try:
            # Skip if problem is None or not a dict
            if not problem or not isinstance(problem, dict):
                logger.warning("Invalid problem object - not saving to Google Sheets")
                return False
                
            # Get the MathProblems worksheet
            math_worksheet = self._get_worksheet('MathProblems')
            
            # Get current timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Clean and prepare data
            problem_id = str(problem.get('id', '')).strip()
            question = str(problem.get('question', '')).strip()
            
            # Skip if no ID or question
            if not problem_id or not question:
                logger.warning(f"Skipping problem with missing ID or question: {problem_id}")
                return False
            
            # Convert answer to string
            answer = problem.get('correct_answer', '')
            if isinstance(answer, (int, float)):
                answer = str(answer)
            else:
                answer = str(answer).strip()
            
            # Prepare the row data
            row_data = [
                problem_id,
                question,
                answer,
                str(problem.get('category', '')).strip(),
                str(problem.get('topic', '')).strip(),
                str(problem.get('difficulty', '')).strip(),
                str(problem.get('explanation', '')).strip(),
                timestamp
            ]
            
            # Check if problem with this ID already exists
            try:
                id_col = math_worksheet.col_values(1)
                if problem_id in id_col:
                    # Problem exists, skip it to avoid duplicates
                    logger.info(f"Problem ID {problem_id} already exists in Google Sheets, skipping")
                    return True
            except Exception as e:
                logger.warning(f"Error checking for existing problem: {e}")
            
            # Append the row to the worksheet
            math_worksheet.append_row(row_data)
            logger.info(f"Saved math problem ID {problem_id} to Google Sheets")
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