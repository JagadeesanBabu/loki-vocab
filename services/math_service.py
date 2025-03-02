import random
import json
from flask import session
from services.auth_service import clear_session_files
from services.openai_service import generate_math_problem, generate_problem_explanation
import logging
logger = logging.getLogger(__name__)

# GL school level categories and topics
MATH_CATEGORIES = {
    'Number': [
        'Place value', 'Ordering', 'Rounding', 'Number properties', 
        'Fractions', 'Decimals', 'Percentages', 'Ratio and proportion',
        'Mental math', 'Calculator skills'
    ],
    'Algebra': [
        'Sequences', 'Function machines', 'Substitution', 'Simple equations',
        'Formulae', 'Expressions'
    ],
    'Geometry': [
        'Properties of shapes', 'Angles', 'Symmetry', 'Coordinates',
        'Perimeter and area', 'Volume', 'Transformations'
    ],
    'Measures': [
        'Time', 'Money', 'Length', 'Mass', 'Capacity', 'Units conversion'
    ],
    'Statistics': [
        'Data collection', 'Data presentation', 'Averages', 'Probability'
    ],
    'Problem Solving': [
        'Multi-step problems', 'Word problems', 'Logical reasoning', 
        'Visual puzzles', 'Pattern recognition'
    ]
}

# Difficulty levels
DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']

# Sample problems (will be replaced by OpenAI API call)
SAMPLE_PROBLEMS = [
    {
        'id': 1,
        'question': 'Emma has 24 marbles. She gives 1/3 of her marbles to Jack and 1/4 of the remaining marbles to Sarah. How many marbles does Emma have left?',
        'correct_answer': 12,
        'category': 'Number',
        'topic': 'Fractions',
        'difficulty': 'medium',
        'explanation': 'Emma starts with 24 marbles. She gives 1/3 of them to Jack, which is 24 × (1/3) = 8 marbles. So Emma has 24 - 8 = 16 marbles left. Then she gives 1/4 of these 16 marbles to Sarah, which is 16 × (1/4) = 4 marbles. So Emma has 16 - 4 = 12 marbles left.'
    },
    {
        'id': 2,
        'question': 'A rectangular garden is 15 meters long and 10 meters wide. What is the area of the garden in square meters?',
        'correct_answer': 150,
        'category': 'Geometry',
        'topic': 'Perimeter and area',
        'difficulty': 'easy',
        'explanation': 'The area of a rectangle is calculated by multiplying the length by the width. So the area is 15 meters × 10 meters = 150 square meters.'
    },
    {
        'id': 3,
        'question': 'If 5 workers can build a wall in 6 days, how many days would it take 3 workers to build the same wall, assuming all workers work at the same rate?',
        'correct_answer': 10,
        'category': 'Number',
        'topic': 'Ratio and proportion',
        'difficulty': 'hard',
        'explanation': 'This is an inverse proportion problem. The time taken is inversely proportional to the number of workers. So if the number of workers decreases, the time increases proportionally. We can set up the equation: 5 workers × 6 days = 3 workers × x days. Solving for x: x = (5 × 6) ÷ 3 = 30 ÷ 3 = 10 days.'
    }
]

def reset_math_score():
    """Resets the user's math score."""
    if 'math_score' in session:
        session['math_score'] = {'correct': 0, 'incorrect': 0}
    if 'math_problems_today' in session:
        session['math_problems_today'] = 0
    if 'incorrect_math_answers' in session:
        session['incorrect_math_answers'] = []
    session.modified = True

def get_random_problem_params():
    """Generates random problem parameters for variety."""
    category = random.choice(list(MATH_CATEGORIES.keys()))
    topic = random.choice(MATH_CATEGORIES[category])
    difficulty = random.choice(DIFFICULTY_LEVELS)
    
    return {
        'category': category,
        'topic': topic,
        'difficulty': difficulty
    }

