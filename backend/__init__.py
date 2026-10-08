"""Shared helpers: DB access, auth decorators, CSRF, uploads, pricing."""
import os, sqlite3, secrets, uuid
from functools import wraps
from flask import current_app, g, session, redirect, url_for, request, jsonify, flash
from werkzeug.utils import secure_filename

ORDER_STATUSES = ["Order Placed", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def current_user():
    if "user" not in g:
        uid = session.get("user_id")
        g.user = query("SELECT * FROM users WHERE id=?", (uid,), one=True) if uid else None
    return g.user


def account_type(user=None):
    """Return the UI/business account type: customer, farmer, seller, or admin."""
    user = user or current_user()
    if not user:
        return "guest"
    if user["role"] in ("seller", "farmer", "admin"):
        return user["role"]
    # Backward compatibility for databases created before farmer became a first-class role.
    if query("SELECT 1 FROM farmer_profiles WHERE user_id=?", (user["id"],), one=True):
        return "farmer"
    return "customer"


def account_required(*types):
    def deco(f):
        @wraps(f)
        @login_required
        def wrapper(*a, **kw):
            if account_type() not in types:
                if wants_json():
                    return jsonify(ok=False, error="This feature is not available for your account type."), 403
                flash("This feature is not available for your account type.", "error")
                return redirect(url_for("main.index"))
            return f(*a, **kw)
        return wrapper
    return deco


def wants_json():
    return request.is_json or request.path.startswith("/api") or request.method in ("PUT", "DELETE") \
        or request.headers.get("X-Requested-With") == "fetch"


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_user():
            if wants_json():
                return jsonify(ok=False, error="Please log in to continue."), 401
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return f(*a, **kw)
    return wrapper


def role_required(*roles):
    def deco(f):
        @wraps(f)
        @login_required
        def wrapper(*a, **kw):
            if current_user()["role"] not in roles:
                if wants_json():
                    return jsonify(ok=False, error="You do not have permission."), 403
                flash("You do not have permission to view that page.", "error")
                return redirect(url_for("main.index"))
            return f(*a, **kw)
        return wrapper
    return deco


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def check_csrf():
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            return False
    return True


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(file, subfolder):
    """Validate + store an uploaded image; returns DB path like 'uploads/products/x.jpg' or None."""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("Only JPG, JPEG, PNG or WEBP images are allowed.")
    head = file.stream.read(12); file.stream.seek(0)
    if not (head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG") or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")):
        raise ValueError("Uploaded file is not a valid image.")
    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, name))
    return f"uploads/{subfolder}/{name}"


def image_url(path):
    """Resolve an image path to a URL: upload -> local static file -> Unsplash fallback."""
    if not path:
        return url_for("static", filename="images/logo/placeholder.svg")
    if path.startswith("http"):
        return path
    if path.startswith("uploads/"):
        return url_for("main.media", filename=path[len("uploads/"):])
    local = os.path.join(current_app.static_folder, "images", path)
    if os.path.exists(local):
        return url_for("static", filename="images/" + path)
    # Bundled artwork that shows the exact subject (replaced automatically by a downloaded photo above).
    art = os.path.join("art", os.path.splitext(path)[0] + ".svg")
    if os.path.exists(os.path.join(current_app.static_folder, "images", art)):
        return url_for("static", filename="images/" + art.replace(os.sep, "/"))
    remote = current_app.config["GENERIC_REMOTE"].get(path)
    if remote:
        return remote
    # No verified photo yet: show a neutral labelled card instead of a wrong picture.
    label = os.path.splitext(os.path.basename(path))[0].replace("-", " ")
    return url_for("main.placeholder", label=label)


def sale_price(price, discount):
    return round(price * (100 - (discount or 0)) / 100)


def calc_totals(lines):
    """lines: iterable of (mrp, discount_pct, qty). Server-side source of truth."""
    cfg = current_app.config
    subtotal = sum(m * q for m, d, q in lines)
    net = sum(sale_price(m, d) * q for m, d, q in lines)
    discount = subtotal - net
    delivery = 0 if (net == 0 or net >= cfg["FREE_DELIVERY_ABOVE"]) else cfg["DELIVERY_FEE"]
    tax = round(net * cfg["TAX_PERCENT"] / 100)
    return dict(subtotal=subtotal, discount=discount, delivery=delivery, tax=tax, total=net + delivery + tax)
