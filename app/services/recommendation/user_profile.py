import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ...extensions import db
from ...models.recommendation import UserProfile
from ...models.learning import LearningRecord, UserCourseProgress
from ...models.course import Course


class UserProfileService:

    ACTION_WEIGHTS = {
        'view': 0.1,
        'start': 0.3,
        'progress': 0.6,
        'complete': 1.0
    }

    @classmethod
    def get_or_compute(cls, user_id, force_refresh=False):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if profile and not force_refresh:
            if (datetime.utcnow() - profile.updated_at) < timedelta(hours=1):
                return profile
        return cls.compute_profile(user_id, profile)

    @classmethod
    def compute_profile(cls, user_id, existing_profile=None):
        progress_records = UserCourseProgress.query.filter_by(user_id=user_id).all()
        learning_records = LearningRecord.query.filter_by(user_id=user_id).all()

        if not progress_records and not learning_records:
            if existing_profile:
                return existing_profile
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
            return profile

        category_scores = defaultdict(float)
        difficulty_scores = defaultdict(float)
        teacher_scores = defaultdict(float)
        duration_counts = defaultdict(int)

        course_cache = {}
        for p in progress_records:
            course = course_cache.get(p.course_id)
            if not course:
                course = Course.query.get(p.course_id)
                course_cache[p.course_id] = course
            if not course:
                continue

            if p.progress >= 100:
                weight = cls.ACTION_WEIGHTS['complete']
            elif p.progress >= 50:
                weight = cls.ACTION_WEIGHTS['progress']
            elif p.progress > 0:
                weight = cls.ACTION_WEIGHTS['start']
            else:
                weight = cls.ACTION_WEIGHTS['view']

            if course.category_id:
                category_scores[str(course.category_id)] += weight
            difficulty_scores[course.difficulty] += weight
            if course.teacher_name:
                teacher_scores[course.teacher_name] += weight

            if course.duration <= 720:
                duration_counts['short'] += 1
            elif course.duration <= 1440:
                duration_counts['medium'] += 1
            else:
                duration_counts['long'] += 1

        cat_total = sum(category_scores.values()) or 1
        category_prefs = {k: round(v / cat_total, 3) for k, v in category_scores.items()}

        diff_total = sum(difficulty_scores.values()) or 1
        difficulty_prefs = {k: round(v / diff_total, 3) for k, v in difficulty_scores.items()}

        teacher_sorted = sorted(teacher_scores.items(), key=lambda x: -x[1])[:5]
        teacher_prefs = {k: round(v, 2) for k, v in teacher_sorted}

        preferred_duration = max(duration_counts, key=duration_counts.get) if duration_counts else 'medium'

        hour_counter = Counter()
        for r in learning_records:
            if r.created_at:
                hour_counter[r.created_at.hour] += 1
        active_hours = [h for h, _ in hour_counter.most_common(3)]

        total_duration_sec = sum(p.total_duration for p in progress_records)
        if learning_records:
            dates = sorted(set(r.created_at.date() for r in learning_records if r.created_at))
            active_days = len(dates) or 1
            avg_pace = round(total_duration_sec / 60 / active_days, 1)
        else:
            avg_pace = 0.0

        profile = existing_profile or UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        profile.category_preferences = json.dumps(category_prefs)
        profile.difficulty_preferences = json.dumps(difficulty_prefs)
        profile.teacher_preferences = json.dumps(teacher_prefs)
        profile.avg_learning_pace = avg_pace
        profile.preferred_duration = preferred_duration
        profile.active_hours = json.dumps(active_hours)
        profile.total_courses_learned = len(progress_records)
        profile.updated_at = datetime.utcnow()

        db.session.commit()
        return profile
