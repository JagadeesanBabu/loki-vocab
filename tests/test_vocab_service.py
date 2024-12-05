import unittest
from unittest.mock import patch, MagicMock
from flask import session
from services.vocab_service import reset_score, get_next_question, check_answer, get_summary
from database.models import WordData, WordCount

class TestVocabService(unittest.TestCase):

    def setUp(self):
        self.patcher1 = patch('services.vocab_service.clear_session_files')
        self.mock_clear_session_files = self.patcher1.start()
        self.addCleanup(self.patcher1.stop)

        self.patcher2 = patch('services.vocab_service.session', {'score': {'correct': 0, 'incorrect': 0}})
        self.mock_session = self.patcher2.start()
        self.addCleanup(self.patcher2.stop)

    def test_reset_score(self):
        reset_score()
        self.assertEqual(session['score'], {'correct': 0, 'incorrect': 0})
        self.mock_clear_session_files.assert_called_once()

    @patch('services.vocab_service.fetch_definition')
    @patch('services.vocab_service.fetch_incorrect_options')
    @patch('services.vocab_service.WordData.word_exists')
    @patch('services.vocab_service.WordData.add_word_data')
    @patch('services.vocab_service.WordData.get_correct_answer')
    @patch('services.vocab_service.WordData.get_incorrect_options')
    def test_get_next_question(self, mock_get_incorrect_options, mock_get_correct_answer, mock_add_word_data, mock_word_exists, mock_fetch_incorrect_options, mock_fetch_definition):
        unlearned_words = ['test_word']
        mock_word_exists.return_value = False
        mock_fetch_definition.return_value = 'test_definition'
        mock_fetch_incorrect_options.return_value = ['incorrect1', 'incorrect2', 'incorrect3']

        question_data = get_next_question(unlearned_words)

        self.assertEqual(question_data['word'], 'test_word')
        self.assertEqual(question_data['correct_answer'], 'test_definition')
        self.assertIn('test_definition', question_data['options'])
        self.assertEqual(len(question_data['options']), 4)

    @patch('services.vocab_service.WordCount.increment_word_count')
    @patch('services.vocab_service.WordCount.increment_incorrect_count')
    def test_check_answer_correct(self, mock_increment_incorrect_count, mock_increment_word_count):
        session['score'] = {'correct': 0, 'incorrect': 0}
        result_data = check_answer('correct_answer', 'test_word', 'correct_answer')

        self.assertEqual(result_data['answer_status'], 'correct')
        self.assertEqual(session['score']['correct'], 1)
        mock_increment_word_count.assert_called_once_with('test_word')
        mock_increment_incorrect_count.assert_not_called()

    @patch('services.vocab_service.WordCount.increment_word_count')
    @patch('services.vocab_service.WordCount.increment_incorrect_count')
    def test_check_answer_incorrect(self, mock_increment_incorrect_count, mock_increment_word_count):
        session['score'] = {'correct': 0, 'incorrect': 0}
        result_data = check_answer('wrong_answer', 'test_word', 'correct_answer')

        self.assertEqual(result_data['answer_status'], 'incorrect')
        self.assertEqual(session['score']['incorrect'], 1)
        mock_increment_incorrect_count.assert_called_once_with('test_word')
        mock_increment_word_count.assert_not_called()

    def test_get_summary(self):
        session['score'] = {'correct': 5, 'incorrect': 3}
        session['incorrect_answers'] = [
            {'word': 'word1', 'user_answer': 'answer1', 'correct_answer': 'correct1'},
            {'word': 'word2', 'user_answer': 'answer2', 'correct_answer': 'correct2'}
        ]

        summary_data = get_summary()

        self.assertEqual(summary_data['correct_answers'], 5)
        self.assertEqual(summary_data['incorrect_answers'], 3)
        self.assertEqual(summary_data['total_answers'], 8)
        self.assertEqual(len(summary_data['incorrect_answer_details']), 2)

if __name__ == '__main__':
    unittest.main()
