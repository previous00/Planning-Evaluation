import json
from datetime import datetime
from ..extensions import db


class RecommendationLog(db.Model):
    __tablename__ = 'recommendation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    strategy = db.Column(db.String(30), nullable=False)
    score = db.Column(db.Float, default=0.0)
    position = db.Column(db.Integer, default=0)
    is_clicked = db.Column(db.Boolean, default=False)
    is_enrolled = db.Column(db.Boolean, default=False)
    shown_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('recommendation_logs', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('recommendation_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'strategy': self.strategy,
            'score': self.score,
            'position': self.position,
            'is_clicked': self.is_clicked,
            'is_enrolled': self.is_enrolled,
            'shown_at': self.shown_at.isoformat() if self.shown_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None
        }


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    category_preferences = db.Column(db.Text, default='{}')
    difficulty_preferences = db.Column(db.Text, default='{}')
    teacher_preferences = db.Column(db.Text, default='{}')
    avg_learning_pace = db.Column(db.Float, default=0.0)
    preferred_duration = db.Column(db.String(20), default='medium')
    active_hours = db.Column(db.Text, default='[]')
    total_courses_learned = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('profile', uselist=False))

    def get_category_prefs(self):
        return json.loads(self.category_preferences or '{}')

    def get_difficulty_prefs(self):
        return json.loads(self.difficulty_preferences or '{}')

    def get_teacher_prefs(self):
        return json.loads(self.teacher_preferences or '{}')

    def get_active_hours(self):
        return json.loads(self.active_hours or '[]')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_preferences': self.get_category_prefs(),
            'difficulty_preferences': self.get_difficulty_prefs(),
            'teacher_preferences': self.get_teacher_prefs(),
            'avg_learning_pace': self.avg_learning_pace,
            'preferred_duration': self.preferred_duration,
            'active_hours': self.get_active_hours(),
            'total_courses_learned': self.total_courses_learned,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
