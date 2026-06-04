from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.assessment import ProfileService, RiskService, EffectService
from ..models.assessment import AssessmentSnapshot

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/learning-profile', methods=['GET'])
@jwt_required()
def get_learning_profile():
    user_id = int(get_jwt_identity())
    profile = ProfileService.get_or_compute(user_id)
    risk = RiskService.assess_risk(user_id)

    return jsonify({
        'profile': profile.to_dict(),
        'risk': risk
    })


@profile_bp.route('/risk-assessment', methods=['GET'])
@jwt_required()
def get_risk_assessment():
    user_id = int(get_jwt_identity())
    ProfileService.get_or_compute(user_id)
    risk = RiskService.assess_risk(user_id)
    return jsonify({'risk': risk})


@profile_bp.route('/effect-assessment', methods=['GET'])
@jwt_required()
def get_effect_assessment():
    user_id = int(get_jwt_identity())
    result = EffectService.compute_effectiveness(user_id)
    return jsonify({'effect': result})


@profile_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    days = request.args.get('days', 30, type=int)

    from datetime import datetime, timedelta
    start_date = (datetime.utcnow() - timedelta(days=days)).date()

    snapshots = AssessmentSnapshot.query.filter(
        AssessmentSnapshot.user_id == user_id,
        AssessmentSnapshot.snapshot_date >= start_date
    ).order_by(AssessmentSnapshot.snapshot_date).all()

    return jsonify({'snapshots': [s.to_dict() for s in snapshots]})


@profile_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_profile():
    user_id = int(get_jwt_identity())
    profile = ProfileService.get_or_compute(user_id, force=True)
    RiskService.assess_risk(user_id)
    ProfileService.take_snapshot(user_id)
    return jsonify({'message': '学习画像已更新', 'profile': profile.to_dict()})
