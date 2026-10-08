"""Public pages, profile, wishlist page, and the seller / admin dashboards."""
import re
from collections import OrderedDict
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from . import query, execute, current_user, login_required, role_required, account_type, save_upload, ORDER_STATUSES
from .products import BASE_SQL, product_dict

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    role = account_type()
    if role in ("customer", "farmer"):
        cats = query("SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id AND p.status='approved') n FROM categories c WHERE c.audience=? ORDER BY c.id", (role,))
    elif role == "seller":
        cats = []
    else:
        cats = query("SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id AND p.status='approved') n FROM categories c ORDER BY c.id")
    return render_template("index.html", cats=cats, account_type=role)


@bp.route("/about")
def about():
    stats = dict(products=query("SELECT COUNT(*) n FROM products WHERE status='approved'", one=True)["n"],
                 sellers=query("SELECT COUNT(*) n FROM sellers", one=True)["n"])
    return render_template("about.html", stats=stats)


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        if all(request.form.get(k, "").strip() for k in ("name", "email", "message")):
            flash("Thank you! Our support team will reach out within one business day.", "success")
            return redirect(url_for("main.contact"))
        flash("Please fill all required fields.", "error")
    return render_template("contact.html")


@bp.route("/farmers")
def farmers():
    rows = query("""SELECT s.*, u.name, (SELECT COUNT(*) FROM products p WHERE p.seller_id=s.id AND p.status='approved') n
                    FROM sellers s JOIN users u ON u.id=s.user_id ORDER BY n DESC""")
    return render_template("farmers.html", sellers=rows)


@bp.route("/deals")
def deals():
    return render_template("deals.html")


@bp.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@bp.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")


# ---------------------------------------------------------------- profile
@bp.route("/profile")
@login_required
def profile():
    u = current_user()
    return render_template("profile.html",
        addresses=query("SELECT * FROM addresses WHERE user_id=? ORDER BY is_default DESC, id DESC", (u["id"],)),
        orders=query("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (u["id"],)),
        payments=query("""SELECT p.*, o.order_number FROM payments p JOIN orders o ON o.id=p.order_id WHERE o.user_id=? ORDER BY p.created_at DESC""", (u["id"],)))


@bp.route("/update-profile", methods=["PUT"])
@login_required
def update_profile():
    d = request.get_json(silent=True) or {}
    name, phone = (d.get("name") or "").strip(), (d.get("phone") or "").strip()
    if not name or not phone:
        return jsonify(ok=False, error="Please fill all required fields."), 400
    if not re.fullmatch(r"(\+91[\s-]?)?[6-9]\d{9}", phone):
        return jsonify(ok=False, error="Enter a valid 10-digit Indian mobile number."), 400
    execute("UPDATE users SET name=?, phone=? WHERE id=?", (name[:80], phone, current_user()["id"]))
    return jsonify(ok=True, message="Profile updated.")


@bp.route("/profile/photo", methods=["POST"])
@login_required
def profile_photo():
    try:
        path = save_upload(request.files.get("photo"), "profiles")
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 400
    if not path:
        return jsonify(ok=False, error="Choose an image first."), 400
    execute("UPDATE users SET photo=? WHERE id=?", (path, current_user()["id"]))
    return jsonify(ok=True, message="Profile photo updated.")


@bp.route("/profile/address", methods=["POST"])
@login_required
def add_address():
    d = request.get_json(silent=True) or {}
    f = {k: (d.get(k) or "").strip() for k in ("line1", "village", "district", "state", "pincode")}
    if not all(f.values()) or not re.fullmatch(r"[1-9]\d{5}", f["pincode"]):
        return jsonify(ok=False, error="Please fill all required fields with a valid pincode."), 400
    execute("INSERT INTO addresses (user_id,line1,village,district,state,pincode) VALUES (?,?,?,?,?,?)",
            (current_user()["id"], f["line1"], f["village"], f["district"], f["state"], f["pincode"]))
    return jsonify(ok=True, message="Address saved.")


@bp.route("/profile/address/<int:aid>", methods=["DELETE"])
@login_required
def delete_address(aid):
    execute("DELETE FROM addresses WHERE id=? AND user_id=?", (aid, current_user()["id"]))
    return jsonify(ok=True, message="Address removed.")


@bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    d = request.get_json(silent=True) or {}
    u = current_user()
    if not check_password_hash(u["password"], d.get("current") or ""):
        return jsonify(ok=False, error="Current password is incorrect."), 400
    if len(d.get("new") or "") < 6:
        return jsonify(ok=False, error="New password must be at least 6 characters."), 400
    execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(d["new"]), u["id"]))
    return jsonify(ok=True, message="Password changed.")


# ---------------------------------------------------------------- seller dashboard
def _month_series(rows):
    """rows: iterable of (created_at, amount) -> last 6 months OrderedDict label -> [orders, revenue]."""
    from datetime import datetime
    now = datetime.now()
    keys = []
    y, m = now.year, now.month
    for _ in range(6):
        keys.append((y, m)); m -= 1
        if m == 0: y, m = y - 1, 12
    out = OrderedDict((k, [0, 0]) for k in reversed(keys))
    for created, amount in rows:
        d = datetime.fromisoformat(created)
        if (d.year, d.month) in out:
            out[(d.year, d.month)][0] += 1; out[(d.year, d.month)][1] += amount
    return [datetime(y, m, 1).strftime("%b") for y, m in out], [v[0] for v in out.values()], [round(v[1]) for v in out.values()]


