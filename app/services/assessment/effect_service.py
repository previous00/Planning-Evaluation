from datetime import datetime, timedelta
from ...models.learning import LearningRecord, UserCourseProgress


class EffectService:

    @classmethod
    def compute_effectiveness(cls, user_id):
        progress_list = UserCourseProgress.query.filter_by(user_id=user_id).all()
        records = LearningRecord.query.filter_by(user_id=user_id).all()

        total_progress = sum(p.progress for p in progress_list)
        total_hours = sum(p.total_duration for p in progress_list) / 3600
        efficiency = round(total_progress / max(total_hours, 0.1), 2)

        now = datetime.utcnow()
        weeks_data = []
        for week_offset in range(4):
            start = now - timedelta(days=7 * (week_offset + 1))
            end = now - timedelta(days=7 * week_offset)
            week_records = [r for r in records if start <= r.created_at < end]
            week_duration = sum(r.duration or 0 for r in week_records)
            weeks_data.append(week_duration)

        weeks_data.reverse()
        improvement_rate = 0.0
        if len(weeks_data) >= 2 and weeks_data[-2] > 0:
            improvement_rate = round(
                (weeks_data[-1] - weeks_data[-2]) / weeks_data[-2] * 100, 1
            )

        completed_courses = [p for p in progress_list if p.status == 'completed']
        avg_completion_time = 0
        if completed_courses:
            completion_times = []
            for p in completed_courses:
                if p.started_at and p.completed_at:
                    days = (p.completed_at - p.started_at).days
                    completion_times.append(days)
            if completion_times:
                avg_completion_time = round(sum(completion_times) / len(completion_times), 1)

        active_days_per_week = []
        for week_offset in range(4):
            start = now - timedelta(days=7 * (week_offset + 1))
            end = now - timedelta(days=7 * week_offset)
            week_days = set()
            for r in records:
                if start <= r.created_at < end:
                    week_days.add(r.created_at.date())
            active_days_per_week.append(len(week_days))
        active_days_per_week.reverse()

        return {
            'efficiency': efficiency,
            'improvement_rate': improvement_rate,
            'weekly_duration_trend': weeks_data,
            'weekly_active_days': active_days_per_week,
            'avg_completion_days': avg_completion_time,
            'total_completed': len(completed_courses),
            'total_in_progress': len(progress_list) - len(completed_courses),
            'total_learning_hours': round(total_hours, 1)
        }
