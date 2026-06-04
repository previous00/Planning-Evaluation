from datetime import datetime
from ..extensions import db


class CourseAnalytics(db.Model):
    __tablename__ = 'course_analytics'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    new_enrollments = db.Column(db.Integer, default=0)
    active_learners = db.Column(db.Integer, default=0)
    completions = db.Column(db.Integer, default=0)
    total_learning_seconds = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0.0)

    __table_args__ = (db.UniqueConstraint('course_id', 'date', name='uq_course_date'),)

    course = db.relationship('Course', backref=db.backref('analytics', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_title': self.course.title if self.course else None,
            'date': self.date.isoformat() if self.date else None,
            'new_enrollments': self.new_enrollments,
            'active_learners': self.active_learners,
            'completions': self.completions,
            'total_learning_seconds': self.total_learning_seconds,
            'revenue': self.revenue
        }


class PlatformDailyStats(db.Model):
    __tablename__ = 'platform_daily_stats'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    dau = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    new_enrollments = db.Column(db.Integer, default=0)
    total_learning_seconds = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    completions = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'dau': self.dau,
            'new_users': self.new_users,
            'new_enrollments': self.new_enrollments,
            'total_learning_seconds': self.total_learning_seconds,
            'total_revenue': self.total_revenue,
            'completions': self.completions
        }
