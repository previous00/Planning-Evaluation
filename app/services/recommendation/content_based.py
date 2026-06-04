from ...models.course import Course
from ...models.learning import UserCourseProgress
from .user_profile import UserProfileService


class ContentBasedFilter:

    DURATION_BANDS = {
        'short': (0, 720),
        'medium': (721, 1440),
        'long': (1441, float('inf'))
    }

    @classmethod
    def recommend(cls, user_id, limit=10, exclude_course_ids=None):
        exclude_ids = set(exclude_course_ids or [])

        completed = UserCourseProgress.query.filter_by(
            user_id=user_id, status='completed'
        ).with_entities(UserCourseProgress.course_id).all()
        exclude_ids.update(c.course_id for c in completed)

        profile = UserProfileService.get_or_compute(user_id)
        cat_prefs = profile.get_category_prefs()
        diff_prefs = profile.get_difficulty_prefs()
        teacher_prefs = profile.get_teacher_prefs()
        pref_duration = profile.preferred_duration

        courses = Course.query.filter_by(status='published').all()
        if not courses:
            return []

        scored = []
        for course in courses:
            if course.id in exclude_ids:
                continue

            cat_score = cat_prefs.get(str(course.category_id), 0.0)
            diff_score = diff_prefs.get(course.difficulty, 0.0)
            teacher_score = 1.0 if course.teacher_name in teacher_prefs else 0.0
            dur_score = cls._duration_match(course.duration, pref_duration)

            score = 0.4 * cat_score + 0.25 * diff_score + 0.2 * teacher_score + 0.15 * dur_score
            if score > 0:
                scored.append((course.id, round(score, 4)))

        scored.sort(key=lambda x: -x[1])
        return scored[:limit]

    @classmethod
    def _duration_match(cls, course_duration, preferred):
        bands = ['short', 'medium', 'long']
        course_band = 'medium'
        for band, (low, high) in cls.DURATION_BANDS.items():
            if low <= course_duration <= high:
                course_band = band
                break

        if course_band == preferred:
            return 1.0
        if abs(bands.index(course_band) - bands.index(preferred)) == 1:
            return 0.5
        return 0.2
