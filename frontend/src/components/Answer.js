import React, { useState } from 'react';
import axios from 'axios';

const Answer = () => {
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState(null);

  const handleChange = (event) => {
    setAnswer(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/answer', { answer });
      setResult(response.data);
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  return (
    <div>
      <h1>Answer Quiz</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Your Answer:
          <input type="text" value={answer} onChange={handleChange} />
        </label>
        <button type="submit">Submit</button>
      </form>
      {result && (
        <div>
          <p>{result.result_message}</p>
          <p>Correct Answer: {result.correct_answer}</p>
        </div>
      )}
    </div>
  );
};

export default Answer;
