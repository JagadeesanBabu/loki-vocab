from flask import Blueprint, request, jsonify, session
from flask_restful import Api, Resource
from flask_login import login_required, current_user
from database.models import WordData, WordCount
from services.vocab_service import get_next_question, check_answer, get_summary
from services.dashboard_service import DashboardService
from datetime import date, timedelta

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)

class QuizResource(Resource):
    @login_required
    def get(self):
        unlearned_words = WordData.get_unlearned_words(session['all_words'], max_count=10)
        if not unlearned_words:
            return jsonify({'message': 'Congratulations! You have learned all the words.'})
        question_data = get_next_question(unlearned_words)
        return jsonify(question_data)

class AnswerResource(Resource):
    @login_required
    def post(self):
        data = request.get_json()
        user_answer = data.get('answer')
        word = data.get('word')
        correct_answer = data.get('correct_answer')
        result_data = check_answer(user_answer, word, correct_answer)
        return jsonify(result_data)

class SummaryResource(Resource):
    @login_required
    def get(self):
        summary_data = get_summary()
        return jsonify(summary_data)

class DashboardResource(Resource):
    @login_required
    def get(self):
        today = date.today() + timedelta(days=1)
        one_month_ago = today - timedelta(days=30)
        daily_correct_counts_records_by_user = DashboardService.get_correct_counts_by_user(one_month_ago, today)
        daily_incorrect_counts_records = DashboardService.get_incorrect_counts_by_user(one_month_ago, today)
        return jsonify({
            'daily_correct_counts_records_by_user': daily_correct_counts_records_by_user,
            'daily_incorrect_counts_records': daily_incorrect_counts_records
        })

api.add_resource(QuizResource, '/api/quiz')
api.add_resource(AnswerResource, '/api/answer')
api.add_resource(SummaryResource, '/api/summary')
api.add_resource(DashboardResource, '/api/dashboard')
