from datetime import datetime
from ..extensions import db


class Chapter(db.Model):
    __tablename__ = 'chapters'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    order_num = db.Column(db.Integer, default=1)
    duration = db.Column(db.Integer, default=0)
    is_free = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('chapters', lazy='dynamic', order_by='Chapter.order_num'))

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'order_num': self.order_num,
            'duration': self.duration,
            'is_free': self.is_free,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
