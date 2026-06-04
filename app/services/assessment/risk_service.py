import json
from datetime import datetime, timedelta
from ...extensions import db
from ...models.assessment import LearningProfile
from ...models.learning import LearningRecord, UserCourseProgress
from ...models.user import User


class RiskService:

    @classmethod
    def assess_risk(cls, user_id):
        profile = LearningProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return {'risk_level': 'normal', 'risk_factors': [], 'suggestions': []}

        factors = []
        suggestions = []

        if profile.days_since_last_activity > 14:
            factors.append('长期未学习（超过14天未登录学习）')
            suggestions.append('建议设定每日学习计划，保持学习连续性')
        elif profile.days_since_last_activity > 7:
            factors.append('近期学习频率下降（超过7天未学习）')
            suggestions.append('建议每天至少学习15分钟')

        if profile.completion_rate < 20 and profile.total_learning_days > 7:
            factors.append('课程完成率过低')
            suggestions.append('建议降低课程难度或缩小学习范围')

        if profile.engagement_trend == 'declining':
            factors.append('学习投入呈下降趋势')
            suggestions.append('建议调整学习内容，尝试更感兴趣的课程')

        if profile.avg_daily_duration < 10 and profile.total_learning_days > 3:
            factors.append('日均学习时长不足')
            suggestions.append('建议每天保证至少30分钟的专注学习')

        if profile.learning_efficiency < 5 and profile.total_learning_days > 7:
            factors.append('学习效率较低')
            suggestions.append('建议采用番茄工作法，提高专注度')

        if len(factors) >= 3:
            risk_level = 'high_risk'
        elif len(factors) >= 2:
            risk_level = 'at_risk'
        elif len(factors) >= 1:
            risk_level = 'low_risk'
        else:
            risk_level = 'normal'

        profile.risk_level = risk_level
        profile.risk_factors = json.dumps(factors, ensure_ascii=False)
        db.session.commit()

        return {
            'risk_level': risk_level,
            'risk_factors': factors,
            'suggestions': suggestions,
            'days_since_last_activity': profile.days_since_last_activity,
            'completion_rate': profile.completion_rate,
            'engagement_trend': profile.engagement_trend
        }

    @classmethod
    def get_at_risk_users(cls, threshold='at_risk'):
        risk_levels = ['at_risk', 'high_risk'] if threshold == 'at_risk' else ['high_risk']
        profiles = LearningProfile.query.filter(
            LearningProfile.risk_level.in_(risk_levels)
        ).all()

        results = []
        for p in profiles:
            user = User.query.get(p.user_id)
            if user:
                results.append({
                    'user_id': p.user_id,
                    'username': user.username,
                    'email': user.email,
                    'risk_level': p.risk_level,
                    'risk_factors': p.get_risk_factors(),
                    'days_since_last_activity': p.days_since_last_activity,
                    'completion_rate': p.completion_rate,
                    'engagement_trend': p.engagement_trend
                })
        return results
