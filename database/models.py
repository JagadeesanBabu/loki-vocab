
from sqlalchemy import func
from .db import db
from flask_login import UserMixin, current_user
from datetime import datetime, timedelta

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
        elif user_id == "2":
            return User(id="2", username="adarsh", password="sridhar")
        return None

class WordCount(db.Model):
    __tablename__ = 'word_counts'
    word = db.Column(db.String(150), primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=0)
    incorrect_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    updated_by = db.Column(db.String(150), nullable=True)

    @classmethod
    def get_todays_user_word_count(cls):
        day_ago = datetime.now() - timedelta(days=1)
        print(f"Current user is: {current_user.username} and today's date is: {func.current_date()}")
        return cls.query.filter(cls.updated_at >= day_ago, cls.updated_by == current_user.username ).count()
    
    @classmethod
    def increment_word_count(cls, word):
        # Check this word exist for the logged in user in the table by querying column word and updated_by

        word_count_row = cls.query.filter_by(word=word).filter_by(updated_by=current_user.username).first()
        if word_count_row:
            word_count_row.count += 1
            word_count_row.updated_at = db.func.now()
        else:
            word_count_row = cls(word=word, count=1, updated_by=current_user.username, updated_at=db.func.now())
            db.session.add(word_count_row)
        db.session.commit()
        
    @classmethod
    def increment_incorrect_count(cls, word):
        print(f'Current user is: {current_user.username} word is: {word}' )
        word_incorrect_count = cls.query.filter_by(word=word, updated_by=current_user.username).first()
        if word_incorrect_count:
            # Safely increment the count if the row exists
            word_incorrect_count.incorrect_count += 1
            word_incorrect_count.updated_at = db.func.now()
        else:
            # Create a new row if it does not exist
            word_incorrect_count = cls(word=word, incorrect_count=1, updated_by=current_user.username, updated_at=db.func.now())
            db.session.add(word_incorrect_count)
        
        # Commit the changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to update incorrect count: {e}") 
    
    @classmethod
    def get_learnt_words(cls):
        return [word.word for word in cls.query.filter(cls.count > 0).all()]
    
    # New methods for summary statistics
    @classmethod
    def get_total_words(cls):
        return cls.query.count()

    @classmethod
    def get_total_counts(cls):
        return db.session.query(db.func.sum(cls.count)).scalar() or 0
    # get_total_counts() returns the total number of times a word has been answered correctly ordered by the date of the last update.
    
    @classmethod
    def get_daily_counts(cls, start_date, end_date):
        return db.session.query(
            func.date(cls.updated_at).label('date'),
            func.sum(cls.count).label('total_count')
        ).filter(
            cls.updated_at >= start_date,
            cls.updated_at <= end_date
        ).group_by(func.date(cls.updated_at)).order_by(func.date(cls.updated_at)).all()
    
    @classmethod
    def get_daily_incorrect_counts(cls, start_date, end_date):
        return db.session.query(
            func.date(cls.updated_at).label('date'),
            func.sum(cls.incorrect_count).label('total_incorrect_count'),
            cls.updated_by.label('updated_by')
        ).filter(
            cls.updated_at >= start_date,
            cls.updated_at <= end_date
        ).group_by(func.date(cls.updated_at)).order_by(func.date(cls.updated_at)).all()
    
    @classmethod
    def get_daily_incorrect_counts_by_user(cls, start_date, end_date):
        return db.session.query(
            func.date(cls.updated_at).label('date'),
            func.sum(cls.incorrect_count).label('total_incorrect_count')
        ).filter(
            cls.updated_at >= start_date,
            cls.updated_at <= end_date
        ).group_by(func.date(cls.updated_at)).group_by(cls.updated_by).order_by(func.date(cls.updated_at)).all()

from sqlalchemy.dialects.postgresql import JSON

class WordData(db.Model):
    __tablename__ = 'word_data'
    word = db.Column(db.String(150), primary_key=True)
    definition = db.Column(db.Text, nullable=False)
    incorrect_options = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())


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