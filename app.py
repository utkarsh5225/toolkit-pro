from flask import Flask, request, session
from flask_login import LoginManager
from flask_talisman import Talisman
from config import Config
from extensions import limiter
from models import db, User
import os
import secrets

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ---- Security Headers ----
    csp = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'img-src': ["'self'", "data:", "blob:"],
        'frame-ancestors': ["'none'"],
        'form-action': ["'self'"],
    }
    Talisman(app, content_security_policy=csp, force_https=False)
    
    # ---- Rate Limiter ----
    limiter.init_app(app)
    
    # ---- CSRF Protection ----
    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            if request.path == "/billing/webhook":
                return
            token = session.get("_csrf_token")
            if not token:
                session["_csrf_token"] = secrets.token_hex(32)
                return
            form_token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
            if not form_token or not secrets.compare_digest(token, form_token):
                return {"error": "CSRF validation failed"}, 403
    
    @app.context_processor
    def inject_csrf():
        return {"csrf_token": session.get("_csrf_token", "")}
    
    # ---- File upload limits ----
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    # ---- Database ----
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from routes.landing import landing_bp
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.tools import tools_bp
    from routes.billing import billing_bp
    from routes.settings import settings_bp
    
    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(tools_bp, url_prefix="/tools")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    
    # ---- Error handlers ----
    @app.errorhandler(413)
    def too_large(e):
        return {"error": "file_too_large", "message": "File exceeds 50MB limit."}, 413
    
    @app.errorhandler(429)
    def ratelimit_error(e):
        return {"error": "rate_limited", "message": "Too many requests."}, 429
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
