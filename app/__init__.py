from flask import Flask, render_template
from .extensions import db, login_manager, migrate, limiter
from .util.hooks import check_session_validity


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    limiter.init_app(app)  # 👈 initialize limiter here

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # 👈 redirect unauthorized users here

    migrate.init_app(app, db)

    # Register blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    from .user import user_bp
    from .python import python_bp  # local import avoids circular dependency

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(python_bp, url_prefix='/python')

    with app.app_context():
        db.create_all()

     # Register session validity hook
    @app.before_request
    def before_request():
        response = check_session_validity()
        if response:
            return response
        
    @app.route('/', endpoint='index')
    def home():
        return render_template('home.html')

    return app
