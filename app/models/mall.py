import json
from datetime import datetime
from ..extensions import db


class MallItem(db.Model):
    __tablename__ = 'mall_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    image = db.Column(db.String(256), default='')
    type = db.Column(db.String(30), nullable=False)
    points_cost = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=-1)
    status = db.Column(db.String(20), default='active')
    extra_data = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_extra_data(self):
        return json.loads(self.extra_data or '{}')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'type': self.type,
            'points_cost': self.points_cost,
            'stock': self.stock,
            'status': self.status,
            'extra_data': self.get_extra_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RedemptionOrder(db.Model):
    __tablename__ = 'redemption_orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('mall_items.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    fulfilled_at = db.Column(db.DateTime, nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('redemption_orders', lazy='dynamic'))
    item = db.relationship('MallItem', backref=db.backref('orders', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'points_spent': self.points_spent,
            'status': self.status,
            'fulfilled_at': self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
