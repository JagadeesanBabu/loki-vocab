import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Summary = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await axios.get('/api/summary');
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  return (
    <div>
      <h1>Summary</h1>
      {summary ? (
        <div>
          <p>Total Answers: {summary.total_answers}</p>
          <p>Correct Answers: {summary.correct_answers}</p>
          <p>Incorrect Answers: {summary.incorrect_answers}</p>
          <h2>Incorrect Answer Details</h2>
          <ul>
            {summary.incorrect_answer_details.map((detail, index) => (
              <li key={index}>
                <p>Word: {detail.word}</p>
                <p>Your Answer: {detail.user_answer}</p>
                <p>Correct Answer: {detail.correct_answer}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>Loading summary...</p>
      )}
    </div>
  );
};

export default Summary;
