from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.recommendation import RecommendationLog, UserProfile
from ..models.course import Course
from ..services.recommendation import RecommendationEngine, UserProfileService

recommend_bp = Blueprint('recommend', __name__)


@recommend_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 10, type=int)
    strategy = request.args.get('strategy', 'all')

    if strategy not in ('all', 'collaborative', 'content', 'popularity'):
        strategy = 'all'

    results = RecommendationEngine.recommend(user_id, limit=limit, strategy=strategy)

    log_ids = []
    for item in results:
        log = RecommendationLog(
            user_id=user_id,
            course_id=item['course']['id'],
            strategy=item['strategy'],
            score=item['score'],
            position=item['rank']
        )
        db.session.add(log)
        db.session.flush()
        log_ids.append(log.id)

    db.session.commit()

    profile = UserProfileService.get_or_compute(user_id)
    cat_prefs = profile.get_category_prefs()
    diff_prefs = profile.get_difficulty_prefs()

    top_categories = sorted(cat_prefs.items(), key=lambda x: -x[1])[:3]
    top_cat_names = []
    for cat_id, _ in top_categories:
        from ..models.course import Category
        cat = Category.query.get(int(cat_id))
        if cat:
            top_cat_names.append(cat.name)

    preferred_diff = max(diff_prefs, key=diff_prefs.get) if diff_prefs else 'beginner'

    return jsonify({
        'recommendations': results,
        'profile_summary': {
            'top_categories': top_cat_names,
            'preferred_difficulty': preferred_diff
        },
        'log_ids': log_ids
    })


@recommend_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    profile = UserProfileService.get_or_compute(user_id)

    cat_prefs = profile.get_category_prefs()
    enriched_cats = {}
    from ..models.course import Category
    for cat_id, weight in cat_prefs.items():
        cat = Category.query.get(int(cat_id))
        if cat:
            enriched_cats[cat.name] = weight

    return jsonify({
        'profile': {
            **profile.to_dict(),
            'category_names': enriched_cats
        }
    })


@recommend_bp.route('/profile/refresh', methods=['POST'])
@jwt_required()
def refresh_profile():
    user_id = int(get_jwt_identity())
    profile = UserProfileService.get_or_compute(user_id, force_refresh=True)
    return jsonify({'message': '用户画像已更新', 'profile': profile.to_dict()})


@recommend_bp.route('/click', methods=['POST'])
@jwt_required()
def track_click():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    log_id = data.get('log_id')
    course_id = data.get('course_id')

    if log_id:
        log = RecommendationLog.query.get(log_id)
        if log and log.user_id == user_id:
            log.is_clicked = True
            log.clicked_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': '点击已记录'})

    if course_id:
        log = RecommendationLog.query.filter_by(
            user_id=user_id, course_id=course_id, is_clicked=False
        ).order_by(RecommendationLog.shown_at.desc()).first()
        if log:
            log.is_clicked = True
            log.clicked_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': '点击已记录'})

    return jsonify({'message': '记录未找到'}), 404


@recommend_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    from ..models.user import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403

    total_impressions = RecommendationLog.query.count()
    total_clicks = RecommendationLog.query.filter_by(is_clicked=True).count()
    total_conversions = RecommendationLog.query.filter_by(is_enrolled=True).count()

    ctr = round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0
    conversion_rate = round(total_conversions / total_clicks, 4) if total_clicks > 0 else 0

    recommended_courses = db.session.query(
        db.func.count(db.distinct(RecommendationLog.course_id))
    ).scalar() or 0
    total_courses = Course.query.filter_by(status='published').count() or 1
    coverage = round(recommended_courses / total_courses, 4)

    strategies = ['collaborative', 'content_based', 'popularity']
    per_strategy = {}
    for s in strategies:
        s_impressions = RecommendationLog.query.filter_by(strategy=s).count()
        s_clicks = RecommendationLog.query.filter_by(strategy=s, is_clicked=True).count()
        s_ctr = round(s_clicks / s_impressions, 4) if s_impressions > 0 else 0
        per_strategy[s] = {
            'impressions': s_impressions,
            'clicks': s_clicks,
            'ctr': s_ctr
        }

    return jsonify({
        'stats': {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'ctr': ctr,
            'coverage': coverage,
            'conversion_rate': conversion_rate,
            'per_strategy': per_strategy
        }
    })


@recommend_bp.route('/popular', methods=['GET'])
def get_popular():
    limit = request.args.get('limit', 10, type=int)
    results = RecommendationEngine.get_popular(limit=limit)
    return jsonify({'recommendations': results})