def get_next_math_problem():
    """Fetches the next math problem with options."""
    from config import Config
    from services.google_sheet_service import GoogleSheetsService
    
    # Check if we have cached problems
    if 'math_problems' not in session:
        # First, try to load problems from Google Sheets
        try:
            service_account_file_info = Config.GOOGLE_CREDENTIALS_JSON
            spreadsheet_id = Config.SPREADSHEET_ID
            sheets_service = GoogleSheetsService(service_account_file_info, spreadsheet_id)
            loaded_problems = sheets_service.load_math_problems()
            
            if loaded_problems:
                logger.info(f"Loaded {len(loaded_problems)} math problems from Google Sheets")
                session['math_problems'] = loaded_problems
                session['sheet_service'] = {'service_account_info': service_account_file_info, 'spreadsheet_id': spreadsheet_id}
            else:
                logger.info("No math problems found in Google Sheets, generating new ones")
                session['math_problems'] = []
        except Exception as e:
            logger.error(f"Error loading math problems from Google Sheets: {e}")
            session['math_problems'] = []
    
    # If we have no problems (either no cached or no loaded), generate some
    if not session.get('math_problems'):
        # Generate more problems using OpenAI API
        new_problems = []
        
        # Generate just 1 problem to start (to avoid timeouts)
        # We'll generate more problems in the background later
        params = get_random_problem_params()
        try:
            problem = generate_math_problem(
                category=params['category'], 
                topic=params['topic'], 
                difficulty=params['difficulty']
            )
            if problem:
                # Generate a unique ID for the problem
                from uuid import uuid4
                problem['id'] = str(uuid4())[:8]  # First 8 chars of UUID
                new_problems.append(problem)
                
                # Save to Google Sheets if possible
                if 'sheet_service' in session:
                    try:
                        service_info = session['sheet_service']
                        sheets_service = GoogleSheetsService(
                            service_info['service_account_info'], 
                            service_info['spreadsheet_id']
                        )
                        sheets_service.save_math_problem(problem)
                    except Exception as e:
                        logger.error(f"Error saving problem to Google Sheets: {e}")
        except Exception as e:
            logger.error(f"Error generating math problem: {e}")
        
        # Fall back to sample problems if API fails and we couldn't load any
        if not new_problems:
            new_problems = SAMPLE_PROBLEMS.copy()
        
        session['math_problems'] = new_problems
        session.modified = True
    
    # If we're running low on problems, generate just one more (to avoid timeouts)
    if len(session['math_problems']) < 2:
        new_problems = []
        params = get_random_problem_params()
        try:
            # Generate just 1 more problem to avoid timeouts
            problem = generate_math_problem(
                category=params['category'], 
                topic=params['topic'], 
                difficulty=params['difficulty']
            )
            if problem:
                # Generate a unique ID for the problem
                from uuid import uuid4
                problem['id'] = str(uuid4())[:8]  # First 8 chars of UUID
                new_problems.append(problem)
                
                # Save to Google Sheets if possible
                if 'sheet_service' in session:
                    try:
                        service_info = session['sheet_service']
                        sheets_service = GoogleSheetsService(
                            service_info['service_account_info'], 
                            service_info['spreadsheet_id']
                        )
                        sheets_service.save_math_problem(problem)
                    except Exception as e:
                        logger.error(f"Error saving problem to Google Sheets: {e}")
        except Exception as e:
            logger.error(f"Error generating additional math problems: {e}")
        
        session['math_problems'].extend(new_problems)
        session.modified = True
    
    # Pick a random problem from the list
    problem = random.choice(session['math_problems'])
    
    # Remove the selected problem from the list to avoid repetition in this session
    session['math_problems'] = [p for p in session['math_problems'] if p.get('id') != problem.get('id')]
    session.modified = True
    
    return {
        'problem': problem,
        'correct_answer': problem['correct_answer']
    }

def check_math_answer(user_answer, problem, correct_answer):
    """Checks the user's answer to a math problem and updates the score."""
    
    # Compare answers, with flexibility for numeric values
    is_correct = False
    
    # Convert both to same type if possible
    if isinstance(user_answer, (int, float)) and isinstance(correct_answer, (int, float)):
        # For numerical answers, allow small differences due to rounding
        is_correct = abs(user_answer - correct_answer) < 0.001
    else:
        # For string answers, exact match required
        is_correct = str(user_answer).lower() == str(correct_answer).lower()
    
    explanation = problem.get('explanation', '')
    
    # If no explanation exists, generate one
    if not explanation and is_correct is False:
        try:
            explanation = generate_problem_explanation(problem['question'], correct_answer)
        except Exception as e:
            logger.error(f"Error generating problem explanation: {e}")
            explanation = "No explanation available."
    
    if is_correct:
        session['math_score']['correct'] += 1
        result_message = f"Correct! The answer is {correct_answer}."
        answer_status = "correct"
    else:
        session['math_score']['incorrect'] += 1
        result_message = f"Incorrect. The correct answer is {correct_answer}."
        answer_status = "incorrect"
        
        # Store the incorrect answer details for the summary page
        if 'incorrect_math_answers' not in session:
            session['incorrect_math_answers'] = []
        session['incorrect_math_answers'].append({
            'question': problem['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': explanation
        })
    
    return {
        'result_message': result_message,
        'correct_answer': correct_answer,
        'answer_status': answer_status,
        'updated_score': session['math_score'],
        'explanation': explanation
    }

def get_math_summary():
    """Aggregates the summary of math problem results."""
    correct_answers = session.get('math_score', {}).get('correct', 0)
    incorrect_answers = session.get('math_score', {}).get('incorrect', 0)
    total_answers = correct_answers + incorrect_answers
    return {
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'total_answers': total_answers,
        'incorrect_answer_details': session.get('incorrect_math_answers', [])
    }