from datetime import datetime, date, timedelta
from sqlalchemy import func, distinct
from ...extensions import db
from ...models.learning import LearningRecord, UserCourseProgress, Enrollment
from ...models.course import Course
from ...models.user import User
from ...models.analytics import CourseAnalytics, PlatformDailyStats


class StatsService:

    @classmethod
    def compute_daily_stats(cls, target_date=None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        cls._compute_platform_stats(target_date)
        cls._compute_course_stats(target_date)

    @classmethod
    def _compute_platform_stats(cls, target_date):
        existing = PlatformDailyStats.query.filter_by(date=target_date).first()
        if existing:
            stats = existing
        else:
            stats = PlatformDailyStats(date=target_date)

        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

        stats.dau = db.session.query(
            func.count(distinct(LearningRecord.user_id))
        ).filter(
            LearningRecord.created_at >= day_start,
            LearningRecord.created_at < day_end
        ).scalar() or 0

        stats.new_users = User.query.filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()

        stats.new_enrollments = Enrollment.query.filter(
            Enrollment.enrolled_at >= day_start,
            Enrollment.enrolled_at < day_end
        ).count()

        stats.total_learning_seconds = db.session.query(
            func.sum(LearningRecord.duration)
        ).filter(
            LearningRecord.created_at >= day_start,
            LearningRecord.created_at < day_end,
            LearningRecord.duration > 0
        ).scalar() or 0

        stats.completions = UserCourseProgress.query.filter(
            UserCourseProgress.completed_at >= day_start,
            UserCourseProgress.completed_at < day_end
        ).count()

        enrollments_today = Enrollment.query.filter(
            Enrollment.enrolled_at >= day_start,
            Enrollment.enrolled_at < day_end
        ).all()
        stats.total_revenue = sum(
            Course.query.get(e.course_id).price or 0 for e in enrollments_today
            if Course.query.get(e.course_id)
        )

        if not existing:
            db.session.add(stats)
        db.session.commit()

    @classmethod
    def _compute_course_stats(cls, target_date):
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

        courses = Course.query.filter_by(status='published').all()
        for course in courses:
            existing = CourseAnalytics.query.filter_by(
                course_id=course.id, date=target_date
            ).first()
            if existing:
                analytics = existing
            else:
                analytics = CourseAnalytics(course_id=course.id, date=target_date)

            analytics.new_enrollments = Enrollment.query.filter(
                Enrollment.course_id == course.id,
                Enrollment.enrolled_at >= day_start,
                Enrollment.enrolled_at < day_end
            ).count()

            analytics.active_learners = db.session.query(
                func.count(distinct(LearningRecord.user_id))
            ).filter(
                LearningRecord.course_id == course.id,
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end
            ).scalar() or 0

            analytics.completions = UserCourseProgress.query.filter(
                UserCourseProgress.course_id == course.id,
                UserCourseProgress.completed_at >= day_start,
                UserCourseProgress.completed_at < day_end
            ).count()

            analytics.total_learning_seconds = db.session.query(
                func.sum(LearningRecord.duration)
            ).filter(
                LearningRecord.course_id == course.id,
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end,
                LearningRecord.duration > 0
            ).scalar() or 0

            analytics.revenue = analytics.new_enrollments * (course.price or 0)

            if not existing:
                db.session.add(analytics)

        db.session.commit()

    @classmethod
    def get_realtime_today(cls):
        today = date.today()
        day_start = datetime.combine(today, datetime.min.time())

        dau = db.session.query(
            func.count(distinct(LearningRecord.user_id))
        ).filter(LearningRecord.created_at >= day_start).scalar() or 0

        new_enrollments = Enrollment.query.filter(
            Enrollment.enrolled_at >= day_start
        ).count()

        total_seconds = db.session.query(
            func.sum(LearningRecord.duration)
        ).filter(
            LearningRecord.created_at >= day_start,
            LearningRecord.duration > 0
        ).scalar() or 0

        completions = UserCourseProgress.query.filter(
            UserCourseProgress.completed_at >= day_start
        ).count()

        active_courses = db.session.query(
            func.count(distinct(LearningRecord.course_id))
        ).filter(LearningRecord.created_at >= day_start).scalar() or 0

        return {
            'dau': dau,
            'new_enrollments': new_enrollments,
            'total_learning_seconds': total_seconds,
            'total_learning_hours': round(total_seconds / 3600, 1),
            'completions': completions,
            'active_courses': active_courses,
            'timestamp': datetime.utcnow().isoformat()
        }

    @classmethod
    def get_overview(cls, days=7):
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        daily_stats = PlatformDailyStats.query.filter(
            PlatformDailyStats.date >= start_date,
            PlatformDailyStats.date <= end_date
        ).order_by(PlatformDailyStats.date).all()

        return {
            'period': f'{days}d',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_stats': [s.to_dict() for s in daily_stats],
            'totals': {
                'dau_avg': round(sum(s.dau for s in daily_stats) / max(len(daily_stats), 1), 1),
                'total_enrollments': sum(s.new_enrollments for s in daily_stats),
                'total_revenue': sum(s.total_revenue for s in daily_stats),
                'total_completions': sum(s.completions for s in daily_stats),
                'total_learning_hours': round(
                    sum(s.total_learning_seconds for s in daily_stats) / 3600, 1
                )
            }
        }

    @classmethod
    def get_course_ranking(cls, metric='students', limit=10):
        if metric == 'students':
            courses = Course.query.filter_by(status='published').order_by(
                Course.student_count.desc()
            ).limit(limit).all()
        elif metric == 'completion':
            courses = db.session.query(Course).join(UserCourseProgress).filter(
                Course.status == 'published'
            ).group_by(Course.id).order_by(
                func.avg(UserCourseProgress.progress).desc()
            ).limit(limit).all()
        else:
            courses = Course.query.filter_by(status='published').order_by(
                Course.view_count.desc()
            ).limit(limit).all()

        results = []
        for c in courses:
            avg_progress = db.session.query(
                func.avg(UserCourseProgress.progress)
            ).filter_by(course_id=c.id).scalar() or 0

            completion_count = UserCourseProgress.query.filter_by(
                course_id=c.id, status='completed'
            ).count()

            results.append({
                'course_id': c.id,
                'title': c.title,
                'category_name': c.category.name if c.category else None,
                'student_count': c.student_count,
                'view_count': c.view_count,
                'avg_progress': round(avg_progress, 1),
                'completion_count': completion_count,
                'completion_rate': round(
                    completion_count / max(c.student_count, 1) * 100, 1
                )
            })
        return results
