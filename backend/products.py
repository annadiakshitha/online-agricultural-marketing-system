"""Product catalogue, search API, reviews and seller/admin product CRUD."""
import re
from flask import Blueprint, render_template, request, jsonify, abort, url_for, redirect
from . import query, execute, get_db, image_url, sale_price, login_required, role_required, current_user, account_type, save_upload

bp = Blueprint("products", __name__)

BASE_SQL = """SELECT p.*, c.name AS category, c.slug AS category_slug, s.business_name AS seller, s.location AS seller_location,
              s.verified AS seller_verified FROM products p JOIN categories c ON c.id=p.category_id
              JOIN sellers s ON s.id=p.seller_id"""


def product_dict(r):
    return dict(id=r["id"], name=r["name"], category=r["category"], category_slug=r["category_slug"], seller=r["seller"],
                seller_id=r["seller_id"], price=r["price"], discount=r["discount"] or 0, sale_price=sale_price(r["price"], r["discount"]),
                stock=r["stock"], image=image_url(r["image"]), rating=r["rating"] or 0, reviews=r["reviews_count"] or 0,
                brand=r["brand"] or "", tags=r["tags"] or "", organic=bool(r["organic"]), created=r["created_at"],
                description=(r["description"] or "")[:140])


def _catalog_filter(user=None):
    role = account_type(user)
    if role == "customer":
        return "c.audience='customer'", ()
    if role == "farmer":
        return "c.audience='farmer'", ()
    if role == "seller":
        sid = query("SELECT id FROM sellers WHERE user_id=?", ((user or current_user())["id"],), one=True)
        return ("p.seller_id=?", (sid["id"],)) if sid else ("1=0", ())
    return "1=1", ()


def _catalog_category_sql(role):
    if role == "customer":
        return "c.audience='customer'"
    if role == "farmer":
        return "c.audience='farmer'"
    return "1=1"


@bp.route("/api/products")
def api_products():
    role = account_type()
    where, args = _catalog_filter()
    rows = query(BASE_SQL + f" WHERE p.status='approved' AND {where} ORDER BY p.id", args)
    return jsonify([product_dict(r) for r in rows])


@bp.route("/products")
def shop():
    role = account_type()
    if role == "seller":
        return redirect(url_for("main.seller_dashboard"))
    where, args = _catalog_filter()
    cats = query(f"SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id AND p.status='approved' AND {where}) n FROM categories c WHERE {_catalog_category_sql(role)} ORDER BY c.id", args)
    seller_sql = "SELECT DISTINCT s.business_name FROM sellers s JOIN products p ON p.seller_id=s.id WHERE p.status='approved'"
    seller_args = ()
    if role == "seller":
        seller_sql += " AND p.seller_id=?"
        seller_args = args
    sellers = query(seller_sql + " ORDER BY 1", seller_args)
    brand_sql = "SELECT DISTINCT brand FROM products WHERE status='approved' AND brand<>''"
    if role == "customer":
        brand_sql += " AND category_id IN (SELECT id FROM categories WHERE audience='customer')"
    elif role == "farmer":
        brand_sql += " AND category_id IN (SELECT id FROM categories WHERE audience='farmer')"
    elif role == "seller":
        brand_sql += " AND seller_id=?"
        brands = query(brand_sql + " ORDER BY 1", args)
        return render_template("products.html", cats=cats, sellers=sellers, brands=brands, account_type=role)
    brands = query(brand_sql + " ORDER BY 1")
    return render_template("products.html", cats=cats, sellers=sellers, brands=brands, account_type=role)


@bp.route("/categories")
def categories():
    role = account_type()
    if role == "seller":
        return redirect(url_for("main.seller_dashboard"))
    where, args = _catalog_filter()
    cats = query(f"SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id AND p.status='approved' AND {where}) n FROM categories c WHERE {_catalog_category_sql(role)} ORDER BY c.id", args)
    return render_template("categories.html", cats=cats, account_type=role)


@bp.route("/product/<int:pid>")
def product_details(pid):
    r = query(BASE_SQL + " WHERE p.id=?", (pid,), one=True)
    if not r:
        abort(404)
    user = current_user()
    if r["status"] != "approved" and not (user and (user["role"] == "admin" or
            query("SELECT 1 FROM sellers WHERE id=? AND user_id=?", (r["seller_id"], user["id"]), one=True))):
        abort(404)
    role = account_type(user)
    if role in ("customer", "farmer") and (query("SELECT audience FROM categories WHERE id=?", (r["category_id"],), one=True)["audience"] != role):
        abort(404)
    if role == "seller" and not query("SELECT 1 FROM sellers WHERE id=? AND user_id=?", (r["seller_id"], user["id"]), one=True):
        abort(404)
    reviews = query("SELECT r.*, u.name FROM reviews r JOIN users u ON u.id=r.user_id WHERE product_id=? ORDER BY r.created_at DESC", (pid,))
    seller = query("SELECT * FROM sellers WHERE id=?", (r["seller_id"],), one=True)
    seller_count = query("SELECT COUNT(*) n FROM products WHERE seller_id=? AND status='approved'", (r["seller_id"],), one=True)["n"]
    specs = [s.split(":", 1) for s in (r["specs"] or "").split("|") if ":" in s]
    gallery = [image_url(r["image"])] + [image_url(x["image"]) for x in
               query("SELECT image FROM products WHERE category_id=? AND id<>? AND status='approved' LIMIT 3", (r["category_id"], pid))]
    dist = {i: sum(1 for x in reviews if x["rating"] == i) for i in range(5, 0, -1)}
    return render_template("product-details.html", p=r, pd=product_dict(r), reviews=reviews, seller=seller, seller_count=seller_count,
                           specs=specs, gallery=gallery, dist=dist)


