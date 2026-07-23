from flask import Blueprint, request, jsonify, send_file, render_template
from flask_login import login_required, current_user
from models import db, DailyUsage
from extensions import limiter
from datetime import date
import io
import os

tools_bp = Blueprint("tools", __name__)

DAILY_LIMIT = 5
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_PDF_MAGIC = b"%PDF"

def validate_pdf(data: bytes) -> bool:
    """Verify file starts with PDF magic bytes."""
    return data[:4] == ALLOWED_PDF_MAGIC or data[:5] == b"%PDF-"

def validate_image(data: bytes) -> bool:
    """Verify file has valid image magic bytes."""
    magic_signatures = [
        b"\x89PNG\r\n\x1a\n",          # PNG
        b"\xff\xd8\xff",                # JPEG
        b"RIFF",                        # WEBP (needs WEBP check after)
        b"GIF87a", b"GIF89a",          # GIF
        b"BM",                          # BMP
    ]
    for sig in magic_signatures:
        if data[:len(sig)] == sig:
            # Extra check for WEBP
            if sig == b"RIFF" and data[8:12] != b"WEBP":
                continue
            return True
    return False

def check_usage():
    """Check if user has remaining operations."""
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
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        allowed, count, limit = check_usage()
        if not allowed:
            return jsonify({
                "error": "daily_limit",
                "message": f"You've used {count}/{limit} free operations today. Upgrade to Pro.",
                "used": count,
                "limit": limit,
            }), 429
        return f(*args, **kwargs)
    return wrapper

def get_file() -> tuple:
    """Get and validate uploaded file. Returns (data, filename, error_json)."""
    file = request.files.get("file")
    if not file:
        return None, None, (jsonify({"error": "no_file"}), 400)
    if file.content_length and file.content_length > MAX_FILE_SIZE:
        return None, None, (jsonify({"error": "file_too_large", "message": "File exceeds 50MB limit."}), 413)
    data = file.read()
    if len(data) > MAX_FILE_SIZE:
        return None, None, (jsonify({"error": "file_too_large"}), 413)
    return data, file.filename, None

# ============ Tool Page Routes ============

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

@tools_bp.route("/qr-code")
def qr_code_page():
    return render_template("tools/qr_code.html")

@tools_bp.route("/file-converter")
def file_converter_page():
    return render_template("tools/file_converter.html")

# ============ API Endpoints ============

@tools_bp.route("/api/pdf-compress", methods=["POST"])
@login_required
@require_usage
@limiter.limit("30 per hour")
def pdf_compress():
    from tools.pdf_compress import compress_pdf
    data, fname, err = get_file()
    if err:
        return err
    if not validate_pdf(data):
        return jsonify({"error": "invalid_file", "message": "Not a valid PDF."}), 400
    
    try:
        quality = int(request.form.get("quality", 50))
        quality = max(0, min(100, quality))
    except (ValueError, TypeError):
        quality = 50
    
    result = compress_pdf(data, fname, quality=quality)
    if result is None:
        return jsonify({"error": "processing_failed"}), 500
    
    increment_usage()
    return send_file(io.BytesIO(result), mimetype="application/pdf",
                     as_attachment=True, download_name=f"compressed_{fname}")

@tools_bp.route("/api/pdf-merge", methods=["POST"])
@login_required
@require_usage
@limiter.limit("20 per hour")
def pdf_merge():
    from tools.pdf_merge import merge_pdfs
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "need_two_files"}), 400
    if len(files) > 20:
        return jsonify({"error": "too_many_files", "message": "Max 20 files."}), 400
    
    file_data = []
    for f in files:
        d = f.read()
        if not validate_pdf(d):
            return jsonify({"error": "invalid_pdf", "message": f"{f.filename} is not a valid PDF."}), 400
        file_data.append((d, f.filename))
    
    result = merge_pdfs(file_data)
    if result is None:
        return jsonify({"error": "processing_failed"}), 500
    
    increment_usage()
    return send_file(io.BytesIO(result), mimetype="application/pdf",
                     as_attachment=True, download_name="merged.pdf")

@tools_bp.route("/api/pdf-split", methods=["POST"])
@login_required
@require_usage
@limiter.limit("20 per hour")
def pdf_split():
    from tools.pdf_split import split_pdf
    data, fname, err = get_file()
    if err:
        return err
    if not validate_pdf(data):
        return jsonify({"error": "invalid_file"}), 400
    
    pages = request.form.get("pages", "")
    result = split_pdf(data, pages)
    if result is None:
        return jsonify({"error": "processing_failed"}), 500
    
    increment_usage()
    return send_file(io.BytesIO(result), mimetype="application/pdf",
                     as_attachment=True, download_name=f"split_{fname}")

@tools_bp.route("/api/image-bg-remove", methods=["POST"])
@login_required
@require_usage
@limiter.limit("10 per hour")
def image_bg_remove():
    from tools.image_bg_remove import remove_background
    data, fname, err = get_file()
    if err:
        return err
    if not validate_image(data):
        return jsonify({"error": "invalid_image"}), 400
    
    result, mime = remove_background(data)
    if result is None:
        return jsonify({"error": "processing_failed"}), 500
    
    increment_usage()
    return send_file(io.BytesIO(result), mimetype=mime,
                     as_attachment=True, download_name=f"nobg_{fname.rsplit('.',1)[0]}.png")

@tools_bp.route("/api/image-convert", methods=["POST"])
@login_required
@require_usage
@limiter.limit("30 per hour")
def image_convert():
    from tools.image_convert import convert_image
    data, fname, err = get_file()
    if err:
        return err
    if not validate_image(data):
        return jsonify({"error": "invalid_image"}), 400
    
    target_format = request.form.get("format", "png").lower()
    if target_format not in ("png", "jpg", "jpeg", "webp"):
        return jsonify({"error": "unsupported_format"}), 400
    
    result, mime = convert_image(data, target_format)
    if result is None:
        return jsonify({"error": "processing_failed"}), 500
    
    increment_usage()
    return send_file(io.BytesIO(result), mimetype=mime,
                     as_attachment=True, download_name=f"converted.{target_format}")

@tools_bp.route("/api/qr-code", methods=["POST"])
@login_required
@require_usage
@limiter.limit("30 per hour")
def qr_code_generate():
    import qrcode
    from PIL import Image
    
    text = request.form.get("text", "").strip()
    if not text or len(text) > 2048:
        return jsonify({"error": "invalid_input"}), 400
    
    try:
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        increment_usage()
        return send_file(io.BytesIO(buf.getvalue()), mimetype="image/png",
                         as_attachment=True, download_name="qrcode.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
