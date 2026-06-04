from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.learning import LearningRecord, UserCourseProgress, Enrollment
from ..models.course import Course
from ..models.chapter import Chapter
from ..models.user import User

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/enroll', methods=['POST'])
@jwt_required()
def enroll_course():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    course_id = data.get('course_id')
    coupon_order_id = data.get('coupon_order_id')

    if not course_id:
        return jsonify({'message': '课程ID不能为空'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing:
        return jsonify({'message': '已报名该课程', 'enrolled': True})

    discount = 0
    if coupon_order_id and course.price > 0:
        from ..models.mall import RedemptionOrder, MallItem
        coupon_order = RedemptionOrder.query.get(coupon_order_id)
        if not coupon_order or coupon_order.user_id != user_id:
            return jsonify({'message': '优惠券无效'}), 400
        if coupon_order.status != 'fulfilled' or coupon_order.used_at is not None:
            return jsonify({'message': '优惠券已使用或不可用'}), 400

        extra = coupon_order.item.get_extra_data()
        min_amount = extra.get('min_amount', 0)
        if course.price < min_amount:
            return jsonify({'message': f'课程价格未满{min_amount}元，不可使用此优惠券'}), 400

        discount = extra.get('discount', 0)
        coupon_order.used_at = datetime.utcnow()
        coupon_order.status = 'used'

    final_price = max(course.price - discount, 0)

    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()

    # 购课返积分（基于实付金额）
    if final_price > 0:
        try:
            from ..services.growth import PointsService
            PointsService.award_purchase_points(user_id, final_price, course_id=course_id)
        except Exception:
            pass

    return jsonify({
        'message': '报名成功',
        'enrolled': True,
        'original_price': course.price,
        'discount': discount,
        'final_price': final_price
    }), 201


@learning_bp.route('/check-enroll/<int:course_id>', methods=['GET'])
@jwt_required()
def check_enrollment(course_id):
    user_id = int(get_jwt_identity())
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    user = User.query.get(user_id)
    if user and user.role == 'admin':
        return jsonify({'enrolled': True, 'free': False, 'admin': True})

    if course.price <= 0:
        return jsonify({'enrolled': True, 'free': True})

    enrolled = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    return jsonify({'enrolled': enrolled is not None, 'free': False})


@learning_bp.route('/available-coupons/<int:course_id>', methods=['GET'])
@jwt_required()
def get_available_coupons(course_id):
    user_id = int(get_jwt_identity())
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    from ..models.mall import RedemptionOrder, MallItem

    coupon_orders = db.session.query(RedemptionOrder).join(MallItem).filter(
        RedemptionOrder.user_id == user_id,
        RedemptionOrder.status == 'fulfilled',
        RedemptionOrder.used_at == None,
        MallItem.type == 'coupon'
    ).all()

    available = []
    for order in coupon_orders:
        extra = order.item.get_extra_data()
        min_amount = extra.get('min_amount', 0)
        discount = extra.get('discount', 0)
        if course.price >= min_amount:
            available.append({
                'order_id': order.id,
                'item_name': order.item.name,
                'min_amount': min_amount,
                'discount': discount,
                'final_price': round(max(course.price - discount, 0), 2)
            })

    return jsonify({'coupons': available, 'course_price': course.price})


@learning_bp.route('/record', methods=['POST'])
@jwt_required()
def record_learning():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    course_id = data.get('course_id')
    chapter_id = data.get('chapter_id')
    action = data.get('action', 'view')
    duration = data.get('duration', 0)

    if not course_id:
        return jsonify({'message': '课程ID不能为空'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    if action != 'view' and course.price > 0:
        user = User.query.get(user_id)
        if not (user and user.role == 'admin'):
            enrolled = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
            if not enrolled:
                return jsonify({'message': '请先购买课程', 'need_enroll': True}), 403

    record = LearningRecord(
        user_id=user_id,
        course_id=course_id,
        chapter_id=chapter_id,
        action=action,
        duration=duration
    )
    db.session.add(record)

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
            progress=0,
            total_duration=duration,
            status='learning'
        )
        db.session.add(user_progress)
        course.student_count += 1
    else:
        user_progress.total_duration += duration
        user_progress.last_learn_at = datetime.utcnow()

    # 根据累计学习总时长与课程总时长自动计算进度百分比
    course_total_seconds = course.duration * 60
    if course_total_seconds > 0:
        computed_progress = min(
            round(user_progress.total_duration / course_total_seconds * 100, 1),
            100
        )
    else:
        computed_progress = 100

    user_progress.progress = computed_progress
    record.progress = computed_progress

    if computed_progress >= 100 and user_progress.status != 'completed':
        user_progress.status = 'completed'
        user_progress.completed_at = datetime.utcnow()

    db.session.commit()

    # 学习积分奖励
    try:
        from ..services.growth import PointsService
        PointsService.award_study_points(user_id, duration)
    except Exception:
        pass

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


@learning_bp.route('/record-beacon', methods=['POST'])
def record_learning_beacon():
    """处理sendBeacon发送的学习记录（页面关闭时）"""
    import json as json_module
    raw = request.get_json(force=True)
    token = raw.get('token', '')
    data = json_module.loads(raw.get('data', '{}'))

    if not token or not data.get('course_id'):
        return '', 204

    from flask_jwt_extended import decode_token
    try:
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
    except Exception:
        return '', 204

    course_id = data.get('course_id')
    chapter_id = data.get('chapter_id')
    duration = data.get('duration', 0)

    if duration < 5:
        return '', 204

    course = Course.query.get(course_id)
    if not course:
        return '', 204

    record = LearningRecord(
        user_id=user_id,
        course_id=course_id,
        chapter_id=chapter_id,
        action='progress',
        duration=duration
    )
    db.session.add(record)

    user_progress = UserCourseProgress.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    if user_progress:
        user_progress.total_duration += duration
        user_progress.last_learn_at = datetime.utcnow()
        course_total_seconds = course.duration * 60
        if course_total_seconds > 0:
            computed_progress = min(
                round(user_progress.total_duration / course_total_seconds * 100, 1),
                100
            )
            user_progress.progress = computed_progress
            if computed_progress >= 100 and user_progress.status != 'completed':
                user_progress.status = 'completed'
                user_progress.completed_at = datetime.utcnow()
    else:
        user_progress = UserCourseProgress(
            user_id=user_id,
            course_id=course_id,
            progress=0,
            total_duration=duration,
            status='learning'
        )
        db.session.add(user_progress)
        course.student_count += 1

    db.session.commit()
    return '', 204
