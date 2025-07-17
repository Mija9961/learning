from flask import Flask, render_template
from .extensions import db, login_manager, migrate, limiter
from .util.hooks import check_session_validity
from flask_login import current_user

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
    from .mocktest import mocktest_bp  # local import avoids circular dependency
    from .autogen import autogen_bp
    from .chat import chat_bp
    from .custom_subject import custom_subject_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(python_bp, url_prefix='/python')
    app.register_blueprint(mocktest_bp, url_prefix='/mocktest')
    app.register_blueprint(autogen_bp, url_prefix='/autogen')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(custom_subject_bp, url_prefix='/custom_subject')

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
        return render_template('home.html', user=current_user)
    
    # Custom 404 error handler
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    # Optional: handle 500 internal server errors
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    return app
