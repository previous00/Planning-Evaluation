from datetime import datetime
from ...extensions import db
from ...models.growth import PointsAccount, PointsTransaction


class PointsService:

    RULES = {
        'check_in': {'base': 5, 'streak_bonus': 1, 'max_streak_bonus': 10},
        'daily_study': {'per_10min': 1, 'daily_cap': 20},
        'complete_chapter': {'points': 30},
        'complete_course': {'points': 50},
        'plan_complete': {'points': 100},
        'purchase': {'percent': 10},
    }

    @classmethod
    def ensure_account(cls, user_id):
        account = PointsAccount.query.filter_by(user_id=user_id).first()
        if not account:
            account = PointsAccount(user_id=user_id)
            db.session.add(account)
            db.session.commit()
        return account

    @classmethod
    def get_balance(cls, user_id):
        account = cls.ensure_account(user_id)
        return account.balance

    @classmethod
    def award_points(cls, user_id, amount, type_name, reference_id=None, description=''):
        if amount <= 0:
            return None
        account = cls.ensure_account(user_id)
        account.balance += amount
        account.total_earned += amount
        account.updated_at = datetime.utcnow()

        transaction = PointsTransaction(
            user_id=user_id,
            amount=amount,
            type=type_name,
            reference_id=reference_id,
            description=description
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    @classmethod
    def spend_points(cls, user_id, amount, type_name, reference_id=None, description=''):
        if amount <= 0:
            raise ValueError('扣除积分数必须为正数')
        account = cls.ensure_account(user_id)
        if account.balance < amount:
            raise ValueError(f'积分不足，当前余额: {account.balance}，需要: {amount}')

        account.balance -= amount
        account.total_spent += amount
        account.updated_at = datetime.utcnow()

        transaction = PointsTransaction(
            user_id=user_id,
            amount=-amount,
            type=type_name,
            reference_id=reference_id,
            description=description
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    @classmethod
    def award_study_points(cls, user_id, duration_seconds):
        today = datetime.utcnow().date()
        today_earned = db.session.query(
            db.func.sum(PointsTransaction.amount)
        ).filter(
            PointsTransaction.user_id == user_id,
            PointsTransaction.type == 'daily_study',
            db.func.date(PointsTransaction.created_at) == today
        ).scalar() or 0

        cap = cls.RULES['daily_study']['daily_cap']
        if today_earned >= cap:
            return None

        points = duration_seconds // 600
        points = min(points, cap - today_earned)
        if points <= 0:
            return None

        return cls.award_points(
            user_id, points, 'daily_study',
            description=f'学习奖励（{duration_seconds // 60}分钟）'
        )

    @classmethod
    def award_purchase_points(cls, user_id, price, course_id=None):
        percent = cls.RULES['purchase']['percent']
        points = int(price * percent / 100)
        if points <= 0:
            return None
        return cls.award_points(
            user_id, points, 'purchase',
            reference_id=course_id,
            description=f'购课返积分（消费{price}元，返还{percent}%）'
        )
