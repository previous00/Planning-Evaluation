from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.learning import LearningRecord, UserCourseProgress, Enrollment
from ..models.course import Course

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/enroll', methods=['POST'])
@jwt_required()
def enroll_course():
    """报名/购买课程"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'message': '课程ID不能为空'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing:
        return jsonify({'message': '已报名该课程', 'enrolled': True})

    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()

    return jsonify({'message': '报名成功', 'enrolled': True}), 201


@learning_bp.route('/check-enroll/<int:course_id>', methods=['GET'])
@jwt_required()
def check_enrollment(course_id):
    """检查是否已报名"""
    user_id = int(get_jwt_identity())
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    # 免费课程无需报名
    if course.price <= 0:
        return jsonify({'enrolled': True, 'free': True})

    enrolled = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    return jsonify({'enrolled': enrolled is not None, 'free': False})


@learning_bp.route('/record', methods=['POST'])
@jwt_required()
def record_learning():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    course_id = data.get('course_id')
    action = data.get('action', 'view')
    progress = data.get('progress', 0)
    duration = data.get('duration', 0)

    if not course_id:
        return jsonify({'message': '课程ID不能为空'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    # 付费课程需要先报名才能学习（浏览不限制）
    if action != 'view' and course.price > 0:
        enrolled = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if not enrolled:
            return jsonify({'message': '请先购买课程', 'need_enroll': True}), 403

    record = LearningRecord(
        user_id=user_id,
        course_id=course_id,
        action=action,
        progress=progress,
        duration=duration
    )
    db.session.add(record)

    # 浏览行为不更新学习进度
    if action == 'view':
        db.session.commit()
        user_progress = UserCourseProgress.query.filter_by(
            user_id=user_id, course_id=course_id
        ).first()
        return jsonify({
            'message': '浏览记录已保存',
            'progress': user_progress.to_dict() if user_progress else None
        })

    user_progress = UserCourseProgress.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()

    if not user_progress:
        user_progress = UserCourseProgress(
            user_id=user_id,
            course_id=course_id,
            progress=progress,
            total_duration=duration,
            status='learning'
        )
        db.session.add(user_progress)
        course.student_count += 1
    else:
        if progress > user_progress.progress:
            user_progress.progress = progress
        user_progress.total_duration += duration
        user_progress.last_learn_at = datetime.utcnow()

        if progress >= 100:
            user_progress.status = 'completed'
            user_progress.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': '学习记录已保存', 'progress': user_progress.to_dict()})


@learning_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_all_progress():
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '')

    query = UserCourseProgress.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    progress_list = query.order_by(UserCourseProgress.last_learn_at.desc()).all()
    return jsonify({'progress': [p.to_dict() for p in progress_list]})


@learning_bp.route('/progress/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_progress(course_id):
    user_id = int(get_jwt_identity())
    progress = UserCourseProgress.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()

    if not progress:
        return jsonify({'progress': None})

    return jsonify({'progress': progress.to_dict()})


@learning_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = LearningRecord.query.filter_by(user_id=user_id)\
        .order_by(LearningRecord.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'records': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@learning_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent():
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 5, type=int)

    recent = UserCourseProgress.query.filter_by(user_id=user_id)\
        .order_by(UserCourseProgress.last_learn_at.desc())\
        .limit(limit).all()

    return jsonify({'recent': [r.to_dict() for r in recent]})


@learning_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())

    total_courses = UserCourseProgress.query.filter_by(user_id=user_id).count()
    completed_courses = UserCourseProgress.query.filter_by(
        user_id=user_id, status='completed'
    ).count()
    learning_courses = UserCourseProgress.query.filter_by(
        user_id=user_id, status='learning'
    ).count()

    total_duration = db.session.query(
        db.func.sum(UserCourseProgress.total_duration)
    ).filter_by(user_id=user_id).scalar() or 0

    total_records = LearningRecord.query.filter_by(user_id=user_id).count()

    return jsonify({
        'stats': {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'learning_courses': learning_courses,
            'total_duration': total_duration,
            'total_records': total_records
        }
    })
