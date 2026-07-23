from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    plan = db.Column(db.String(20), default="free")  # free, pro
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    subscription_status = db.Column(db.String(20), default="inactive")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage = db.relationship("DailyUsage", backref="user", lazy=True)

class DailyUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    count = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="unique_user_date"),
    )
