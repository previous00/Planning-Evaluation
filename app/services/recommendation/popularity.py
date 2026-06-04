from ...models.course import Course
from ...models.learning import UserCourseProgress


class PopularityFilter:

    WEIGHT_VIEWS = 0.35
    WEIGHT_STUDENTS = 0.65

    @classmethod
    def recommend(cls, user_id, limit=10, exclude_course_ids=None):
        exclude_ids = set(exclude_course_ids or [])

        completed = UserCourseProgress.query.filter_by(
            user_id=user_id, status='completed'
        ).with_entities(UserCourseProgress.course_id).all()
        exclude_ids.update(c.course_id for c in completed)

        courses = Course.query.filter_by(status='published').all()
        if not courses:
            return []

        max_views = max((c.view_count for c in courses), default=1) or 1
        max_students = max((c.student_count for c in courses), default=1) or 1

        scored = []
        for course in courses:
            if course.id in exclude_ids:
                continue
            view_score = course.view_count / max_views
            student_score = course.student_count / max_students

            score = cls.WEIGHT_VIEWS * view_score + cls.WEIGHT_STUDENTS * student_score
            scored.append((course.id, round(score, 4)))

        scored.sort(key=lambda x: -x[1])
        return scored[:limit]
