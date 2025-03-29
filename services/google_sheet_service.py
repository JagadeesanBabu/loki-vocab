import json
import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime, timedelta
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
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=12)
                # Add headers for math problems
                worksheet.update('A1:L1', [['ID', 'Question', 'Answer', 'Category', 'Topic', 'Difficulty', 'Explanation', 'Created', 'Is Visual', 'Figures', 'Pattern Explanation', 'Image URLs']])
                return worksheet
            elif sheet_name == 'MathStats':
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=9)
                # Add headers for math statistics
                worksheet.update('A1:I1', [['User', 'Date', 'Category', 'Difficulty', 'Correct', 'Incorrect', 'Total Time', 'Average Time', 'Is Visual']])
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
            
            # If no words found, add some default vocabulary words to the worksheet
            if not words:
                logger.info("No words found in Google Sheets. Adding default vocabulary words.")
                default_words = [
                    "abase", "abate", "abdicate", "aberrant", "abeyance", "abhor", "abject", "abjure",
                    "abnegate", "abominate", "aboriginal", "abortive", "abrasive", "abrogate", "abscond",
                    "absolution", "abstain", "abstemious", "abstruse", "abundant", "abut", "abysmal",
                    "accede", "accessible", "accessory", "acclaimed", "accolade", "accomplish", "accord",
                    "accost", "acerbic", "acme", "acquiesce", "acquisitive", "acrimonious", "acumen"
                ]
                
                # Add each word to the sheet
                for word in default_words:
                    try:
                        # Add placeholder definition (will be replaced by OpenAI)
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.worksheet.append_row([word, "Definition will be fetched automatically", timestamp])
                        logger.info(f"Added default word '{word}' to Google Sheets")
                    except Exception as e:
                        logger.error(f"Error adding default word '{word}' to Google Sheets: {e}")
                
                # Return the default words
                return default_words
            
            # Filter out empty strings and strings that only contain whitespace
            words = [word for word in words if word and word.strip()]
            
            return words
        except Exception as e:
            logger.error(f"Error loading words from Google Sheets: {e}")
            # Return default words as fallback if there's an error
            default_words = [
                "abase", "abate", "abdicate", "aberrant", "abeyance", "abhor", "abject", "abjure",
                "abnegate", "abominate", "aboriginal", "abortive", "abrasive", "abrogate", "abscond"
            ]
            logger.info("Returning default vocabulary words due to Google Sheets error")
            return default_words
            
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
            
            # Handle visual puzzle data
            is_visual = problem.get('is_visual', False)
            figures_json = ''
            pattern_explanation = ''
            image_urls = ''
            
            if is_visual:
                if 'figures' in problem:
                    figures_json = json.dumps([{
                        'description': f.get('description', ''),
                        'caption': f.get('caption', '')
                    } for f in problem['figures']])
                    image_urls = json.dumps([f.get('image_url', '') for f in problem['figures']])
                pattern_explanation = str(problem.get('pattern_explanation', '')).strip()
            
            # Prepare the row data
            row_data = [
                problem_id,
                question,
                answer,
                str(problem.get('category', '')).strip(),
                str(problem.get('topic', '')).strip(),
                str(problem.get('difficulty', '')).strip(),
                str(problem.get('explanation', '')).strip(),
                timestamp,
                'true' if is_visual else 'false',
                figures_json,
                pattern_explanation,
                image_urls
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

    def batch_update_words(self, updates):
        """Batch update multiple words at once"""
        try:
            # Get the Vocabulary worksheet
            worksheet = self._get_worksheet('Vocabulary')
            
            # Get all existing words
            word_col = worksheet.col_values(1)
            word_to_row = {word.lower(): idx + 1 for idx, word in enumerate(word_col)}
            
            # Prepare batch updates
            batch_updates = []
            new_rows = []
            
            for update in updates:
                word = update['word'].lower()
                definition = update['definition']
                timestamp = update['timestamp']
                
                if word in word_to_row:
                    # Update existing word
                    row_idx = word_to_row[word]
                    batch_updates.extend([
                        (row_idx, 2, definition),  # Update definition
                        (row_idx, 3, timestamp)    # Update timestamp
                    ])
                else:
                    # Add new word
                    new_rows.append([update['word'], definition, timestamp])
            
            # Execute batch updates for existing words
            if batch_updates:
                cells_to_update = []
                for row, col, value in batch_updates:
                    cells_to_update.append({
                        'range': f'{chr(64+col)}{row}',
                        'values': [[value]]
                    })
                worksheet.batch_update(cells_to_update)
            
            # Add new words in batch
            if new_rows:
                worksheet.append_rows(new_rows)
            
            logger.info(f"Batch updated {len(updates)} words in Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            return False

    def batch_update_math_stats(self, stats_list):
        """Update multiple math statistics entries in batch."""
        try:
            if not stats_list:
                return True

            # Get the MathStats worksheet
            stats_worksheet = self._get_worksheet('MathStats')

            # Prepare batch update data
            rows = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for stats in stats_list:
                row = [
                    str(stats.get('user', '')).strip(),
                    str(stats.get('date', timestamp)).strip(),
                    str(stats.get('category', '')).strip(),
                    str(stats.get('difficulty', '')).strip(),
                    str(stats.get('correct', 0)).strip(),
                    str(stats.get('incorrect', 0)).strip(),
                    str(stats.get('total_time', 0)).strip(),
                    str(stats.get('avg_time', 0)).strip(),
                    'true' if stats.get('is_visual', False) else 'false'
                ]
                rows.append(row)

            # Append all rows at once
            stats_worksheet.append_rows(rows)
            logger.info(f"Saved {len(rows)} math statistics entries to Google Sheets")
            return True

        except Exception as e:
            logger.error(f"Error saving math statistics to Google Sheets: {e}")
            return False

    def get_math_stats(self, user, start_date, end_date):
        """Get math statistics for a user within a date range."""
        try:
            # Get the MathStats worksheet
            stats_worksheet = self._get_worksheet('MathStats')
            
            # Get all values
            all_values = stats_worksheet.get_all_values()
            
            # Skip if only header row or empty
            if len(all_values) <= 1:
                return {
                    'by_category': {},
                    'by_difficulty': {},
                    'daily_correct': [],
                    'daily_incorrect': []
                }
            
            # Process the data
            headers = all_values[0]
            by_category = {}
            by_difficulty = {}
            daily_stats = {}
            
            for row in all_values[1:]:
                # Skip if row is too short
                if len(row) < 6:
                    continue
                    
                row_user = row[0]
                row_date = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").date()
                row_category = row[2]
                row_difficulty = row[3]
                row_correct = int(row[4]) if row[4].isdigit() else 0
                row_incorrect = int(row[5]) if row[5].isdigit() else 0
                
                # Skip if not matching user or date range
                if row_user != user or not (start_date.date() <= row_date <= end_date.date()):
                    continue
                
                # Update category stats
                if row_category not in by_category:
                    by_category[row_category] = {'correct': 0, 'incorrect': 0}
                by_category[row_category]['correct'] += row_correct
                by_category[row_category]['incorrect'] += row_incorrect
                
                # Update difficulty stats
                if row_difficulty not in by_difficulty:
                    by_difficulty[row_difficulty] = {'correct': 0, 'incorrect': 0}
                by_difficulty[row_difficulty]['correct'] += row_correct
                by_difficulty[row_difficulty]['incorrect'] += row_incorrect
                
                # Update daily stats
                date_str = row_date.strftime("%Y-%m-%d")
                if date_str not in daily_stats:
                    daily_stats[date_str] = {'correct': 0, 'incorrect': 0}
                daily_stats[date_str]['correct'] += row_correct
                daily_stats[date_str]['incorrect'] += row_incorrect
            
            # Convert daily stats to lists
            dates = []
            daily_correct = []
            daily_incorrect = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                dates.append(date_str)
                stats = daily_stats.get(date_str, {'correct': 0, 'incorrect': 0})
                daily_correct.append(stats['correct'])
                daily_incorrect.append(stats['incorrect'])
                current_date += timedelta(days=1)
            
            return {
                'by_category': by_category,
                'by_difficulty': by_difficulty,
                'daily_correct': daily_correct,
                'daily_incorrect': daily_incorrect
            }
            
        except Exception as e:
            logger.error(f"Error getting math statistics from Google Sheets: {e}")
            return {
                'by_category': {},
                'by_difficulty': {},
                'daily_correct': [],
                'daily_incorrect': []
            }