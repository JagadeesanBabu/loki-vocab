# loki-vocab
This is to improve loki vocabulary

## Project Setup and Installation

To set up this project locally, follow these steps:

1. **Clone the repository:**
   ```sh
   git clone https://github.com/JagadeesanBabu/loki-vocab.git
   cd loki-vocab
   ```

2. **Create a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `local.env` file in the root directory of the project and add the necessary environment variables. Refer to `config.py` for the required variables.

5. **Initialize the database:**
   ```sh
   flask db upgrade
   ```

6. **Run the application:**
   ```sh
   flask run
   ```

## Functions and Features

This project is a vocabulary game designed to help users improve their vocabulary. The main features include:

- **User Authentication:** Users can log in and log out of the application.
- **Vocabulary Game:** Users can play a game where they are presented with words and must choose the correct definition from multiple options.
- **Progress Dashboard:** Users can view their progress, including the number of correct and incorrect answers.
- **Summary:** Users can view a summary of their performance, including details of incorrect answers.

## Running the Project Locally

To run the project locally, follow the steps in the "Project Setup and Installation" section. Once the application is running, you can access it in your web browser at `http://localhost:5000`.

## Using the Vocabulary Game

1. **Log in:** Use the login page to log in to the application.
2. **Start the game:** Once logged in, you will be presented with a word and multiple definitions. Choose the correct definition and submit your answer.
3. **View results:** After submitting your answer, you will see whether you were correct or incorrect. You can then proceed to the next question.
4. **View progress:** Use the dashboard to view your progress, including the number of correct and incorrect answers.
5. **View summary:** Use the summary page to view a detailed summary of your performance, including details of incorrect answers.
