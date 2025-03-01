import openai
from config import Config
from openai.error import RateLimitError, OpenAIError
import logging

openai.api_key = Config.OPENAI_API_KEY
model = "gpt-4o-mini-2024-07-18"

def fetch_definition(word):
    logging.info(f"Fetching definition for '{word}' from OpenAI API.")
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": f"Define the word '{word}'."}
            ],
            temperature=0.5,
            max_tokens=100,
            n=1,
            stop=None,
        )
        definition = response['choices'][0]['message']['content'].strip()
        return definition
    except RateLimitError as e:
        logging.error(f"Rate limit exceeded: {e}")
        return "Definition not available due to API rate limit."
    except OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return "Definition not available due to API error."
    except Exception as e:
        logging.error(f"Error fetching meaning: {e}")
        return "Definition not available."

def fetch_incorrect_options(word, correct_definition, num_options=3):
    try:
        # prompt = f"Provide {num_options} plausible but incorrect definitions for the word '{word}' that are different from its actual meaning, without any introductions or extra explanations. Only list each incorrect definition on a new line."
        prompt = (
        f"Provide {num_options} brief, plausible, and incorrect definitions for the word '{word}' that closely resemble "
        f"the style and structure of this correct definition: '{correct_definition}', but with a different meaning."
        f" Each incorrect definition should sound believable but describe the word inaccurately."
        )
        response = openai.ChatCompletion.create(
            model= model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60 * num_options,
            n=1,
            stop=None,
        )
        incorrect_definitions = response['choices'][0]['message']['content'].strip().split("\n")
        # Clean up the definitions
        incorrect_definitions = [defn.strip('-•1234567890. ').strip() for defn in incorrect_definitions if defn.strip()]
        return incorrect_definitions[:num_options]
    except RateLimitError as e:
        logging.error(f"Rate limit exceeded: {e}")
        return ["Incorrect option not available due to API rate limit."] * num_options
    except OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return ["Incorrect option not available due to API error."] * num_options
    except Exception as e:
        logging.error(f"Error fetching incorrect options: {e}")
        return ["Incorrect option not available."] * num_options

def fetch_similar_words(word, num_words=4):
    logging.info(f"Fetching similar words for '{word}' from OpenAI API.")
    try:
        prompt = (
            f"For the word '{word}', provide {num_words} similar or related words with their brief definitions. "
            f"Format the response exactly like this example (without numbering, just word: definition pairs):\n\n"
            f"articulate: Able to express oneself clearly and effectively.\n"
            f"eloquent: Fluent and persuasive in speaking or writing.\n"
            f"coherent: Logical and consistent in thought or speech.\n"
            f"expressive: Effectively conveying thought or feeling."
        )
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
            n=1,
            stop=None,
        )
        content = response['choices'][0]['message']['content'].strip()
        
        # Parse the response into word-definition pairs
        similar_words = []
        for line in content.split('\n'):
            if line and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    word = parts[0].strip()
                    definition = parts[1].strip()
                    similar_words.append({"word": word, "definition": definition})
        
        return similar_words[:num_words]  # Ensure we return at most num_words
    except RateLimitError as e:
        logging.error(f"Rate limit exceeded: {e}")
        return [{"word": "Not available", "definition": "Similar words not available due to API rate limit."}]
    except OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return [{"word": "Not available", "definition": "Similar words not available due to API error."}]
    except Exception as e:
        logging.error(f"Error fetching similar words: {e}")
        return [{"word": "Not available", "definition": "Similar words not available."}]
