from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.chapter import Chapter
from ..models.course import Course
from ..models.user import User

chapter_bp = Blueprint('chapter', __name__)


@chapter_bp.route('/course/<int:course_id>', methods=['GET'])
def get_chapters(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order_num).all()
    return jsonify({'chapters': [c.to_dict() for c in chapters]})


@chapter_bp.route('/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'message': '章节不存在'}), 404
    return jsonify({'chapter': chapter.to_dict()})


@chapter_bp.route('/', methods=['POST'])
@jwt_required()
def create_chapter():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403

    data = request.get_json()
    course_id = data.get('course_id')
    title = data.get('title')

    if not course_id or not title:
        return jsonify({'message': '课程ID和标题不能为空'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': '课程不存在'}), 404

    max_order = db.session.query(db.func.max(Chapter.order_num)).filter_by(course_id=course_id).scalar() or 0

    chapter = Chapter(
        course_id=course_id,
        title=title,
        description=data.get('description', ''),
        order_num=max_order + 1,
        duration=data.get('duration', 0),
        is_free=(max_order == 0)
    )
    db.session.add(chapter)
    db.session.commit()

    return jsonify({'message': '章节创建成功', 'chapter': chapter.to_dict()}), 201


@chapter_bp.route('/<int:chapter_id>', methods=['PUT'])
@jwt_required()
def update_chapter(chapter_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'message': '章节不存在'}), 404

    data = request.get_json()
    if 'title' in data:
        chapter.title = data['title']
    if 'description' in data:
        chapter.description = data['description']
    if 'duration' in data:
        chapter.duration = data['duration']
    if 'order_num' in data:
        chapter.order_num = data['order_num']
    if 'is_free' in data:
        chapter.is_free = data['is_free']

    db.session.commit()
    return jsonify({'message': '章节更新成功', 'chapter': chapter.to_dict()})


@chapter_bp.route('/<int:chapter_id>', methods=['DELETE'])
@jwt_required()
def delete_chapter(chapter_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'message': '章节不存在'}), 404

    db.session.delete(chapter)
    db.session.commit()
    return jsonify({'message': '章节删除成功'})
