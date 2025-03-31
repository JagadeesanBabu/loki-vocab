import unittest
from unittest.mock import patch, MagicMock
from services.openai_service import fetch_definition, fetch_incorrect_options

class TestOpenAIService(unittest.TestCase):

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_definition(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content.strip.return_value = "A brief definition of the word."
        mock_create.return_value = mock_response

        definition = fetch_definition("test_word")
        self.assertEqual(definition, "A brief definition of the word.")
        mock_create.assert_called_once()

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_definition_rate_limit_error(self, mock_create):
        mock_create.side_effect = openai.error.RateLimitError("Rate limit exceeded")

        definition = fetch_definition("test_word")
        self.assertEqual(definition, "Definition not available due to API rate limit.")
        mock_create.assert_called_once()

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_definition_openai_error(self, mock_create):
        mock_create.side_effect = openai.error.OpenAIError("API error")

        definition = fetch_definition("test_word")
        self.assertEqual(definition, "Definition not available due to API error.")
        mock_create.assert_called_once()

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_incorrect_options(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content.strip.return_value = "Incorrect definition 1\nIncorrect definition 2\nIncorrect definition 3"
        mock_create.return_value = mock_response

        incorrect_options = fetch_incorrect_options("test_word", "correct_definition")
        self.assertEqual(incorrect_options, ["Incorrect definition 1", "Incorrect definition 2", "Incorrect definition 3"])
        mock_create.assert_called_once()

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_incorrect_options_rate_limit_error(self, mock_create):
        mock_create.side_effect = openai.error.RateLimitError("Rate limit exceeded")

        incorrect_options = fetch_incorrect_options("test_word", "correct_definition")
        self.assertEqual(incorrect_options, ["Incorrect option not available due to API rate limit."] * 3)
        mock_create.assert_called_once()

    @patch('services.openai_service.openai.ChatCompletion.create')
    def test_fetch_incorrect_options_openai_error(self, mock_create):
        mock_create.side_effect = openai.error.OpenAIError("API error")

        incorrect_options = fetch_incorrect_options("test_word", "correct_definition")
        self.assertEqual(incorrect_options, ["Incorrect option not available due to API error."] * 3)
        mock_create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
