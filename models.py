from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(20), default="free")  # free, pro
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    subscription_status = db.Column(db.String(20), default="inactive")
    api_key = db.Column(db.String(64), unique=True)
    dark_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage = db.relationship("DailyUsage", backref="user", lazy=True)
    file_history = db.relationship("FileRecord", backref="user", lazy=True)
    
    def generate_api_key(self):
        self.api_key = f"tk_{secrets.token_hex(24)}"
        return self.api_key

class DailyUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    count = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="unique_user_date"),
    )

class FileRecord(db.Model):
    """Track processed files for Pro users (file history feature)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tool = db.Column(db.String(50), nullable=False)  # e.g. 'pdf-compress'
    original_name = db.Column(db.String(256))
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)  # bytes
