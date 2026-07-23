from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from config import Config
from models import db, User
import stripe

billing_bp = Blueprint("billing", __name__)

@billing_bp.route("/upgrade")
@login_required
def upgrade():
    return render_template("pricing.html")

@billing_bp.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    stripe.api_key = Config.STRIPE_SECRET_KEY
    
    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": Config.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=Config.SITE_URL + "/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=Config.SITE_URL + "/pricing",
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Payment error: {str(e)}", "danger")
        return redirect(url_for("landing.pricing"))

@billing_bp.route("/webhook", methods=["POST"])
def webhook():
    stripe.api_key = Config.STRIPE_SECRET_KEY
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify({"error": "Invalid signature"}), 400
    
    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.plan = "pro"
            user.stripe_subscription_id = subscription_id
            user.subscription_status = "active"
            db.session.commit()
    
    # Handle subscription cancellation
    if event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user = User.query.filter_by(stripe_subscription_id=subscription["id"]).first()
        if user:
            user.plan = "free"
            user.subscription_status = "inactive"
            db.session.commit()
    
    return jsonify({"status": "ok"})

@billing_bp.route("/portal", methods=["POST"])
@login_required
def portal():
    stripe.api_key = Config.STRIPE_SECRET_KEY
    
    if not current_user.stripe_customer_id:
        flash("No billing account found.", "warning")
        return redirect(url_for("dashboard.home"))
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=Config.SITE_URL + "/dashboard",
        )
        return redirect(portal_session.url, code=303)
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("dashboard.home"))
