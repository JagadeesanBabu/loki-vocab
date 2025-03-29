import random
import json
from flask import session
from services.auth_service import clear_session_files
from services.optimization_service import OpenAIOptimizer, MathSheetsOptimizer
import logging
from flask_login import current_user
from datetime import datetime

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
    clear_session_files()
    session['math_score'] = {'correct': 0, 'incorrect': 0}
    session.modified = True

async def get_next_math_problem():
    """Gets the next math problem."""
    # Randomly select category, topic, and difficulty
    category = random.choice(list(MATH_CATEGORIES.keys()))
    topic = random.choice(MATH_CATEGORIES[category])
    difficulty = random.choice(DIFFICULTY_LEVELS)
    
    try:
        # Use optimized OpenAI service to generate problem
        problem = await OpenAIOptimizer.generate_math_problem(category, topic, difficulty)
        if not problem:
            logger.error("Failed to generate math problem")
            return None
            
        # Add unique ID if not present
        if 'id' not in problem:
            problem['id'] = f"{category}_{topic}_{difficulty}_{random.randint(1000, 9999)}"
        
        # Queue update to Google Sheets in background
        MathSheetsOptimizer.queue_update(problem)
        
        return problem
    except Exception as e:
        logger.error(f"Error generating math problem: {e}")
        return None

async def check_math_answer(user_answer, problem):
    """Checks the user's answer to a math problem and updates the score."""
    if not problem or 'correct_answer' not in problem:
        return {
            'result_message': "Error: Invalid problem data",
            'answer_status': "error",
            'updated_score': session.get('math_score', {'correct': 0, 'incorrect': 0}),
            'explanation': "Could not verify answer due to missing problem data."
        }
    
    correct_answer = problem['correct_answer']
    is_visual = problem.get('is_visual', False)
    
    # Compare answers, with flexibility for numeric values
    is_correct = False
    
    if is_visual:
        # For visual puzzles, do a more flexible string comparison
        user_answer = str(user_answer).lower().strip()
        correct_answer = str(correct_answer).lower().strip()
        # Split into words and check if key elements are present
        user_words = set(user_answer.split())
        correct_words = set(correct_answer.split())
        # Calculate similarity score
        common_words = user_words.intersection(correct_words)
        similarity_score = len(common_words) / max(len(user_words), len(correct_words))
        is_correct = similarity_score > 0.7  # Consider correct if 70% similar
    else:
        # For regular math problems, use numeric comparison
        try:
            if isinstance(correct_answer, (int, float)):
                user_answer = float(user_answer)
                is_correct = abs(user_answer - float(correct_answer)) < 0.001
            else:
                is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
        except ValueError:
            # If conversion fails, do string comparison
            is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
    
    # Get or generate explanation
    explanation = problem.get('explanation', '')
    if is_visual:
        pattern_explanation = problem.get('pattern_explanation', '')
        if pattern_explanation:
            explanation = f"{explanation}\n\nPattern: {pattern_explanation}"
    elif not explanation and not is_correct:
        try:
            explanation = await OpenAIOptimizer.generate_problem_explanation(
                problem['question'],
                str(correct_answer)
            )
        except Exception as e:
            logger.error(f"Error generating problem explanation: {e}")
            explanation = "Explanation not available at the moment."
    
    # Initialize or update score in session
    if 'math_score' not in session:
        session['math_score'] = {'correct': 0, 'incorrect': 0}
    
    if is_correct:
        session['math_score']['correct'] += 1
        result_message = "Correct! " + (f"The pattern continues with {correct_answer}." if is_visual else f"The answer is {correct_answer}.")
        answer_status = "correct"
    else:
        session['math_score']['incorrect'] += 1
        result_message = "Incorrect. " + (f"The pattern continues with {correct_answer}." if is_visual else f"The correct answer is {correct_answer}.")
        answer_status = "incorrect"
        
        # Store incorrect answer for summary
        if 'incorrect_math_answers' not in session:
            session['incorrect_math_answers'] = []
        incorrect_answer = {
            'question': problem['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'is_visual': is_visual
        }
        if is_visual and 'figures' in problem:
            incorrect_answer['figures'] = problem['figures']
        session['incorrect_math_answers'].append(incorrect_answer)
    
    # Ensure session is marked as modified
    session.modified = True
    
    # Queue stats update to Google Sheets
    stats_data = {
        'user': current_user.username if current_user and current_user.is_authenticated else 'anonymous',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'category': problem.get('category', ''),
        'difficulty': problem.get('difficulty', ''),
        'correct': 1 if is_correct else 0,
        'incorrect': 0 if is_correct else 1,
        'total_time': session.get('last_answer_time', 0),
        'avg_time': session.get('last_answer_time', 0),  # For now, just use the last time
        'is_visual': is_visual
    }
    
    # Force immediate update to Google Sheets
    MathSheetsOptimizer.queue_stats_update(stats_data)
    
    return {
        'result_message': result_message,
        'answer_status': answer_status,
        'updated_score': session['math_score'],
        'explanation': explanation
    }

def get_math_summary():
    """Gets the summary of math practice session."""
    return {
        'correct_answers': session.get('math_score', {}).get('correct', 0),
        'incorrect_answers': session.get('math_score', {}).get('incorrect', 0),
        'incorrect_answer_details': session.get('incorrect_math_answers', [])
    }