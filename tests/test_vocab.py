import unittest
from unittest.mock import patch, MagicMock
from flask import session
from services.vocab_service import reset_score, get_next_question, check_answer, get_summary

class TestVocabService(unittest.TestCase):

    @patch('services.vocab_service.clear_session_files')
    def test_reset_score(self, mock_clear_session_files):
        with patch('flask.session', {'score': {'correct': 5, 'incorrect': 3}}):
            reset_score()
            self.assertEqual(session['score'], {'correct': 0, 'incorrect': 0})
            mock_clear_session_files.assert_called_once()

    @patch('services.vocab_service.random.choice')
    @patch('services.vocab_service.fetch_definition')
    @patch('services.vocab_service.fetch_incorrect_options')
    @patch('services.vocab_service.WordData.word_exists')
    @patch('services.vocab_service.WordData.add_word_data')
    @patch('services.vocab_service.WordData.get_correct_answer')
    @patch('services.vocab_service.WordData.get_incorrect_options')
    def test_get_next_question(self, mock_get_incorrect_options, mock_get_correct_answer, mock_add_word_data, mock_word_exists, mock_fetch_incorrect_options, mock_fetch_definition, mock_random_choice):
        mock_random_choice.return_value = 'test_word'
        mock_fetch_definition.return_value = 'test_definition'
        mock_fetch_incorrect_options.return_value = ['incorrect1', 'incorrect2', 'incorrect3']
        mock_word_exists.return_value = False

        question_data = get_next_question(['test_word'])

        self.assertEqual(question_data['word'], 'test_word')
        self.assertEqual(question_data['correct_answer'], 'test_definition')
        self.assertIn('test_definition', question_data['options'])
        self.assertEqual(len(question_data['options']), 4)

    def test_check_answer_correct(self):
        with patch('flask.session', {'score': {'correct': 0, 'incorrect': 0}}):
            result_data = check_answer('correct_answer', 'test_word', 'correct_answer')
            self.assertEqual(result_data['answer_status'], 'correct')
            self.assertEqual(session['score']['correct'], 1)

    def test_check_answer_incorrect(self):
        with patch('flask.session', {'score': {'correct': 0, 'incorrect': 0}}):
            result_data = check_answer('wrong_answer', 'test_word', 'correct_answer')
            self.assertEqual(result_data['answer_status'], 'incorrect')
            self.assertEqual(session['score']['incorrect'], 1)

    def test_get_summary(self):
        with patch('flask.session', {'score': {'correct': 5, 'incorrect': 3}, 'incorrect_answers': [{'word': 'test_word', 'user_answer': 'wrong_answer', 'correct_answer': 'correct_answer'}]}):
            summary = get_summary()
            self.assertEqual(summary['correct_answers'], 5)
            self.assertEqual(summary['incorrect_answers'], 3)
            self.assertEqual(summary['total_answers'], 8)
            self.assertEqual(len(summary['incorrect_answer_details']), 1)

if __name__ == '__main__':
    unittest.main()
