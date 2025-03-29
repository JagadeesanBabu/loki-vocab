import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from collections import defaultdict
import logging
import aiohttp
from openai import OpenAI, AsyncOpenAI, RateLimitError, APIError
from config import Config
from services.google_sheet_service import GoogleSheetsService

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
async_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class PersistentCache:
    """A cache that persists data to disk periodically."""
    def __init__(self, cache_file: str = 'word_cache.json'):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.last_save = time.time()
        self.save_interval = 300  # 5 minutes

    def _load_cache(self) -> Dict:
        """Load cache from disk."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
            self.last_save = time.time()
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get(self, key: str) -> Optional[Dict]:
        """Get value from cache."""
        return self.cache.get(key)

    def set(self, key: str, value: Dict):
        """Set value in cache and save if needed."""
        self.cache[key] = value
        if time.time() - self.last_save > self.save_interval:
            self._save_cache()

class OpenAIOptimizer:
    """Optimizes OpenAI API usage through batching and caching."""
    _cache = PersistentCache()
    _token_usage = {'total': 0, 'prompt': 0, 'completion': 0}

    @classmethod
    async def fetch_word_data(cls, word: str) -> Dict:
        """Fetch word data from OpenAI API with caching."""
        cached_data = cls._cache.get(word)
        if cached_data:
            logger.info(f"Cache hit for word: {word}")
            return cached_data

        try:
            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a vocabulary teacher providing concise definitions and related words."},
                    {"role": "user", "content": f"""Define the word '{word}' and provide incorrect options and similar words. Format as JSON:
{{
    "definition": "A clear, single-sentence definition without elaboration",
    "incorrect_options": ["short incorrect definition 1", "short incorrect definition 2", "short incorrect definition 3"],
    "similar_words": [
        {{
            "word": "similar_word1",
            "definition": "brief definition of similar word 1"
        }},
        {{
            "word": "similar_word2",
            "definition": "brief definition of similar word 2"
        }},
        {{
            "word": "similar_word3",
            "definition": "brief definition of similar word 3"
        }}
    ]
}}
Keep all definitions under 15 words. Make incorrect options plausible but clearly wrong."""}
                ]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            try:
                word_data = json.loads(content)
                # Validate the response format
                required_keys = ['definition', 'incorrect_options', 'similar_words']
                if not all(key in word_data for key in required_keys):
                    logger.error(f"Invalid response format for word '{word}': missing required keys")
                    return cls._get_fallback_word_data(word)
                if not isinstance(word_data['incorrect_options'], list) or not isinstance(word_data['similar_words'], list):
                    logger.error(f"Invalid response format for word '{word}': arrays not properly formatted")
                    return cls._get_fallback_word_data(word)
                if len(word_data['incorrect_options']) != 3 or len(word_data['similar_words']) != 3:
                    logger.error(f"Invalid response format for word '{word}': wrong number of options/similar words")
                    return cls._get_fallback_word_data(word)
                
                # Ensure definitions are concise
                if len(word_data['definition'].split()) > 15:
                    word_data['definition'] = ' '.join(word_data['definition'].split()[:15]) + '.'
                for i, opt in enumerate(word_data['incorrect_options']):
                    if len(opt.split()) > 15:
                        word_data['incorrect_options'][i] = ' '.join(opt.split()[:15]) + '.'
                for word_obj in word_data['similar_words']:
                    if len(word_obj['definition'].split()) > 15:
                        word_obj['definition'] = ' '.join(word_obj['definition'].split()[:15]) + '.'
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response for word '{word}'")
                return cls._get_fallback_word_data(word)
            
            # Update token usage
            cls._token_usage['prompt'] += response.usage.prompt_tokens
            cls._token_usage['completion'] += response.usage.completion_tokens
            cls._token_usage['total'] += response.usage.total_tokens
            
            # Cache the result
            cls._cache.set(word, word_data)
            return word_data
            
        except RateLimitError:
            logger.error("Rate limit exceeded")
            return cls._get_fallback_word_data(word)
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return cls._get_fallback_word_data(word)
        except Exception as e:
            logger.error(f"Error fetching word data: {e}")
            return cls._get_fallback_word_data(word)

    @classmethod
    def _get_fallback_word_data(cls, word: str) -> Dict:
        """Provide fallback data when API fails."""
        return {
            'definition': f"Definition for {word} is temporarily unavailable.",
            'incorrect_options': [
                f"Alternative meaning 1 for {word}",
                f"Alternative meaning 2 for {word}",
                f"Alternative meaning 3 for {word}"
            ],
            'similar_words': [
                {
                    'word': f"similar1_{word}",
                    'definition': "Definition temporarily unavailable"
                },
                {
                    'word': f"similar2_{word}",
                    'definition': "Definition temporarily unavailable"
                },
                {
                    'word': f"similar3_{word}",
                    'definition': "Definition temporarily unavailable"
                }
            ]
        }

    @classmethod
    async def generate_math_problem(cls, category: str, topic: str, difficulty: str) -> Dict:
        """Generate a math problem with caching."""
        cache_key = f"math_{category}_{topic}_{difficulty}"
        cached_data = cls._cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for math problem: {cache_key}")
            return cached_data

        try:
            # Special handling for visual puzzles
            if topic == 'Visual puzzles':
                return await cls._generate_visual_puzzle(category, difficulty)

            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a math teacher creating problems."},
                    {"role": "user", "content": f"""Create a {difficulty} {category} problem about {topic}. Format the response as JSON with the following structure:
{{
    "id": "unique_string",
    "question": "detailed_problem_text",
    "correct_answer": numeric_or_string_answer,
    "category": "{category}",
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "explanation": "step_by_step_solution",
    "is_visual": false
}}
Make sure the correct_answer is a number when appropriate, and ensure all fields are present."""}
                ]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            try:
                problem_data = json.loads(content)
                # Validate the response format
                required_keys = ['id', 'question', 'correct_answer', 'category', 'topic', 'difficulty', 'explanation', 'is_visual']
                if not all(key in problem_data for key in required_keys):
                    logger.error(f"Invalid response format for math problem: missing required keys")
                    return cls._get_fallback_math_problem(category, topic, difficulty)
                
                # Try to convert correct_answer to float if it's numeric
                try:
                    if str(problem_data['correct_answer']).replace('.', '').isdigit():
                        problem_data['correct_answer'] = float(problem_data['correct_answer'])
                except ValueError:
                    pass  # Keep as string if conversion fails
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response for math problem")
                return cls._get_fallback_math_problem(category, topic, difficulty)
            
            # Update token usage
            cls._token_usage['prompt'] += response.usage.prompt_tokens
            cls._token_usage['completion'] += response.usage.completion_tokens
            cls._token_usage['total'] += response.usage.total_tokens
            
            # Cache the result
            cls._cache.set(cache_key, problem_data)
            return problem_data
            
        except Exception as e:
            logger.error(f"Error generating math problem: {e}")
            return cls._get_fallback_math_problem(category, topic, difficulty)

    @classmethod
    async def _generate_visual_puzzle(cls, category: str, difficulty: str) -> Dict:
        """Generate a visual puzzle problem."""
        try:
            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a math teacher creating visual puzzles."},
                    {"role": "user", "content": f"""Create a {difficulty} visual puzzle problem. Format the response as JSON with the following structure:
{{
    "id": "unique_string",
    "question": "detailed_problem_text",
    "figures": [
        {{
            "description": "Detailed description of figure 1 that can be used to generate an image",
            "caption": "Figure 1"
        }},
        {{
            "description": "Detailed description of figure 2 that can be used to generate an image",
            "caption": "Figure 2"
        }},
        {{
            "description": "Detailed description of figure 3 that can be used to generate an image",
            "caption": "Figure 3"
        }}
    ],
    "correct_answer": "description_of_next_figure",
    "category": "{category}",
    "topic": "Visual puzzles",
    "difficulty": "{difficulty}",
    "explanation": "step_by_step_solution",
    "is_visual": true,
    "pattern_explanation": "explanation of how the pattern evolves"
}}
Make sure to create a clear visual pattern that can be understood from the descriptions."""}
                ]
            )

            content = response.choices[0].message.content
            try:
                problem_data = json.loads(content)
                # Validate the response format
                required_keys = ['id', 'question', 'figures', 'correct_answer', 'category', 'topic', 'difficulty', 'explanation', 'is_visual', 'pattern_explanation']
                if not all(key in problem_data for key in required_keys):
                    logger.error("Invalid response format for visual puzzle")
                    return cls._get_fallback_visual_puzzle(category, difficulty)

                # Generate images for each figure using DALL-E
                figures_with_images = []
                for figure in problem_data['figures']:
                    try:
                        image_response = await async_client.images.generate(
                            model="dall-e-3",
                            prompt=f"Create a clear, simple diagram for a visual puzzle: {figure['description']}. The image should be clean, minimal, and suitable for a math puzzle.",
                            size="1024x1024",
                            quality="standard",
                            n=1,
                        )
                        figure['image_url'] = image_response.data[0].url
                        figures_with_images.append(figure)
                    except Exception as e:
                        logger.error(f"Error generating image for figure: {e}")
                        figure['image_url'] = None
                        figures_with_images.append(figure)

                problem_data['figures'] = figures_with_images
                return problem_data

            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response for visual puzzle")
                return cls._get_fallback_visual_puzzle(category, difficulty)

        except Exception as e:
            logger.error(f"Error generating visual puzzle: {e}")
            return cls._get_fallback_visual_puzzle(category, difficulty)

    @classmethod
    def _get_fallback_visual_puzzle(cls, category: str, difficulty: str) -> Dict:
        """Provide fallback visual puzzle when API fails."""
        return {
            'id': f"fallback_visual_{category}_{difficulty}",
            'question': "What comes next in this pattern?",
            'figures': [
                {
                    'description': "A simple square",
                    'caption': "Figure 1",
                    'image_url': None
                },
                {
                    'description': "A square with a circle inside",
                    'caption': "Figure 2",
                    'image_url': None
                },
                {
                    'description': "A square with a circle and triangle inside",
                    'caption': "Figure 3",
                    'image_url': None
                }
            ],
            'correct_answer': "A square with a circle, triangle, and star inside",
            'category': category,
            'topic': "Visual puzzles",
            'difficulty': difficulty,
            'explanation': "Each figure adds one shape inside the square",
            'is_visual': True,
            'pattern_explanation': "In each step, a new basic shape is added inside the square"
        }

    @classmethod
    def _get_fallback_math_problem(cls, category: str, topic: str, difficulty: str) -> Dict:
        """Provide fallback math problem when API fails."""
        return {
            'id': f"fallback_{category}_{topic}_{difficulty}",
            'question': f"What is 2 + 2? (Fallback {category} {topic} problem)",
            'correct_answer': 4,
            'category': category,
            'topic': topic,
            'difficulty': difficulty,
            'explanation': "This is a basic addition problem: 2 + 2 = 4"
        }

    @classmethod
    async def generate_problem_explanation(cls, question: str, answer: str) -> str:
        """Generate a step-by-step explanation for a math problem."""
        try:
            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a math teacher providing clear, step-by-step explanations."},
                    {"role": "user", "content": f"""Provide a clear, step-by-step explanation for this math problem:
