import json
from datetime import datetime, timedelta
from sqlalchemy import func, distinct
from ...extensions import db
from ...models.learning import LearningRecord, UserCourseProgress
from ...models.assessment import LearningProfile, AssessmentSnapshot


class ProfileService:

    CACHE_HOURS = 2

    @classmethod
    def get_or_compute(cls, user_id, force=False):
        profile = LearningProfile.query.filter_by(user_id=user_id).first()
        if profile and not force:
            age = datetime.utcnow() - profile.computed_at
            if age < timedelta(hours=cls.CACHE_HOURS):
                return profile
        return cls.compute_profile(user_id, profile)

    @classmethod
    def compute_profile(cls, user_id, existing=None):
        profile = existing or LearningProfile(user_id=user_id)

        records = LearningRecord.query.filter_by(user_id=user_id).all()
        progress_list = UserCourseProgress.query.filter_by(user_id=user_id).all()

        if not records:
            profile.computed_at = datetime.utcnow()
            if not existing:
                db.session.add(profile)
            db.session.commit()
            return profile

        learning_days = set()
        total_duration = 0
        for r in records:
            if r.duration and r.duration > 0:
                learning_days.add(r.created_at.date())
                total_duration += r.duration

        profile.total_learning_days = len(learning_days)
        profile.avg_daily_duration = round(total_duration / max(len(learning_days), 1) / 60, 1)

        total_courses = len(progress_list)
        completed = sum(1 for p in progress_list if p.status == 'completed')
        profile.completion_rate = round(completed / max(total_courses, 1) * 100, 1)

        avg_progress = sum(p.progress for p in progress_list) / max(total_courses, 1)
        profile.avg_score = round(avg_progress, 1)

        if records:
            last_record = max(records, key=lambda r: r.created_at)
            profile.days_since_last_activity = (datetime.utcnow() - last_record.created_at).days
        else:
            profile.days_since_last_activity = 999

        profile.learning_efficiency = cls._compute_efficiency(progress_list)
        profile.improvement_rate = cls._compute_improvement(records)
        profile.knowledge_retention = cls._compute_retention(records)

        profile.dimension_scores = json.dumps(cls._compute_dimensions(
            profile, records, progress_list
        ))

        profile.engagement_trend = cls._compute_trend(records)

        profile.computed_at = datetime.utcnow()

        if not existing:
            db.session.add(profile)
        db.session.commit()
        return profile

    @classmethod
    def _compute_efficiency(cls, progress_list):
        total_progress = sum(p.progress for p in progress_list)
        total_hours = sum(p.total_duration for p in progress_list) / 3600
        if total_hours == 0:
            return 0.0
        return round(total_progress / total_hours, 2)

    @classmethod
    def _compute_improvement(cls, records):
        now = datetime.utcnow()
        this_week = [r for r in records if (now - r.created_at).days < 7]
        last_week = [r for r in records if 7 <= (now - r.created_at).days < 14]

        this_duration = sum(r.duration or 0 for r in this_week)
        last_duration = sum(r.duration or 0 for r in last_week)

        if last_duration == 0:
            return 0.0
        return round((this_duration - last_duration) / last_duration * 100, 1)

    @classmethod
    def _compute_retention(cls, records):
        course_visits = {}
        for r in records:
            if r.course_id not in course_visits:
                course_visits[r.course_id] = set()
            course_visits[r.course_id].add(r.created_at.date())

        if not course_visits:
            return 0.0

        multi_day_courses = sum(1 for days in course_visits.values() if len(days) > 1)
        return round(multi_day_courses / len(course_visits) * 100, 1)

    @classmethod
    def _compute_dimensions(cls, profile, records, progress_list):
        now = datetime.utcnow()

        recent_days = set()
        for r in records:
            if (now - r.created_at).days < 30:
                recent_days.add(r.created_at.date())
        consistency = min(round(len(recent_days) / 30 * 100, 1), 100)

        avg_duration_per_session = 0
        session_records = [r for r in records if r.duration and r.duration > 0]
        if session_records:
            avg_duration_per_session = sum(r.duration for r in session_records) / len(session_records)
        depth = min(round(avg_duration_per_session / 1800 * 100, 1), 100)

        unique_courses = len(set(r.course_id for r in records))
        breadth = min(round(unique_courses / 5 * 100, 1), 100)

        speed = min(profile.learning_efficiency / 20 * 100, 100) if profile.learning_efficiency else 0

        engagement = min(round(profile.avg_daily_duration / 60 * 100, 1), 100)

        return {
            'consistency': consistency,
            'depth': depth,
            'breadth': breadth,
            'speed': round(speed, 1),
            'engagement': engagement
        }

    @classmethod
    def _compute_trend(cls, records):
        now = datetime.utcnow()
        this_week = sum(r.duration or 0 for r in records if (now - r.created_at).days < 7)
        last_week = sum(r.duration or 0 for r in records if 7 <= (now - r.created_at).days < 14)

        if last_week == 0:
            return 'stable'
        change = (this_week - last_week) / last_week
        if change > 0.2:
            return 'improving'
        elif change < -0.2:
            return 'declining'
        return 'stable'

    @classmethod
    def take_snapshot(cls, user_id):
        profile = cls.get_or_compute(user_id)
        today = datetime.utcnow().date()

        existing = AssessmentSnapshot.query.filter_by(
            user_id=user_id, snapshot_date=today
        ).first()
        if existing:
            return existing

        snapshot = AssessmentSnapshot(
            user_id=user_id,
            snapshot_date=today,
            risk_level=profile.risk_level,
            completion_rate=profile.completion_rate,
            avg_daily_duration=profile.avg_daily_duration,
            engagement_trend=profile.engagement_trend,
            dimension_scores=profile.dimension_scores
        )
        db.session.add(snapshot)
        db.session.commit()
        return snapshot
