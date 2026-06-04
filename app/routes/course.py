from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.course import Course, Category
from ..models.learning import LearningRecord, UserCourseProgress, Enrollment
from ..utils.auth import admin_required

course_bp = Blueprint('course', __name__)


@course_bp.route('', methods=['GET'])
def get_courses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category_id = request.args.get('category_id', type=int)
    difficulty = request.args.get('difficulty', '')
    keyword = request.args.get('keyword', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')

    query = Course.query.filter_by(status='published')

    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if keyword:
        query = query.filter(
            (Course.title.contains(keyword)) | (Course.description.contains(keyword))
        )

    if sort_by == 'popular':
        query = query.order_by(Course.student_count.desc())
    elif sort_by == 'newest':
        query = query.order_by(Course.created_at.desc())
    else:
        query = query.order_by(Course.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'courses': [c.to_simple_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@course_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.view_count += 1
    db.session.commit()
    return jsonify({'course': course.to_dict()})


@course_bp.route('', methods=['POST'])
@admin_required
def create_course():
    data = request.get_json()

    if not data.get('title'):
        return jsonify({'message': '课程标题不能为空'}), 400

    course = Course(
        title=data['title'],
        description=data.get('description', ''),
        cover_image=data.get('cover_image', ''),
        category_id=data.get('category_id'),
        teacher_name=data.get('teacher_name', ''),
        duration=data.get('duration', 0),
        difficulty=data.get('difficulty', 'beginner'),
        price=data.get('price', 0.0),
        status=data.get('status', 'published')
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({'message': '课程创建成功', 'course': course.to_dict()}), 201


@course_bp.route('/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json()

    for field in ['title', 'description', 'cover_image', 'category_id',
                  'teacher_name', 'duration', 'difficulty', 'price', 'status']:
        if field in data:
            setattr(course, field, data[field])

    db.session.commit()
    return jsonify({'message': '课程更新成功', 'course': course.to_dict()})


@course_bp.route('/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    LearningRecord.query.filter_by(course_id=course_id).delete()
    UserCourseProgress.query.filter_by(course_id=course_id).delete()
    Enrollment.query.filter_by(course_id=course_id).delete()
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': '课程删除成功'})


@course_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify({'categories': [c.to_dict() for c in categories]})
