from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import DailyUsage, db
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def home():
    today_usage = DailyUsage.query.filter_by(
        user_id=current_user.id, date=date.today()
    ).first()
    used_today = today_usage.count if today_usage else 0
    limit = None if current_user.plan == "pro" else 5
    
    return render_template(
        "dashboard.html",
        plan=current_user.plan,
        used_today=used_today,
        limit=limit,
    )
