import math
from collections import defaultdict

from ...models.course import Course
from ...models.learning import UserCourseProgress


class CollaborativeFilter:

    @classmethod
    def recommend(cls, user_id, limit=10, exclude_course_ids=None):
        exclude_ids = set(exclude_course_ids or [])

        all_progress = UserCourseProgress.query.all()
        if not all_progress:
            return []

        user_courses = defaultdict(dict)
        for p in all_progress:
            user_courses[p.user_id][p.course_id] = p.progress / 100.0

        user_vector = user_courses.get(user_id, {})
        if not user_vector:
            return []

        completed = UserCourseProgress.query.filter_by(
            user_id=user_id, status='completed'
        ).with_entities(UserCourseProgress.course_id).all()
        exclude_ids.update(c.course_id for c in completed)

        all_course_ids = set()
        for scores in user_courses.values():
            all_course_ids.update(scores.keys())

        course_vectors = defaultdict(dict)
        for uid, scores in user_courses.items():
            for cid, score in scores.items():
                course_vectors[cid][uid] = score

        similarity_matrix = {}
        course_list = list(all_course_ids)
        for i in range(len(course_list)):
            for j in range(i + 1, len(course_list)):
                ci, cj = course_list[i], course_list[j]
                sim = cls._cosine_similarity(course_vectors[ci], course_vectors[cj])
                if sim > 0:
                    similarity_matrix[(ci, cj)] = sim
                    similarity_matrix[(cj, ci)] = sim

        candidate_ids = all_course_ids - set(user_vector.keys()) - exclude_ids

        published = set(
            c.id for c in Course.query.filter_by(status='published')
            .with_entities(Course.id).all()
        )
        candidate_ids &= published

        scored = []
        for candidate in candidate_ids:
            numerator = 0.0
            denominator = 0.0
            for learned_id, learned_score in user_vector.items():
                sim = similarity_matrix.get((candidate, learned_id), 0.0)
                if sim > 0:
                    numerator += sim * learned_score
                    denominator += sim
            if denominator > 0:
                pred = numerator / denominator
                scored.append((candidate, round(pred, 4)))

        scored.sort(key=lambda x: -x[1])
        return scored[:limit]

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0

        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
        mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
