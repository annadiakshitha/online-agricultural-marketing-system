"""Cart + wishlist endpoints. The browser keeps the cart in localStorage; these routes validate
stock, return fresh prices and (for logged-in users) mirror the data in SQLite."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from . import query, execute, current_user, calc_totals
from .products import BASE_SQL, product_dict

bp = Blueprint("cart", __name__)


@bp.route("/cart")
def cart():
    return render_template("cart.html")


@bp.route("/checkout")
def checkout():
    user = current_user()
    if not user:
        flash("Please log in to continue to checkout.", "error")
        return redirect(url_for("auth.login", next="/checkout"))
    addr = query("SELECT * FROM addresses WHERE user_id=? ORDER BY is_default DESC LIMIT 1", (user["id"],), one=True)
    return render_template("checkout.html", addr=addr)


@bp.route("/api/cart-items")
def cart_items():
    ids = [int(i) for i in request.args.get("ids", "").split(",") if i.isdigit()][:50]
    if not ids:
        return jsonify([])
    rows = query(BASE_SQL + f" WHERE p.status='approved' AND p.id IN ({','.join('?' * len(ids))})", ids)
    return jsonify([product_dict(r) for r in rows])


@bp.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True) or {}
    try:
        pid, qty = int(data.get("product_id")), max(1, int(data.get("quantity", 1)))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Invalid product."), 400
    r = query(BASE_SQL + " WHERE p.id=? AND p.status='approved'", (pid,), one=True)
    if not r:
        return jsonify(ok=False, error="Product not found."), 404
    if r["stock"] <= 0:
        return jsonify(ok=False, error="Product is out of stock."), 409
    user = current_user()
    if user:
        execute("""INSERT INTO cart (user_id,product_id,quantity) VALUES (?,?,?)
                   ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=MIN(quantity+excluded.quantity, ?)""",
                (user["id"], pid, min(qty, r["stock"]), r["stock"]))
    return jsonify(ok=True, product=product_dict(r), max=r["stock"])


@bp.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    pid = (request.get_json(silent=True) or {}).get("product_id")
    user = current_user()
    if user and pid:
        execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user["id"], pid))
    return jsonify(ok=True)


@bp.route("/add-wishlist", methods=["POST"])
def add_wishlist():
    pid = (request.get_json(silent=True) or {}).get("product_id")
    if not query("SELECT 1 FROM products WHERE id=?", (pid,), one=True):
        return jsonify(ok=False, error="Product not found."), 404
    user = current_user()
    if user:
        execute("INSERT OR IGNORE INTO wishlist (user_id,product_id) VALUES (?,?)", (user["id"], pid))
    return jsonify(ok=True)


@bp.route("/remove-wishlist", methods=["POST"])
def remove_wishlist():
    pid = (request.get_json(silent=True) or {}).get("product_id")
    user = current_user()
    if user and pid:
        execute("DELETE FROM wishlist WHERE user_id=? AND product_id=?", (user["id"], pid))
    return jsonify(ok=True)


@bp.route("/api/wishlist")
def api_wishlist():
    user = current_user()
    ids = [r["product_id"] for r in query("SELECT product_id FROM wishlist WHERE user_id=?", (user["id"],))] if user else []
    return jsonify(ids)