@bp.route("/product/<int:pid>/review", methods=["POST"])
@login_required
def add_review(pid):
    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    title, body = (data.get("title") or "").strip()[:100], (data.get("body") or "").strip()[:1000]
    if not (1 <= rating <= 5) or not title or not body:
        return jsonify(ok=False, error="Please fill all required fields."), 400
    if not query("SELECT 1 FROM products WHERE id=?", (pid,), one=True):
        return jsonify(ok=False, error="Product not found."), 404
    execute("INSERT INTO reviews (product_id,user_id,rating,title,body) VALUES (?,?,?,?,?)",
            (pid, current_user()["id"], rating, title, body))
    p = query("SELECT rating, reviews_count FROM products WHERE id=?", (pid,), one=True)
    count = (p["reviews_count"] or 0) + 1
    new_rating = round(((p["rating"] or 0) * (count - 1) + rating) / count, 1)
    execute("UPDATE products SET rating=?, reviews_count=? WHERE id=?", (new_rating, count, pid))
    return jsonify(ok=True, name=current_user()["name"], rating=rating, title=title, body=body, avg=new_rating, count=count)


@bp.route("/api/check-delivery")
def check_delivery():
    pin = request.args.get("pincode", "").strip()
    if not re.fullmatch(r"[1-9]\d{5}", pin):
        return jsonify(ok=False, error="Enter a valid 6-digit pincode."), 400
    days = {"5": "2-3", "6": "3-4", "4": "3-5"}.get(pin[0], "4-6")
    return jsonify(ok=True, message="Delivery available", days=days)


# ---------------------------------------------------------------- seller / admin CRUD
def _owned_product(pid):
    user = current_user()
    p = query("SELECT * FROM products WHERE id=?", (pid,), one=True)
    if not p:
        return None, (jsonify(ok=False, error="Product not found."), 404)
    if user["role"] != "admin":
        s = query("SELECT id FROM sellers WHERE user_id=?", (user["id"],), one=True)
        if not s or s["id"] != p["seller_id"]:
            return None, (jsonify(ok=False, error="You can only manage your own products."), 403)
    return p, None


def _clean_product(src):
    try:
        data = dict(name=(src.get("name") or "").strip(), description=(src.get("description") or "").strip(),
                    category_id=int(src.get("category_id")), price=float(src.get("price")), discount=int(src.get("discount") or 0),
                    stock=int(src.get("stock") or 0), brand=(src.get("brand") or "").strip(),
                    specs=(src.get("specs") or "").strip(), tags=(src.get("tags") or "").strip(),
                    organic=1 if str(src.get("organic", "")).lower() in ("1", "true", "on") else 0)
    except (TypeError, ValueError):
        return None, "Please fill all required fields."
    if not data["name"] or not data["description"] or data["price"] <= 0 or not 0 <= data["discount"] <= 90 or data["stock"] < 0:
        return None, "Please check the product details (price > 0, discount 0-90, stock >= 0)."
    if not query("SELECT 1 FROM categories WHERE id=?", (data["category_id"],), one=True):
        return None, "Invalid category."
    return data, None


@bp.route("/add-product", methods=["POST"])
@role_required("seller", "admin")
def add_product():
    user = current_user()
    data, err = _clean_product(request.form)
    if err:
        return jsonify(ok=False, error=err), 400
    if user["role"] == "admin":
        seller_id = request.form.get("seller_id", type=int)
        if not query("SELECT 1 FROM sellers WHERE id=?", (seller_id,), one=True):
            return jsonify(ok=False, error="Choose a seller for this product."), 400
        status = "approved"
    else:
        seller_id = query("SELECT id FROM sellers WHERE user_id=?", (user["id"],), one=True)["id"]
        status = "pending"
    try:
        image = save_upload(request.files.get("image"), "products")
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 400
    pid = execute("""INSERT INTO products (name,description,category_id,seller_id,price,discount,stock,image,brand,tags,organic,specs,status)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (data["name"], data["description"], data["category_id"], seller_id, data["price"], data["discount"], data["stock"],
                   image or "", data["brand"], data["tags"], data["organic"], data["specs"], status))
    msg = "Product added." if status == "approved" else "Product submitted. It will appear in the shop once an admin approves it."
    return jsonify(ok=True, id=pid, message=msg)


@bp.route("/update-product/<int:pid>", methods=["PUT"])
@role_required("seller", "admin")
def update_product(pid):
    p, err = _owned_product(pid)
    if err:
        return err
    data, e = _clean_product(request.get_json(silent=True) or {})
    if e:
        return jsonify(ok=False, error=e), 400
    status = p["status"] if current_user()["role"] == "admin" else "pending" if p["status"] == "rejected" else p["status"]
    execute("""UPDATE products SET name=?,description=?,category_id=?,price=?,discount=?,stock=?,brand=?,specs=?,tags=?,organic=?,status=? WHERE id=?""",
            (data["name"], data["description"], data["category_id"], data["price"], data["discount"], data["stock"],
             data["brand"], data["specs"], data["tags"], data["organic"], status, pid))
    return jsonify(ok=True, message="Product updated.")


@bp.route("/delete-product/<int:pid>", methods=["DELETE"])
@role_required("seller", "admin")
def delete_product(pid):
    p, err = _owned_product(pid)
    if err:
        return err
    execute("DELETE FROM products WHERE id=?", (pid,))
    return jsonify(ok=True, message="Product deleted.")


@bp.route("/admin/product/<int:pid>/status", methods=["POST"])
@role_required("admin")
def set_product_status(pid):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("approved", "rejected", "pending"):
        return jsonify(ok=False, error="Invalid status."), 400
    execute("UPDATE products SET status=? WHERE id=?", (status, pid))
    return jsonify(ok=True, message=f"Product {status}.")
