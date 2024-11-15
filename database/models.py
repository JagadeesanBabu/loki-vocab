
from .db import db
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        # Implement your logic to get a user by ID
        # For example, query the database to get the user
        # Here is a simple example with a hardcoded user
        if user_id == "1":
            return User(id="1", username="loke", password="latha")
        return None

class WordCount(db.Model):
    __tablename__ = 'word_counts'
    word = db.Column(db.String(150), primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def increment_word_count(cls, word):
        word_count = cls.query.filter_by(word=word).first()
        if word_count:
            word_count.count += 1
        else:
            word_count = cls(word=word, count=1)
            db.session.add(word_count)
        db.session.commit()
        
    @classmethod
    def get_learnt_words(cls):
        return [word.word for word in cls.query.filter(cls.count > 0).all()]


import json
from sqlalchemy.dialects.postgresql import JSON

class WordData(db.Model):
    __tablename__ = 'word_data'
    word = db.Column(db.String(150), primary_key=True)
    definition = db.Column(db.Text, nullable=False)
    incorrect_options = db.Column(JSON, nullable=False)

    def add_word_data(self):
        exisiting_word = self.query.filter_by(word=self.word).first()
        if exisiting_word:
            return False
        db.session.add(self)
        db.session.commit()
        
    @classmethod
    def word_exists(cls, word):
        return cls.query.filter_by(word=word.strip()).first() is not None

    @classmethod
    def get_correct_answer(cls, word):
        word_data = cls.query.filter_by(word=word.strip()).first()
        return word_data.definition if word_data else None

    @classmethod
    def get_incorrect_options(cls, word):
        word_data = cls.query.filter_by(word=word.strip()).first()
        return word_data.incorrect_options if word_data else None
    
    @classmethod
    def get_unlearned_words(cls, all_words, max_count=10):
        unlearned_words = []
        for word in all_words:
            word_count = word_count = WordCount.query.filter_by(word=word.strip()).first()
            count = word_count.count if word_count else 0
            if count < max_count:
                unlearned_words.append(word)
        return unlearned_words

