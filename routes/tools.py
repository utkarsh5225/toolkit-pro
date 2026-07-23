from flask import Blueprint, request, jsonify, send_file, render_template
from flask_login import login_required, current_user
from models import db, DailyUsage
from datetime import date
import io

tools_bp = Blueprint("tools", __name__)

DAILY_LIMIT = 5

def check_usage():
    """Check if user has remaining operations. Returns (allowed, count, limit)."""
    if current_user.plan == "pro":
        return True, 0, None
    
    today_usage = DailyUsage.query.filter_by(
        user_id=current_user.id, date=date.today()
    ).first()
    
    count = today_usage.count if today_usage else 0
    if count >= DAILY_LIMIT:
        return False, count, DAILY_LIMIT
    return True, count, DAILY_LIMIT

def increment_usage():
    """Increment daily usage counter for free users."""
    if current_user.plan == "pro":
        return
    
    today = date.today()
    usage = DailyUsage.query.filter_by(user_id=current_user.id, date=today).first()
    if usage:
        usage.count += 1
    else:
        usage = DailyUsage(user_id=current_user.id, date=today, count=1)
        db.session.add(usage)
    db.session.commit()

def require_usage(f):
    """Decorator: check usage before processing tool request."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        allowed, count, limit = check_usage()
        if not allowed:
            return jsonify({
                "error": "daily_limit",
                "message": f"You've used {count}/{limit} free operations today. Upgrade to Pro for unlimited access.",
                "used": count,
                "limit": limit,
            }), 429
        return f(*args, **kwargs)
    return wrapper

# --- Tool page routes ---

@tools_bp.route("/pdf-compress")
def pdf_compress_page():
    return render_template("tools/pdf_compress.html")

@tools_bp.route("/pdf-merge")
def pdf_merge_page():
    return render_template("tools/pdf_merge.html")

@tools_bp.route("/pdf-split")
def pdf_split_page():
    return render_template("tools/pdf_split.html")

@tools_bp.route("/image-bg-remove")
def image_bg_remove_page():
    return render_template("tools/image_bg_remove.html")

@tools_bp.route("/image-convert")
def image_convert_page():
    return render_template("tools/image_convert.html")

@tools_bp.route("/text-tools")
def text_tools_page():
    return render_template("tools/text_tools.html")

# --- API endpoints ---

@tools_bp.route("/api/pdf-compress", methods=["POST"])
@login_required
@require_usage
def pdf_compress():
    from tools.pdf_compress import compress_pdf
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    result = compress_pdf(file.read(), file.filename)
    if result is None:
        return jsonify({"error": "Failed to compress PDF"}), 500
    
    increment_usage()
    return send_file(
        io.BytesIO(result),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"compressed_{file.filename}"
    )

@tools_bp.route("/api/pdf-merge", methods=["POST"])
@login_required
@require_usage
def pdf_merge():
    from tools.pdf_merge import merge_pdfs
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Upload at least 2 PDFs"}), 400
    
    file_data = [(f.read(), f.filename) for f in files]
    result = merge_pdfs(file_data)
    if result is None:
        return jsonify({"error": "Failed to merge PDFs"}), 500
    
    increment_usage()
    return send_file(
        io.BytesIO(result),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="merged.pdf"
    )

@tools_bp.route("/api/pdf-split", methods=["POST"])
@login_required
@require_usage
def pdf_split():
    from tools.pdf_split import split_pdf
    file = request.files.get("file")
    pages = request.form.get("pages", "")  # e.g., "1-3,5,7-9"
    
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    result = split_pdf(file.read(), pages)
    if result is None:
        return jsonify({"error": "Failed to split PDF"}), 500
    
    increment_usage()
    return send_file(
        io.BytesIO(result),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"split_{file.filename}"
    )

@tools_bp.route("/api/image-bg-remove", methods=["POST"])
@login_required
@require_usage
def image_bg_remove():
    from tools.image_bg_remove import remove_background
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    result, mime = remove_background(file.read())
    if result is None:
        return jsonify({"error": "Failed to remove background"}), 500
    
    increment_usage()
    ext = "png"
    return send_file(
        io.BytesIO(result),
        mimetype=mime,
        as_attachment=True,
        download_name=f"nobg_{file.filename.rsplit('.',1)[0]}.{ext}"
    )

@tools_bp.route("/api/image-convert", methods=["POST"])
@login_required
@require_usage
def image_convert():
    from tools.image_convert import convert_image
    file = request.files.get("file")
    target_format = request.form.get("format", "png").lower()
    
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    if target_format not in ("png", "jpg", "jpeg", "webp"):
        return jsonify({"error": "Unsupported format"}), 400
    
    result, mime = convert_image(file.read(), target_format)
    if result is None:
        return jsonify({"error": "Failed to convert image"}), 500
    
    increment_usage()
    return send_file(
        io.BytesIO(result),
        mimetype=mime,
        as_attachment=True,
        download_name=f"converted.{target_format}"
    )