Question: {question}
Answer: {answer}

Format your response as a clear, numbered list of steps."""}
                ]
            )
            
            # Get the explanation
            explanation = response.choices[0].message.content
            
            # Update token usage
            cls._token_usage['prompt'] += response.usage.prompt_tokens
            cls._token_usage['completion'] += response.usage.completion_tokens
            cls._token_usage['total'] += response.usage.total_tokens
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating problem explanation: {e}")
            return f"The answer is {answer}. (Detailed explanation unavailable at the moment.)"

class GoogleSheetsOptimizer:
    """Optimizes Google Sheets operations through batching."""
    _service = GoogleSheetsService(Config.GOOGLE_CREDENTIALS_JSON, Config.SPREADSHEET_ID)
    _updates_queue = []
    _batch_size = 10
    _flush_interval = 300
    _last_flush = time.time()

    @classmethod
    def queue_update(cls, word: str, definition: str):
        """Queue an update for batch processing."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cls._updates_queue.append({
            'word': word,
            'definition': definition,
            'timestamp': timestamp
        })
        
        if len(cls._updates_queue) >= cls._batch_size or \
           time.time() - cls._last_flush > cls._flush_interval:
            cls.flush_updates()

    @classmethod
    def flush_updates(cls):
        """Process all queued updates."""
        if not cls._updates_queue:
            return

        try:
            # Process updates in batch
            cls._service.batch_update_words(cls._updates_queue)
            cls._updates_queue = []
            cls._last_flush = time.time()
        except Exception as e:
            logger.error(f"Error flushing updates to Google Sheets: {e}")

