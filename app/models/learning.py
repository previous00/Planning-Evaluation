from datetime import datetime
from ..extensions import db


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='uq_enrollment'),)

    user = db.relationship('User', backref=db.backref('enrollments', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('enrollments', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'enrolled_at': self.enrolled_at.isoformat()
        }


class LearningRecord(db.Model):
    __tablename__ = 'learning_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=True)
    action = db.Column(db.String(20), nullable=False)
    progress = db.Column(db.Float, default=0)
    duration = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chapter = db.relationship('Chapter', backref=db.backref('learning_records', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'chapter_id': self.chapter_id,
            'course_title': self.course.title if self.course else None,
            'chapter_title': self.chapter.title if self.chapter else None,
            'action': self.action,
            'progress': self.progress,
            'duration': self.duration,
            'created_at': self.created_at.isoformat()
        }


class UserCourseProgress(db.Model):
    __tablename__ = 'user_course_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    progress = db.Column(db.Float, default=0)
    total_duration = db.Column(db.Integer, default=0)
    last_learn_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='learning')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'course_title': self.course.title if self.course else None,
            'course_cover': self.course.cover_image if self.course else None,
            'progress': self.progress,
            'total_duration': self.total_duration,
            'last_learn_at': self.last_learn_at.isoformat() if self.last_learn_at else None,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
