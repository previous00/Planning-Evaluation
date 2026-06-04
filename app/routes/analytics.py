from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.auth import admin_required
from ..services.analytics import StatsService
from ..services.assessment import RiskService
from ..models.analytics import CourseAnalytics
from ..models.course import Course
from ..extensions import db

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/realtime', methods=['GET'])
@admin_required
def get_realtime():
    data = StatsService.get_realtime_today()
    return jsonify({'realtime': data})


@analytics_bp.route('/overview', methods=['GET'])
@admin_required
def get_overview():
    days = request.args.get('days', 7, type=int)
    data = StatsService.get_overview(days=days)
    return jsonify({'overview': data})


@analytics_bp.route('/courses/<int:course_id>', methods=['GET'])
@admin_required
def get_course_analytics(course_id):
    course = Course.query.get_or_404(course_id)
    days = request.args.get('days', 30, type=int)

    from datetime import date, timedelta
    start_date = date.today() - timedelta(days=days)

    analytics = CourseAnalytics.query.filter(
        CourseAnalytics.course_id == course_id,
        CourseAnalytics.date >= start_date
    ).order_by(CourseAnalytics.date).all()

    from sqlalchemy import func
    from ..models.learning import UserCourseProgress

    avg_progress = db.session.query(
        func.avg(UserCourseProgress.progress)
    ).filter_by(course_id=course_id).scalar() or 0

    completion_count = UserCourseProgress.query.filter_by(
        course_id=course_id, status='completed'
    ).count()

    return jsonify({
        'course': course.to_dict(),
        'daily_analytics': [a.to_dict() for a in analytics],
        'summary': {
            'avg_progress': round(avg_progress, 1),
            'completion_count': completion_count,
            'completion_rate': round(
                completion_count / max(course.student_count, 1) * 100, 1
            ),
            'total_revenue': course.student_count * (course.price or 0)
        }
    })


@analytics_bp.route('/courses/ranking', methods=['GET'])
@admin_required
def get_course_ranking():
    metric = request.args.get('metric', 'students')
    limit = request.args.get('limit', 10, type=int)
    results = StatsService.get_course_ranking(metric=metric, limit=limit)
    return jsonify({'ranking': results})


@analytics_bp.route('/engagement', methods=['GET'])
@admin_required
def get_engagement():
    from ..models.learning import UserCourseProgress
    from ..models.user import User
    from sqlalchemy import func

    total_users = User.query.filter_by(role='student').count()

    active_learners = db.session.query(
        func.count(db.distinct(UserCourseProgress.user_id))
    ).filter_by(status='learning').scalar() or 0

    completed_learners = db.session.query(
        func.count(db.distinct(UserCourseProgress.user_id))
    ).filter(UserCourseProgress.status == 'completed').scalar() or 0

    from ..models.assessment import LearningProfile
    risk_distribution = {}
    for level in ['normal', 'low_risk', 'at_risk', 'high_risk']:
        count = LearningProfile.query.filter_by(risk_level=level).count()
        risk_distribution[level] = count

    return jsonify({
        'engagement': {
            'total_users': total_users,
            'active_learners': active_learners,
            'completed_learners': completed_learners,
            'inactive_users': total_users - active_learners - completed_learners,
            'risk_distribution': risk_distribution
        }
    })


@analytics_bp.route('/risk-students', methods=['GET'])
@admin_required
def get_risk_students():
    threshold = request.args.get('threshold', 'at_risk')
    students = RiskService.get_at_risk_users(threshold)
    return jsonify({'students': students, 'total': len(students)})


@analytics_bp.route('/compute-daily', methods=['POST'])
@admin_required
def compute_daily():
    from datetime import date, timedelta
    target = request.args.get('date')
    if target:
        target_date = date.fromisoformat(target)
    else:
        target_date = date.today() - timedelta(days=1)

    StatsService.compute_daily_stats(target_date)
    return jsonify({'message': f'已计算 {target_date} 的统计数据'})
