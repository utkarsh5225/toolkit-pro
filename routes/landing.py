from flask import Blueprint, render_template

landing_bp = Blueprint("landing", __name__)

@landing_bp.route("/")
def home():
    return render_template("landing.html")

@landing_bp.route("/pricing")
def pricing():
    return render_template("pricing.html")