@bp.route("/seller-dashboard")
@role_required("seller")
def seller_dashboard():
    u = current_user()
    seller = query("SELECT * FROM sellers WHERE user_id=?", (u["id"],), one=True)
    sid = seller["id"]
    products = query(BASE_SQL + " WHERE p.seller_id=? ORDER BY p.id DESC", (sid,))
    lines = query("""SELECT oi.*, o.order_number, o.id AS oid, o.status, o.created_at, o.customer_name, o.phone, o.user_id
                     FROM order_items oi JOIN orders o ON o.id=oi.order_id JOIN products p ON p.id=oi.product_id
                     WHERE p.seller_id=? ORDER BY o.created_at DESC""", (sid,))
    orders = OrderedDict()
    for l in lines:
        o = orders.setdefault(l["oid"], dict(id=l["oid"], number=l["order_number"], status=l["status"], created=l["created_at"],
                                             customer=l["customer_name"], phone=l["phone"], user_id=l["user_id"], items=[], total=0))
        o["items"].append(f"{l['name']} × {l['quantity']}"); o["total"] += l["price"] * l["quantity"]
    orders = list(orders.values())
    customers = OrderedDict()
    for o in orders:
        c = customers.setdefault(o["user_id"], dict(name=o["customer"], phone=o["phone"], orders=0, spent=0))
        c["orders"] += 1; c["spent"] += o["total"]
    months, m_orders, m_rev = _month_series([(o["created"], o["total"]) for o in orders])
    top = {}
    for l in lines:
        top[l["name"]] = top.get(l["name"], 0) + l["quantity"]
    top = sorted(top.items(), key=lambda x: -x[1])[:5]
    stats = dict(sales=sum(l["quantity"] for l in lines), orders=len(orders), products=len(products), revenue=sum(o["total"] for o in orders))
    return render_template("seller-dashboard.html", seller=seller, products=products, orders=orders, customers=list(customers.values()),
                           stats=stats, cats=query("SELECT * FROM categories"), chart=dict(months=months, orders=m_orders, revenue=m_rev,
                           top_names=[t[0] for t in top], top_qty=[t[1] for t in top]))


# ---------------------------------------------------------------- admin dashboard
@bp.route("/admin-dashboard")
@role_required("admin")
def admin_dashboard():
    count = lambda sql: query(sql, one=True)["n"]
    stats = dict(users=count("SELECT COUNT(*) n FROM users"), farmers=count("SELECT COUNT(*) n FROM sellers"),
                 products=count("SELECT COUNT(*) n FROM products"), orders=count("SELECT COUNT(*) n FROM orders"),
                 revenue=count("SELECT COALESCE(SUM(total_amount),0) n FROM orders"))
    orders = query("SELECT o.*, u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC")
    months, m_orders, m_rev = _month_series([(o["created_at"], o["total_amount"]) for o in orders])
    cat_rev = query("""SELECT c.name, COALESCE(SUM(oi.price*oi.quantity),0) r FROM categories c LEFT JOIN products p ON p.category_id=c.id
                       LEFT JOIN order_items oi ON oi.product_id=p.id GROUP BY c.id ORDER BY c.id""")
    return render_template("admin-dashboard.html", stats=stats, orders=orders,
        users=query("SELECT * FROM users ORDER BY id DESC"),
        sellers=query("""SELECT s.*, u.name, u.email, (SELECT COUNT(*) FROM products p WHERE p.seller_id=s.id) n FROM sellers s JOIN users u ON u.id=s.user_id"""),
        products=query(BASE_SQL + " ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END, p.id DESC"),
        cats=query("""SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id) n FROM categories c"""),
        all_sellers=query("SELECT id, business_name FROM sellers"),
        chart=dict(months=months, revenue=m_rev, orders=m_orders, cat_names=[r["name"] for r in cat_rev], cat_rev=[round(r["r"]) for r in cat_rev]))


@bp.route("/admin/category", methods=["POST"])
@role_required("admin")
def add_category():
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="Please fill all required fields."), 400
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if query("SELECT 1 FROM categories WHERE slug=? OR name=?", (slug, name), one=True):
        return jsonify(ok=False, error="Category already exists."), 409
    execute("INSERT INTO categories (name,slug,image,description) VALUES (?,?,?,?)", (name, slug, "categories/seeds.jpg", f"{name} for modern farming."))
    return jsonify(ok=True, message="Category added.")


@bp.route("/admin/user/<int:uid>", methods=["DELETE"])
@role_required("admin")
def delete_user(uid):
    if uid == current_user()["id"]:
        return jsonify(ok=False, error="You cannot delete your own account."), 400
    if query("SELECT 1 FROM orders WHERE user_id=?", (uid,), one=True):
        return jsonify(ok=False, error="This user has orders and cannot be deleted."), 409
    execute("DELETE FROM users WHERE id=?", (uid,))
    return jsonify(ok=True, message="User deleted.")


@bp.route("/placeholder/<label>.svg")
def placeholder(label):
    """Dark, labelled stand-in shown until the real product photo has been downloaded."""
    from html import escape
    from flask import Response
    text = escape(re.sub(r"[^A-Za-z0-9 ]", "", label).title()[:40])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#0B120D"/><stop offset="1" stop-color="#143a1e"/></linearGradient></defs>'
           '<rect width="800" height="600" fill="url(#g)"/>'
           '<path d="M400 190c-60 20-90 70-80 130 50-5 90-40 100-95 6 40-4 80-20 110 40-20 70-60 70-110 0-20-20-30-70-35z" fill="#39D353" opacity=".85"/>'
           f'<text x="400" y="420" font-family="Inter,Arial,sans-serif" font-size="38" font-weight="700" fill="#fff" text-anchor="middle">{text}</text>'
           '<text x="400" y="465" font-family="Inter,Arial,sans-serif" font-size="20" fill="#A7B3AA" text-anchor="middle">Photo loads after: python download_images.py</text></svg>')
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "no-cache"})
