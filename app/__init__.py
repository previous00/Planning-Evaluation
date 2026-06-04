from flask import Flask
from flask_cors import CORS
from .extensions import db, jwt
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    from .routes.auth import auth_bp
    from .routes.course import course_bp
    from .routes.learning import learning_bp
    from .routes.admin import admin_bp
    from .routes.recommend import recommend_bp
    from .routes.chapter import chapter_bp
    from .routes.profile import profile_bp
    from .routes.growth import growth_bp
    from .routes.analytics import analytics_bp
    from .routes.mall import mall_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(course_bp, url_prefix='/api/courses')
    app.register_blueprint(learning_bp, url_prefix='/api/learning')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(recommend_bp, url_prefix='/api/recommend')
    app.register_blueprint(chapter_bp, url_prefix='/api/chapters')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(growth_bp, url_prefix='/api/growth')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(mall_bp, url_prefix='/api/mall')

    with app.app_context():
        db.create_all()

    return app
