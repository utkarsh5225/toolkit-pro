import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///toolkit.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "price_xxx")  # $7/mo Pro
    
    FREE_DAILY_LIMIT = 5
    SITE_NAME = "ToolKit Pro"
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:5000")
