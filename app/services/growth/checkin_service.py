from datetime import datetime, date, timedelta
from ...extensions import db
from ...models.growth import CheckIn
from .points_service import PointsService


class CheckInService:

    @classmethod
    def do_checkin(cls, user_id):
        today = date.today()
        existing = CheckIn.query.filter_by(user_id=user_id, check_in_date=today).first()
        if existing:
            return existing, False

        streak = cls._compute_streak(user_id, today)
        streak_count = streak + 1

        from ...models.learning import LearningRecord
        today_records = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            db.func.date(LearningRecord.created_at) == today
        ).all()
        duration = sum(r.duration or 0 for r in today_records)
        courses = len(set(r.course_id for r in today_records))

        checkin = CheckIn(
            user_id=user_id,
            check_in_date=today,
            duration=duration,
            courses_studied=courses,
            streak_count=streak_count
        )
        db.session.add(checkin)
        db.session.commit()

        rules = PointsService.RULES['check_in']
        bonus = min(streak_count - 1, rules['max_streak_bonus']) * rules['streak_bonus']
        total_points = rules['base'] + bonus
        PointsService.award_points(
            user_id, total_points, 'check_in',
            reference_id=checkin.id,
            description=f'每日打卡（连续{streak_count}天，+{total_points}积分）'
        )

        return checkin, True

    @classmethod
    def _compute_streak(cls, user_id, today):
        yesterday = today - timedelta(days=1)
        streak = 0
        current_date = yesterday
        while True:
            record = CheckIn.query.filter_by(
                user_id=user_id, check_in_date=current_date
            ).first()
            if not record:
                break
            streak += 1
            current_date -= timedelta(days=1)
        return streak

    @classmethod
    def get_status(cls, user_id):
        today = date.today()
        checkin = CheckIn.query.filter_by(user_id=user_id, check_in_date=today).first()
        streak = cls._compute_streak(user_id, today)
        if checkin:
            streak = checkin.streak_count

        return {
            'checked_in_today': checkin is not None,
            'streak_count': streak if not checkin else checkin.streak_count,
            'today_record': checkin.to_dict() if checkin else None
        }

    @classmethod
    def get_calendar(cls, user_id, year, month):
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        records = CheckIn.query.filter(
            CheckIn.user_id == user_id,
            CheckIn.check_in_date >= start,
            CheckIn.check_in_date < end
        ).all()

        return [r.to_dict() for r in records]
