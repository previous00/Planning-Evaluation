from datetime import date
from ...extensions import db
from ...models.growth import LearningPlan
from ...models.learning import UserCourseProgress
from .points_service import PointsService


class PlanService:

    @classmethod
    def check_plan_expiry(cls, user_id):
        today = date.today()
        expired_plans = LearningPlan.query.filter(
            LearningPlan.user_id == user_id,
            LearningPlan.status == 'active',
            LearningPlan.end_date < today
        ).all()

        for plan in expired_plans:
            progress = cls.evaluate_progress(plan)
            if progress >= plan.target_progress:
                plan.status = 'completed'
                PointsService.award_points(
                    user_id, PointsService.RULES['plan_complete']['points'],
                    'plan_complete', reference_id=plan.id,
                    description=f'完成学习计划: {plan.title}'
                )
            else:
                plan.status = 'expired'

        if expired_plans:
            db.session.commit()

    @classmethod
    def evaluate_progress(cls, plan):
        if not plan.course_id:
            return 0.0
        progress = UserCourseProgress.query.filter_by(
            user_id=plan.user_id, course_id=plan.course_id
        ).first()
        return progress.progress if progress else 0.0

    @classmethod
    def get_plan_detail(cls, plan):
        current_progress = cls.evaluate_progress(plan)
        today = date.today()
        total_days = (plan.end_date - plan.start_date).days
        elapsed_days = (today - plan.start_date).days
        remaining_days = max((plan.end_date - today).days, 0)

        return {
            **plan.to_dict(),
            'current_progress': current_progress,
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'remaining_days': remaining_days,
            'on_track': current_progress >= (elapsed_days / max(total_days, 1) * plan.target_progress)
        }
