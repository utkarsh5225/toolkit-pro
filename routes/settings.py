from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import re

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/")
@login_required
def index():
    return render_template("settings.html")

@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    email = request.form.get("email", "").strip().lower()
    if email and email != current_user.email:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            flash("Invalid email address.", "danger")
            return redirect(url_for("settings.index"))
        if User.query.filter_by(email=email).first():
            flash("Email already in use.", "danger")
            return redirect(url_for("settings.index"))
        current_user.email = email
        db.session.commit()
        flash("Email updated.", "success")
    
    return redirect(url_for("settings.index"))

@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    
    if not check_password_hash(current_user.password_hash, current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("settings.index"))
    
    if len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for("settings.index"))
    
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash("Password changed successfully.", "success")
    return redirect(url_for("settings.index"))

@settings_bp.route("/toggle-dark", methods=["POST"])
@login_required
def toggle_dark():
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    return jsonify({"dark_mode": current_user.dark_mode})

@settings_bp.route("/generate-key", methods=["POST"])
@login_required
def generate_key():
    if current_user.plan != "pro":
        flash("API keys require a Pro plan.", "warning")
        return redirect(url_for("settings.index"))
    current_user.generate_api_key()
    db.session.commit()
    flash("API key generated.", "success")
    return redirect(url_for("settings.index"))

@settings_bp.route("/delete", methods=["POST"])
@login_required
def delete_account():
    pw = request.form.get("confirm_password", "")
    if not check_password_hash(current_user.password_hash, pw):
        flash("Incorrect password. Account not deleted.", "danger")
        return redirect(url_for("settings.index"))
    
    db.session.delete(current_user)
    db.session.commit()
    flash("Account deleted.", "info")
    return redirect(url_for("landing.home"))
