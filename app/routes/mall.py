from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.mall import MallItem, RedemptionOrder
from ..models.user import User
from ..services.growth import PointsService
from ..utils.auth import admin_required

mall_bp = Blueprint('mall', __name__)


@mall_bp.route('/items', methods=['GET'])
@jwt_required()
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    type_filter = request.args.get('type', '')

    query = MallItem.query.filter_by(status='active')
    if type_filter:
        query = query.filter_by(type=type_filter)

    pagination = query.order_by(MallItem.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@mall_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    item = MallItem.query.get_or_404(item_id)
    return jsonify({'item': item.to_dict()})


@mall_bp.route('/items', methods=['POST'])
@admin_required
def create_item():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'message': '商品名称不能为空'}), 400

    item_type = data.get('type', '')
    if item_type not in ('coupon', 'vip', 'resource', 'physical'):
        return jsonify({'message': '无效的商品类型'}), 400

    points_cost = data.get('points_cost', 0)
    if points_cost <= 0:
        return jsonify({'message': '积分价格必须大于0'}), 400

    import json
    item = MallItem(
        name=name,
        description=data.get('description', ''),
        image=data.get('image', ''),
        type=item_type,
        points_cost=points_cost,
        stock=data.get('stock', -1),
        extra_data=json.dumps(data.get('extra_data', {}), ensure_ascii=False)
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({'message': '商品创建成功', 'item': item.to_dict()}), 201


@mall_bp.route('/items/<int:item_id>', methods=['PUT'])
@admin_required
def update_item(item_id):
    item = MallItem.query.get_or_404(item_id)
    data = request.get_json()

    import json
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'image' in data:
        item.image = data['image']
    if 'points_cost' in data:
        item.points_cost = data['points_cost']
    if 'stock' in data:
        item.stock = data['stock']
    if 'status' in data:
        item.status = data['status']
    if 'extra_data' in data:
        item.extra_data = json.dumps(data['extra_data'], ensure_ascii=False)

    db.session.commit()
    return jsonify({'message': '商品更新成功', 'item': item.to_dict()})


@mall_bp.route('/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    item = MallItem.query.get_or_404(item_id)
    item.status = 'inactive'
    db.session.commit()
    return jsonify({'message': '商品已下架'})


@mall_bp.route('/redeem', methods=['POST'])
@jwt_required()
def redeem_item():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'message': '请选择商品'}), 400

    item = MallItem.query.get(item_id)
    if not item or item.status != 'active':
        return jsonify({'message': '商品不存在或已下架'}), 404

    if item.stock == 0:
        return jsonify({'message': '商品库存不足'}), 400

    try:
        PointsService.spend_points(
            user_id, item.points_cost, 'redeem',
            reference_id=item_id,
            description=f'兑换商品: {item.name}'
        )
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

    if item.stock > 0:
        item.stock -= 1
        if item.stock == 0:
            item.status = 'sold_out'

    order = RedemptionOrder(
        user_id=user_id,
        item_id=item_id,
        points_spent=item.points_cost
    )
    db.session.add(order)

    if item.type in ('coupon', 'vip', 'resource'):
        from datetime import datetime
        order.status = 'fulfilled'
        order.fulfilled_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': '兑换成功',
        'order': order.to_dict()
    }), 201


@mall_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = RedemptionOrder.query.filter_by(user_id=user_id)\
        .order_by(RedemptionOrder.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'orders': [o.to_dict() for o in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@mall_bp.route('/orders/all', methods=['GET'])
@admin_required
def get_all_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')

    query = RedemptionOrder.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(RedemptionOrder.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'orders': [o.to_dict() for o in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@mall_bp.route('/orders/<int:order_id>/fulfill', methods=['PUT'])
@admin_required
def fulfill_order(order_id):
    order = RedemptionOrder.query.get_or_404(order_id)
    if order.status != 'pending':
        return jsonify({'message': '订单状态不允许此操作'}), 400

    order.status = 'fulfilled'
    order.fulfilled_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': '订单已完成', 'order': order.to_dict()})
