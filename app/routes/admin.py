from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.user import User
from ..models.course import Course, Category
from ..models.learning import LearningRecord, UserCourseProgress, Enrollment
from ..utils.auth import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    user_count = User.query.count()
    course_count = Course.query.count()
    record_count = LearningRecord.query.count()
    active_learners = db.session.query(
        db.func.count(db.distinct(UserCourseProgress.user_id))
    ).filter_by(status='learning').scalar() or 0

    total_duration = db.session.query(
        db.func.sum(UserCourseProgress.total_duration)
    ).scalar() or 0

    return jsonify({
        'dashboard': {
            'user_count': user_count,
            'course_count': course_count,
            'record_count': record_count,
            'active_learners': active_learners,
            'total_duration': total_duration
        }
    })


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '').strip()

    query = User.query
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) | (User.email.contains(keyword))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'role' in data:
        user.role = data['role']
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']

    db.session.commit()
    return jsonify({'message': '用户信息更新成功', 'user': user.to_dict()})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return jsonify({'message': '不能删除管理员账户'}), 400

    LearningRecord.query.filter_by(user_id=user_id).delete()
    UserCourseProgress.query.filter_by(user_id=user_id).delete()
    Enrollment.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': '用户删除成功'})


@admin_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'message': '分类名称不能为空'}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({'message': '分类已存在'}), 400

    category = Category(name=name, description=data.get('description', ''))
    db.session.add(category)
    db.session.commit()

    return jsonify({'message': '分类创建成功', 'category': category.to_dict()}), 201


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data = request.get_json()

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']

    db.session.commit()
    return jsonify({'message': '分类更新成功', 'category': category.to_dict()})


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    Course.query.filter_by(category_id=category_id).update({'category_id': None})
    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': '分类删除成功'})


@admin_bp.route('/learning-stats', methods=['GET'])
@admin_required
def learning_stats():
    from sqlalchemy import func

    course_stats = db.session.query(
        Course.id,
        Course.title,
        func.count(UserCourseProgress.id).label('learner_count'),
        func.avg(UserCourseProgress.progress).label('avg_progress')
    ).outerjoin(UserCourseProgress).group_by(Course.id)\
        .order_by(func.count(UserCourseProgress.id).desc()).limit(10).all()

    stats = [{
        'course_id': s[0],
        'course_title': s[1],
        'learner_count': s[2],
        'avg_progress': round(s[3] or 0, 1)
    } for s in course_stats]

    return jsonify({'learning_stats': stats})
