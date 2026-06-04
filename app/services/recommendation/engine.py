from collections import defaultdict

from ...models.course import Course
from ...models.learning import UserCourseProgress, Enrollment
from .collaborative import CollaborativeFilter
from .content_based import ContentBasedFilter
from .popularity import PopularityFilter
from .user_profile import UserProfileService


class RecommendationEngine:

    DEFAULT_WEIGHTS = {
        'collaborative': 0.40,
        'content_based': 0.35,
        'popularity': 0.25
    }

    COLD_START_WEIGHTS = {
        'collaborative': 0.0,
        'content_based': 0.35,
        'popularity': 0.65
    }

    @classmethod
    def recommend(cls, user_id, limit=10, strategy='all'):
        profile = UserProfileService.get_or_compute(user_id)
        is_cold = profile.total_courses_learned < 2

        # 排除所有已购买/已报名的课程（包括正在学和已完成的）
        enrolled_ids = set(
            e.course_id for e in Enrollment.query.filter_by(
                user_id=user_id
            ).with_entities(Enrollment.course_id).all()
        )
        progress_ids = set(
            p.course_id for p in UserCourseProgress.query.filter_by(
                user_id=user_id
            ).with_entities(UserCourseProgress.course_id).all()
        )
        exclude_ids = enrolled_ids | progress_ids

        in_progress_ids = set(
            p.course_id for p in UserCourseProgress.query.filter_by(
                user_id=user_id, status='learning'
            ).with_entities(UserCourseProgress.course_id).all()
        )

        if strategy == 'collaborative':
            raw = CollaborativeFilter.recommend(user_id, limit=limit * 2, exclude_course_ids=exclude_ids)
            results = [(cid, score, 'collaborative') for cid, score in raw]
            return cls._finalize(results, in_progress_ids, limit)

        if strategy == 'content':
            raw = ContentBasedFilter.recommend(user_id, limit=limit * 2, exclude_course_ids=exclude_ids)
            results = [(cid, score, 'content_based') for cid, score in raw]
            return cls._finalize(results, in_progress_ids, limit)

        if strategy == 'popularity':
            raw = PopularityFilter.recommend(user_id, limit=limit * 2, exclude_course_ids=exclude_ids)
            results = [(cid, score, 'popularity') for cid, score in raw]
            return cls._finalize(results, in_progress_ids, limit)

        weights = cls.COLD_START_WEIGHTS if is_cold else cls.DEFAULT_WEIGHTS

        collab_scores = {}
        content_scores = {}
        pop_scores = {}
        course_strategies = defaultdict(list)

        if weights['collaborative'] > 0:
            for cid, score in CollaborativeFilter.recommend(user_id, limit=20, exclude_course_ids=exclude_ids):
                collab_scores[cid] = score
                course_strategies[cid].append('collaborative')

        if weights['content_based'] > 0:
            for cid, score in ContentBasedFilter.recommend(user_id, limit=20, exclude_course_ids=exclude_ids):
                content_scores[cid] = score
                course_strategies[cid].append('content_based')

        if weights['popularity'] > 0:
            for cid, score in PopularityFilter.recommend(user_id, limit=20, exclude_course_ids=exclude_ids):
                pop_scores[cid] = score
                course_strategies[cid].append('popularity')

        all_candidates = set(collab_scores) | set(content_scores) | set(pop_scores)

        fused = []
        for cid in all_candidates:
            score = (
                weights['collaborative'] * collab_scores.get(cid, 0) +
                weights['content_based'] * content_scores.get(cid, 0) +
                weights['popularity'] * pop_scores.get(cid, 0)
            )
            dominant = max(course_strategies[cid], key=lambda s: {
                'collaborative': collab_scores,
                'content_based': content_scores,
                'popularity': pop_scores
            }[s].get(cid, 0))
            fused.append((cid, round(score, 4), dominant))

        return cls._finalize(fused, in_progress_ids, limit)

    @classmethod
    def _finalize(cls, scored_list, in_progress_ids, limit):
        adjusted = []
        for cid, score, strategy in scored_list:
            if cid in in_progress_ids:
                score *= 0.3
            adjusted.append((cid, round(score, 4), strategy))

        adjusted.sort(key=lambda x: -x[1])

        diversified = cls._enforce_diversity(adjusted)

        max_score = diversified[0][1] if diversified else 1.0
        max_score = max_score or 1.0

        results = []
        for rank, (cid, score, strategy) in enumerate(diversified[:limit], 1):
            course = Course.query.get(cid)
            if not course:
                continue
            results.append({
                'course': course.to_simple_dict(),
                'score': round(score / max_score, 4),
                'rank': rank,
                'strategy': strategy,
                'reason': cls._generate_reason(course, strategy)
            })
        return results

    @classmethod
    def _enforce_diversity(cls, scored_list):
        category_count = defaultdict(int)
        top_results = []
        deferred = []

        for item in scored_list:
            cid, score, strategy = item
            course = Course.query.get(cid)
            if not course:
                continue
            cat_id = course.category_id
            if category_count[cat_id] < 2:
                category_count[cat_id] += 1
                top_results.append(item)
            else:
                deferred.append(item)

        return top_results + deferred

    @classmethod
    def _generate_reason(cls, course, strategy):
        if strategy == 'collaborative':
            return f'学习了相似课程的同学也在学这门课'
        elif strategy == 'content_based':
            cat_name = course.category.name if course.category else '相关'
            return f'基于你对{cat_name}类课程的学习偏好推荐'
        elif strategy == 'popularity':
            return f'近期热门课程，{course.student_count}人正在学习'
        return '综合推荐：与你的学习兴趣高度匹配'

    @classmethod
    def get_popular(cls, limit=10):
        courses = Course.query.filter_by(status='published').all()
        if not courses:
            return []
        max_views = max((c.view_count for c in courses), default=1) or 1
        max_students = max((c.student_count for c in courses), default=1) or 1

        scored = []
        for course in courses:
            score = 0.35 * (course.view_count / max_views) + 0.65 * (course.student_count / max_students)
            scored.append((course, round(score, 4)))

        scored.sort(key=lambda x: -x[1])
        results = []
        for rank, (course, score) in enumerate(scored[:limit], 1):
            results.append({
                'course': course.to_simple_dict(),
                'score': score,
                'rank': rank,
                'strategy': 'popularity',
                'reason': f'热门课程，{course.student_count}人正在学习'
            })
        return results
