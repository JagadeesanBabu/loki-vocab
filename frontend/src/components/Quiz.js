import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Quiz = () => {
  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchQuestion();
  }, []);

  const fetchQuestion = async () => {
    try {
      const response = await axios.get('/api/quiz');
      setQuestion(response.data);
    } catch (error) {
      console.error('Error fetching question:', error);
    }
  };

  const handleAnswerChange = (event) => {
    setSelectedAnswer(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/answer', {
        answer: selectedAnswer,
        word: question.word,
        correct_answer: question.correct_answer,
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  return (
    <div>
      <h1>Quiz</h1>
      {question && (
        <div>
          <p>What is the meaning of the word "{question.word}"?</p>
          <form onSubmit={handleSubmit}>
            {question.options.map((option, index) => (
              <div key={index}>
                <label>
                  <input
                    type="radio"
                    value={option}
                    checked={selectedAnswer === option}
                    onChange={handleAnswerChange}
                  />
                  {option}
                </label>
              </div>
            ))}
            <button type="submit">Submit</button>
          </form>
        </div>
      )}
      {result && (
        <div>
          <p>{result.result_message}</p>
          <p>Correct Answer: {result.correct_answer}</p>
        </div>
      )}
    </div>
  );
};

export default Quiz;