class MathSheetsOptimizer:
    """Optimizes math problem updates to Google Sheets."""
    _service = GoogleSheetsService(Config.GOOGLE_CREDENTIALS_JSON, Config.SPREADSHEET_ID)
    _updates_queue = []
    _stats_queue = []
    _batch_size = 10
    _flush_interval = 300
    _last_flush = time.time()

    @classmethod
    def queue_update(cls, problem_data: Dict):
        """Queue a math problem update for batch processing."""
        cls._updates_queue.append(problem_data)
        
        if len(cls._updates_queue) >= cls._batch_size or \
           time.time() - cls._last_flush > cls._flush_interval:
            cls.flush_updates()

    @classmethod
    def queue_stats_update(cls, stats_data: Dict):
        """Queue a math statistics update for batch processing."""
        cls._stats_queue.append(stats_data)
        
        # Force flush after each stats update to ensure timely updates
        cls.flush_updates()

    @classmethod
    def flush_updates(cls):
        """Process all queued updates."""
        if not cls._updates_queue and not cls._stats_queue:
            return

        try:
            # Process queued problem updates in batch
            if cls._updates_queue:
                for problem in cls._updates_queue:
                    cls._service.save_math_problem(problem)
                cls._updates_queue = []

            # Process queued stats updates in batch
            if cls._stats_queue:
                cls._service.batch_update_math_stats(cls._stats_queue)
                cls._stats_queue = []

            cls._last_flush = time.time()
        except Exception as e:
            logger.error(f"Error flushing updates to Google Sheets: {e}")

    @classmethod
    def get_math_stats(cls, user: str, start_date: datetime, end_date: datetime) -> Dict:
        """Get math statistics for a user within a date range."""
        try:
            return cls._service.get_math_stats(user, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting math stats from Google Sheets: {e}")
            return {
                'by_category': {},
                'by_difficulty': {},
                'daily_correct': [],
                'daily_incorrect': []
            } 