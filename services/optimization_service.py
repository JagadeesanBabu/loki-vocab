import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from collections import defaultdict
import logging
from openai.error import RateLimitError, OpenAIError
import openai
from config import Config

logger = logging.getLogger(__name__)

class PersistentCache:
    CACHE_FILE = 'word_cache.json'
    CACHE_DURATION = timedelta(days=30)

    _cache: Dict = {}
    _last_save = datetime.now()
    SAVE_INTERVAL = timedelta(minutes=5)

    @classmethod
    def initialize(cls):
        """Initialize cache from file if it exists"""
        if os.path.exists(cls.CACHE_FILE):
            try:
                with open(cls.CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    now = datetime.now()
                    # Filter out expired entries
                    cls._cache = {
                        word: data for word, data in cache_data.items()
                        if datetime.fromisoformat(data['timestamp']) + cls.CACHE_DURATION > now
                    }
                logger.info(f"Loaded {len(cls._cache)} words from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                cls._cache = {}

    @classmethod
    def get(cls, word: str) -> Optional[dict]:
        """Get word data from cache if it exists and is not expired"""
        if word in cls._cache:
            data = cls._cache[word]
            cache_time = datetime.fromisoformat(data['timestamp'])
            if cache_time + cls.CACHE_DURATION > datetime.now():
                return data
            else:
                del cls._cache[word]
        return None

    @classmethod
    def set(cls, word: str, data: dict):
        """Set word data in cache with timestamp"""
        cls._cache[word] = {
            **data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to file periodically
        if datetime.now() - cls._last_save > cls.SAVE_INTERVAL:
            cls.save_to_file()

    @classmethod
    def save_to_file(cls):
        """Save cache to file"""
        try:
            with open(cls.CACHE_FILE, 'w') as f:
                json.dump(cls._cache, f)
            cls._last_save = datetime.now()
            logger.info(f"Saved {len(cls._cache)} words to cache file")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

class OpenAIOptimizer:
    _batch_queue = []
    BATCH_SIZE = 10
    _token_usage = defaultdict(int)
    _last_reset = datetime.now()
    DAILY_TOKEN_LIMIT = 100000  # Adjust based on your budget

    @classmethod
    async def fetch_word_data(cls, word: str) -> dict:
        """Fetch word data either from cache or API"""
        word = word.strip().lower()
        
        # Check cache first
        cached_data = PersistentCache.get(word)
        if cached_data:
            logger.info(f"Cache hit for word: {word}")
            return cached_data

        # Add to batch queue
        cls._batch_queue.append(word)
        
        # Process batch if queue is full
        if len(cls._batch_queue) >= cls.BATCH_SIZE:
            return await cls.process_batch()
        
        # If not in batch, process single word
        return await cls._fetch_single_word(word)

    @classmethod
    async def process_batch(cls) -> dict:
        """Process a batch of words in a single API call"""
        if not cls._batch_queue:
            return {}

        words = cls._batch_queue.copy()
        cls._batch_queue.clear()

        prompt = f"""
        Provide data for these words: {', '.join(words)}
        Return in this exact JSON format for each word:
        {{
            "word": "word",
            "definition": "brief definition",
            "incorrect_options": ["three plausible but incorrect definitions"],
            "similar_words": [
                {{"word": "similar1", "definition": "brief definition"}},
                {{"word": "similar2", "definition": "brief definition"}}
            ]
        }}
        Keep all definitions under 30 words.
        """

        try:
            response = await cls._make_api_call_with_retry(prompt)
            
            # Parse and cache results
            results = {}
            for word_data in response.get('words', []):
                PersistentCache.set(word_data['word'], word_data)
                results[word_data['word']] = word_data
            
            return results
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return await cls._fetch_single_word(words[0])

    @classmethod
    async def _fetch_single_word(cls, word: str) -> dict:
        """Fetch data for a single word"""
        prompt = f"""
        Provide data for the word '{word}' in this exact JSON format:
        {{
            "word": "{word}",
            "definition": "brief definition",
            "incorrect_options": ["three plausible but incorrect definitions"],
            "similar_words": [
                {{"word": "similar1", "definition": "brief definition"}},
                {{"word": "similar2", "definition": "brief definition"}}
            ]
        }}
        Keep all definitions under 30 words.
        """

        try:
            response = await cls._make_api_call_with_retry(prompt)
            word_data = response.get('word_data', {})
            PersistentCache.set(word, word_data)
            return word_data
        except Exception as e:
            logger.error(f"Error fetching single word data: {e}")
            return cls._get_fallback_response(word)

    @classmethod
    async def _make_api_call_with_retry(cls, prompt: str, max_retries: int = 3) -> dict:
        """Make API call with retry logic"""
        if not cls._check_token_limit():
            raise Exception("Daily token limit reached")

        for attempt in range(max_retries):
            try:
                response = await openai.ChatCompletion.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                
                # Track token usage
                cls._track_tokens(response.usage.total_tokens)
                
                return response['choices'][0]['message']['content']
            except RateLimitError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
            except Exception as e:
                logger.error(f"API call error: {e}")
                raise

    @classmethod
    def _check_token_limit(cls) -> bool:
        """Check if we're within token limits"""
        # Reset daily usage if it's a new day
        if datetime.now().date() > cls._last_reset.date():
            cls._token_usage.clear()
            cls._last_reset = datetime.now()
        
        return sum(cls._token_usage.values()) < cls.DAILY_TOKEN_LIMIT

    @classmethod
    def _track_tokens(cls, tokens: int):
        """Track token usage"""
        current_date = datetime.now().date().isoformat()
        cls._token_usage[current_date] += tokens
        
        # Log warning if approaching limit
        daily_usage = cls._token_usage[current_date]
        if daily_usage > cls.DAILY_TOKEN_LIMIT * 0.8:  # 80% of limit
            logger.warning(f"Token usage high: {daily_usage}/{cls.DAILY_TOKEN_LIMIT}")

    @staticmethod
    def _get_fallback_response(word: str) -> dict:
        """Provide fallback response when API fails"""
        return {
            "word": word,
            "definition": "Definition temporarily unavailable",
            "incorrect_options": [
                "Option temporarily unavailable",
                "Option temporarily unavailable",
                "Option temporarily unavailable"
            ],
            "similar_words": []
        }

    @classmethod
    async def generate_math_problem(cls, category: str, topic: str, difficulty: str) -> dict:
        """Generate a math problem with optimized API usage"""
        cache_key = f"math_{category}_{topic}_{difficulty}"
        
        # Check cache first
        cached_data = PersistentCache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for math problem: {cache_key}")
            return cached_data

        prompt = f"""
        Create a {difficulty} level math problem for a grammar school exam (GL level) on the topic of {topic} 
        within the category of {category}. Return in this exact JSON format:
        {{
            "question": "The full word problem",
            "correct_answer": "The answer as a number or string",
            "category": "{category}",
            "topic": "{topic}",
            "difficulty": "{difficulty}",
            "explanation": "Step-by-step solution explanation"
        }}
        Keep the problem suitable for a 10-12 year old child.
        """

        try:
            response = await cls._make_api_call_with_retry(prompt)
            problem_data = json.loads(response)
            
            # Cache the result
            PersistentCache.set(cache_key, problem_data)
            
            return problem_data
        except Exception as e:
            logger.error(f"Error generating math problem: {e}")
            return cls._get_fallback_math_problem(category, topic, difficulty)

    @classmethod
    async def generate_problem_explanation(cls, question: str, answer: str) -> str:
        """Generate explanation for a math problem with optimized API usage"""
        cache_key = f"explanation_{hash(question + str(answer))}"
        
        # Check cache first
        cached_data = PersistentCache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for problem explanation")
            return cached_data.get('explanation', '')

        prompt = f"""
        Provide a clear, step-by-step explanation for solving this math problem:
        Problem: {question}
        Answer: {answer}
        
        Your explanation should be suitable for a 10-12 year old child preparing for grammar school (GL level) exams.
        Break down the problem-solving process into logical steps.
        Keep the explanation under 200 words.
        """

        try:
            response = await cls._make_api_call_with_retry(prompt)
            explanation_data = {'explanation': response}
            
            # Cache the result
            PersistentCache.set(cache_key, explanation_data)
            
            return response
        except Exception as e:
            logger.error(f"Error generating problem explanation: {e}")
            return "Explanation temporarily unavailable."

    @staticmethod
    def _get_fallback_math_problem(category: str, topic: str, difficulty: str) -> dict:
        """Provide fallback response when API fails for math problems"""
        return {
            "question": "Problem temporarily unavailable",
            "correct_answer": "0",
            "category": category,
            "topic": topic,
            "difficulty": difficulty,
            "explanation": "Explanation temporarily unavailable"
        }

class GoogleSheetsOptimizer:
    _batch_updates = []
    _last_sync = None
    BATCH_SIZE = 50
    SYNC_INTERVAL = timedelta(minutes=5)

    @classmethod
    def queue_update(cls, word: str, definition: str):
        """Queue a word update for batch processing"""
        cls._batch_updates.append({
            'word': word.strip(),
            'definition': definition.strip(),
            'timestamp': datetime.now().isoformat()
        })
        
        if len(cls._batch_updates) >= cls.BATCH_SIZE:
            cls.flush_updates()
        elif cls._last_sync and datetime.now() - cls._last_sync > cls.SYNC_INTERVAL:
            cls.flush_updates()

    @classmethod
    def flush_updates(cls):
        """Flush queued updates to Google Sheets"""
        if not cls._batch_updates:
            return

        try:
            updates = cls._batch_updates.copy()
            cls._batch_updates.clear()
            
            # Implement bulk update logic here
            from services.google_sheet_service import GoogleSheetsService
            service = GoogleSheetsService(
                Config.GOOGLE_CREDENTIALS_JSON,
                Config.SPREADSHEET_ID
            )
            
            # Batch update all words
            service.batch_update_words(updates)
            
            cls._last_sync = datetime.now()
            logger.info(f"Batch updated {len(updates)} words to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to update Google Sheets: {e}")
            # Re-queue failed updates
            cls._batch_updates.extend(updates)

class MathSheetsOptimizer:
    _batch_updates = []
    _last_sync = None
    BATCH_SIZE = 20
    SYNC_INTERVAL = timedelta(minutes=5)

    @classmethod
    def queue_update(cls, problem: dict):
        """Queue a math problem update for batch processing"""
        cls._batch_updates.append({
            **problem,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(cls._batch_updates) >= cls.BATCH_SIZE:
            cls.flush_updates()
        elif cls._last_sync and datetime.now() - cls._last_sync > cls.SYNC_INTERVAL:
            cls.flush_updates()

    @classmethod
    def flush_updates(cls):
        """Flush queued updates to Google Sheets"""
        if not cls._batch_updates:
            return

        try:
            updates = cls._batch_updates.copy()
            cls._batch_updates.clear()
            
            # Implement bulk update logic here
            from services.google_sheet_service import GoogleSheetsService
            service = GoogleSheetsService(
                Config.GOOGLE_CREDENTIALS_JSON,
                Config.SPREADSHEET_ID
            )
            
            # Batch update all problems
            for problem in updates:
                service.save_math_problem(problem)
            
            cls._last_sync = datetime.now()
            logger.info(f"Batch updated {len(updates)} math problems to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to update math problems to Google Sheets: {e}")
            # Re-queue failed updates
            cls._batch_updates.extend(updates)

# Initialize cache when module is loaded
PersistentCache.initialize() 