import random
import json
from flask import Flask, render_template, request, session, redirect, url_for

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load vocabulary words from JSON file
with open('vocabulary_words.json', 'r') as file:
    VOCABULARY_WORDS = json.load(file)

# Route for the game page
@app.route('/', methods=['GET', 'POST'])
def vocab_game():
    if 'word_pair' not in session:
        session['word_pair'] = random.choice(VOCABULARY_WORDS)
    word_pair = session['word_pair']
    question_word = word_pair['word']
    result = ""
    answer_status = ""

    # Generate multiple choice options
    correct_answer = word_pair['definition']
    incorrect_answers = random.sample([word['definition'] for word in VOCABULARY_WORDS if word != word_pair], 3)
    options = incorrect_answers + [correct_answer]
    random.shuffle(options)

    if request.method == 'POST':
        user_answer = request.form['answer'].strip().lower()
        correct_answer = word_pair['definition'].strip().lower()

        if user_answer == correct_answer:
            result = f"The word '{question_word}' is correct! Great job!"
            answer_status = "correct"
        else:
            result = f"Incorrect. The correct answer is: '{word_pair['definition']}'"
            answer_status = "incorrect"

        # Load a new word for the next question
        session.pop('word_pair', None)

    return render_template('vocab_game.html', word=question_word, options=options, result=result, answer_status=answer_status)

# Route to get a new word
@app.route('/new', methods=['GET'])
def new_word():
    session.pop('word_pair', None)
    return redirect(url_for('vocab_game'))

# Run the Flask web server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
