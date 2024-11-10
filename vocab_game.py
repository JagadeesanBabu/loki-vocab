import random
import json
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Initialize the server-side session extension
Session(app)

# Load vocabulary words from JSON file
with open('vocabulary_words.json', 'r') as file:
    VOCABULARY_WORDS = json.load(file)

# Create a list of word indices for easy reference
WORD_INDICES = list(range(len(VOCABULARY_WORDS)))

@app.route('/reset', methods=['GET'])
def reset_score():
    session.clear()
    return redirect(url_for('vocab_game'))

@app.route('/', methods=['GET', 'POST'])
def vocab_game():
    if 'score' not in session:
        session['score'] = {'correct': 0, 'incorrect': 0}

    if request.method == 'POST':
        # Retrieve indices from the session
        word_index = session.get('word_index')
        option_indices = session.get('option_indices')
        if word_index is None or option_indices is None:
            # Redirect to initialize if data is missing
            return redirect(url_for('vocab_game'))

        word_pair = VOCABULARY_WORDS[word_index]
        question_word = word_pair['word']
        correct_answer = word_pair['definition']

        # Retrieve options based on indices
        options = [VOCABULARY_WORDS[i]['definition'] for i in option_indices]

        # Get the user's answer
        user_answer = request.form['answer'].strip()

        # Debug information
        print(f"User Answer: {user_answer}")
        print(f"Correct Answer: {correct_answer}")
        print(f"Question: {question_word}")

        # Compare the user's answer with the correct answer
        if user_answer == correct_answer:
            result = f"Correct! The meaning of '{question_word}' is '{correct_answer}'."
            answer_status = "correct"
            session['score']['correct'] += 1
        else:
            result = f"Incorrect. The correct meaning of '{question_word}' is '{correct_answer}'."
            answer_status = "incorrect"
            session['score']['incorrect'] += 1

        # Do not update session variables here
        # Render the response for the current answer
        return render_template(
            'vocab_game.html',
            word=question_word,
            options=options,
            result=result,
            answer_status=answer_status,
            score=session['score'],
            show_next_question=True
        )

    else:
        # GET request: Initialize new question
        word_index = random.choice(WORD_INDICES)
        word_pair = VOCABULARY_WORDS[word_index]
        correct_answer = word_pair['definition']
        question_word = word_pair['word']

        # Generate options
        num_incorrect = min(3, len(VOCABULARY_WORDS) - 1)
        incorrect_indices = random.sample(
            [i for i in WORD_INDICES if i != word_index],
            num_incorrect
        )
        option_indices = incorrect_indices + [word_index]
        random.shuffle(option_indices)
        options = [VOCABULARY_WORDS[i]['definition'] for i in option_indices]

        # Store indices in session
        session['word_index'] = word_index
        session['option_indices'] = option_indices

        return render_template(
            'vocab_game.html',
            word=question_word,
            options=options,
            result="",
            answer_status="",
            score=session['score'],
            show_next_question=False
        )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
