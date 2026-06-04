import json
from datetime import datetime
from ..extensions import db


class LearningProfile(db.Model):
    __tablename__ = 'learning_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    total_learning_days = db.Column(db.Integer, default=0)
    avg_daily_duration = db.Column(db.Float, default=0.0)
    completion_rate = db.Column(db.Float, default=0.0)
    avg_score = db.Column(db.Float, default=0.0)

    risk_level = db.Column(db.String(20), default='normal')
    risk_factors = db.Column(db.Text, default='[]')
    days_since_last_activity = db.Column(db.Integer, default=0)
    engagement_trend = db.Column(db.String(20), default='stable')

    learning_efficiency = db.Column(db.Float, default=0.0)
    improvement_rate = db.Column(db.Float, default=0.0)
    knowledge_retention = db.Column(db.Float, default=0.0)

    dimension_scores = db.Column(db.Text, default='{}')

    computed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('learning_profile', uselist=False))

    def get_risk_factors(self):
        return json.loads(self.risk_factors or '[]')

    def get_dimension_scores(self):
        return json.loads(self.dimension_scores or '{}')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_learning_days': self.total_learning_days,
            'avg_daily_duration': self.avg_daily_duration,
            'completion_rate': self.completion_rate,
            'avg_score': self.avg_score,
            'risk_level': self.risk_level,
            'risk_factors': self.get_risk_factors(),
            'days_since_last_activity': self.days_since_last_activity,
            'engagement_trend': self.engagement_trend,
            'learning_efficiency': self.learning_efficiency,
            'improvement_rate': self.improvement_rate,
            'knowledge_retention': self.knowledge_retention,
            'dimension_scores': self.get_dimension_scores(),
            'computed_at': self.computed_at.isoformat() if self.computed_at else None
        }


class AssessmentSnapshot(db.Model):
    __tablename__ = 'assessment_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    snapshot_date = db.Column(db.Date, nullable=False)
    risk_level = db.Column(db.String(20))
    completion_rate = db.Column(db.Float, default=0.0)
    avg_daily_duration = db.Column(db.Float, default=0.0)
    engagement_trend = db.Column(db.String(20))
    dimension_scores = db.Column(db.Text, default='{}')

    __table_args__ = (db.UniqueConstraint('user_id', 'snapshot_date', name='uq_snapshot_date'),)

    user = db.relationship('User', backref=db.backref('assessment_snapshots', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'risk_level': self.risk_level,
            'completion_rate': self.completion_rate,
            'avg_daily_duration': self.avg_daily_duration,
            'engagement_trend': self.engagement_trend,
            'dimension_scores': json.loads(self.dimension_scores or '{}')
        }
