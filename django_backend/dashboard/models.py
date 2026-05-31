import mongoengine as me
from datetime import datetime

class NewsArticle(me.Document):
    meta = {'collection': 'news_articles'}
    article_id = me.StringField(required=True, unique=True)
    title = me.StringField()
    content = me.StringField()
    url = me.StringField(unique=True)
    source = me.StringField()
    published_at = me.StringField()
    status = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)

class Quiz(me.Document):
    meta = {'collection': 'quizzes'}
    quiz_id = me.StringField(required=True, unique=True)
    article_id = me.StringField()
    topic = me.StringField()
    difficulty = me.StringField()
    questions = me.ListField(me.DictField())
    created_at = me.DateTimeField(default=datetime.utcnow)

class QuizAttempt(me.Document):
    meta = {'collection': 'quiz_attempts'}
    attempt_id = me.StringField(required=True, unique=True)
    user_id = me.IntField(required=True) # Refers to Django User ID (SQLite)
    quiz_id = me.StringField(required=True)
    score = me.IntField()
    answers = me.ListField(me.DictField())
    attempted_at = me.DateTimeField(default=datetime.utcnow)
