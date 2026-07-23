from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
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
    
    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(tools_bp, url_prefix="/tools")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Module-level app for gunicorn: gunicorn app:app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
