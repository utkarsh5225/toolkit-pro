from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from extensions import limiter
import re

auth_bp = Blueprint("auth", __name__)

# Password validation
def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    return None

def validate_email(email: str) -> str | None:
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return "Please enter a valid email address."
    if len(email) > 254:
        return "Email address is too long."
    return None

@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("10 per hour")  # Anti-abuse
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        err = validate_email(email) or validate_password(password)
        if err:
            flash(err, "danger")
            return render_template("signup.html")
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Log in instead.", "warning")
            return redirect(url_for("auth.login"))
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to ToolKit Pro!", "success")
        return redirect(url_for("dashboard.home"))
    
    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")  # Anti-brute-force
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.home"))
        
        flash("Invalid email or password.", "danger")
    
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing.home"))
