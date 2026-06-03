from datetime import datetime
from ..extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'course_count': self.courses.count()
        }


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    cover_image = db.Column(db.String(256), default='')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    teacher_name = db.Column(db.String(100), default='')
    duration = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.String(20), default='beginner')
    price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='published')
    view_count = db.Column(db.Integer, default=0)
    student_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    learning_records = db.relationship('LearningRecord', backref='course', lazy='dynamic')
    user_progress = db.relationship('UserCourseProgress', backref='course', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_image': self.cover_image,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'teacher_name': self.teacher_name,
            'duration': self.duration,
            'difficulty': self.difficulty,
            'price': self.price,
            'status': self.status,
            'view_count': self.view_count,
            'student_count': self.student_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_simple_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'cover_image': self.cover_image,
            'category_name': self.category.name if self.category else None,
            'teacher_name': self.teacher_name,
            'difficulty': self.difficulty,
            'price': self.price,
            'student_count': self.student_count,
            'duration': self.duration
        }
