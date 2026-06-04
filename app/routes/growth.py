from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from ..extensions import db
from ..models.growth import LearningPlan, PointsTransaction
from ..services.growth import PointsService, CheckInService, PlanService

growth_bp = Blueprint('growth', __name__)


@growth_bp.route('/plans', methods=['GET'])
@jwt_required()
def get_plans():
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '')

    PlanService.check_plan_expiry(user_id)

    query = LearningPlan.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    plans = query.order_by(LearningPlan.created_at.desc()).all()
    return jsonify({
        'plans': [PlanService.get_plan_detail(p) for p in plans]
    })


@growth_bp.route('/plans', methods=['POST'])
@jwt_required()
def create_plan():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    title = data.get('title', '').strip()
    if not title:
        return jsonify({'message': '计划标题不能为空'}), 400

    start_date = data.get('start_date')
    end_date = data.get('end_date')
    if not start_date or not end_date:
        return jsonify({'message': '请设置开始和结束日期'}), 400

    plan = LearningPlan(
        user_id=user_id,
        title=title,
        description=data.get('description', ''),
        course_id=data.get('course_id'),
        target_progress=data.get('target_progress', 100.0),
        daily_goal_minutes=data.get('daily_goal_minutes', 30),
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date)
    )
    db.session.add(plan)
    db.session.commit()

    return jsonify({'message': '学习计划创建成功', 'plan': plan.to_dict()}), 201


@growth_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_plan(plan_id):
    user_id = int(get_jwt_identity())
    plan = LearningPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({'message': '计划不存在'}), 404

    data = request.get_json()
    if 'title' in data:
        plan.title = data['title']
    if 'description' in data:
        plan.description = data['description']
    if 'daily_goal_minutes' in data:
        plan.daily_goal_minutes = data['daily_goal_minutes']
    if 'status' in data:
        plan.status = data['status']
    if 'end_date' in data:
        plan.end_date = date.fromisoformat(data['end_date'])

    db.session.commit()
    return jsonify({'message': '计划更新成功', 'plan': plan.to_dict()})


@growth_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_plan(plan_id):
    user_id = int(get_jwt_identity())
    plan = LearningPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({'message': '计划不存在'}), 404

    plan.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': '计划已取消'})


@growth_bp.route('/check-in', methods=['POST'])
@jwt_required()
def check_in():
    user_id = int(get_jwt_identity())
    checkin, is_new = CheckInService.do_checkin(user_id)

    if not is_new:
        return jsonify({
            'message': '今日已打卡',
            'checkin': checkin.to_dict(),
            'is_new': False
        })

    return jsonify({
        'message': f'打卡成功！连续{checkin.streak_count}天',
        'checkin': checkin.to_dict(),
        'is_new': True
    })


@growth_bp.route('/check-in/status', methods=['GET'])
@jwt_required()
def check_in_status():
    user_id = int(get_jwt_identity())
    status = CheckInService.get_status(user_id)
    return jsonify(status)


@growth_bp.route('/check-in/calendar', methods=['GET'])
@jwt_required()
def check_in_calendar():
    user_id = int(get_jwt_identity())
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)

    records = CheckInService.get_calendar(user_id, year, month)
    return jsonify({'records': records, 'year': year, 'month': month})


@growth_bp.route('/points', methods=['GET'])
@jwt_required()
def get_points():
    user_id = int(get_jwt_identity())
    account = PointsService.ensure_account(user_id)
    return jsonify({'points': account.to_dict()})


@growth_bp.route('/points/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    type_filter = request.args.get('type', '')

    query = PointsTransaction.query.filter_by(user_id=user_id)
    if type_filter:
        query = query.filter_by(type=type_filter)

    pagination = query.order_by(PointsTransaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'transactions': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@growth_bp.route('/points/rules', methods=['GET'])
def get_points_rules():
    return jsonify({'rules': PointsService.RULES})
