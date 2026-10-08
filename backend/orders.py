"""Order placement, history, tracking and status updates."""
import re
from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash
from . import query, execute, get_db, current_user, login_required, role_required, calc_totals, sale_price, ORDER_STATUSES
from .payments import process_payment

from backend.coupons import apply_to_order, record as record_coupon
bp = Blueprint("orders", __name__)


@bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    data = request.get_json(silent=True) or {}
    cust, addr, pay = data.get("customer") or {}, data.get("address") or {}, data.get("payment") or {}
    items = data.get("items") or []
    # --- validation
    if not items:
        return jsonify(ok=False, error="Your cart is empty."), 400
    if not (cust.get("name") or "").strip() or not (cust.get("email") or "").strip():
        return jsonify(ok=False, error="Please fill all required fields."), 400
    if not re.fullmatch(r"(\+91[\s-]?)?[6-9]\d{9}", (cust.get("phone") or "").strip()):
        return jsonify(ok=False, error="Enter a valid 10-digit Indian mobile number."), 400
    if not all((addr.get(k) or "").strip() for k in ("line1", "village", "district", "state")):
        return jsonify(ok=False, error="Please fill all required fields."), 400
    if not re.fullmatch(r"[1-9]\d{5}", (addr.get("pincode") or "").strip()):
        return jsonify(ok=False, error="Enter a valid 6-digit pincode."), 400

    # --- re-price everything on the server (never trust browser prices)
    lines, resolved = [], []
    for it in items[:50]:
        try:
            pid, qty = int(it["id"]), max(1, int(it["qty"]))
        except (KeyError, TypeError, ValueError):
            return jsonify(ok=False, error="Invalid cart data."), 400
        p = query("SELECT * FROM products WHERE id=? AND status='approved'", (pid,), one=True)
        if not p:
            return jsonify(ok=False, error="A product in your cart is no longer available."), 400
        if p["stock"] < qty:
            return jsonify(ok=False, error=f"{p['name']}: only {p['stock']} left. Product is out of stock." if p["stock"] == 0
                           else f"{p['name']}: only {p['stock']} left in stock."), 409
        lines.append((p["price"], p["discount"], qty)); resolved.append((p, qty))
    totals = calc_totals(lines)
    coupon, coupon_err = apply_to_order(data.get("coupon"), totals, current_user()["id"])   # optional coupon
    if coupon_err:
        return jsonify(ok=False, error=coupon_err), 400

    ok, err, pay_status, ref = process_payment(pay.get("method"), pay, totals["total"])
    if not ok:
        return jsonify(ok=False, error=err), 400

    address = ", ".join(addr[k].strip() for k in ("line1", "village", "district", "state")) + " - " + addr["pincode"].strip()
    user = current_user()
    db = get_db()
    cur = db.execute("""INSERT INTO orders (user_id,total_amount,status,payment_method,customer_name,phone,shipping_address)
                        VALUES (?,?,?,?,?,?,?)""",
                     (user["id"], totals["total"], "Order Placed", pay["method"], cust["name"].strip()[:80], cust["phone"].strip(), address))
    oid = cur.lastrowid
    number = f"AGC{__import__('datetime').datetime.now():%Y%m}{oid:05d}"
    db.execute("UPDATE orders SET order_number=? WHERE id=?", (number, oid))
    for p, qty in resolved:
        db.execute("INSERT INTO order_items (order_id,product_id,name,quantity,price) VALUES (?,?,?,?,?)",
                   (oid, p["id"], p["name"], qty, sale_price(p["price"], p["discount"])))
        db.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, p["id"]))
    record_coupon(db, oid, user["id"], coupon)
    db.execute("INSERT INTO payments (order_id,method,status,reference,amount) VALUES (?,?,?,?,?)", (oid, pay["method"], pay_status, ref, totals["total"]))
    db.execute("DELETE FROM cart WHERE user_id=?", (user["id"],))
    # remember the address for next time
    if not query("SELECT 1 FROM addresses WHERE user_id=? AND pincode=? AND line1=?", (user["id"], addr["pincode"], addr["line1"]), one=True):
        db.execute("INSERT INTO addresses (user_id,line1,village,district,state,pincode,is_default) VALUES (?,?,?,?,?,?,0)",
                   (user["id"], addr["line1"].strip(), addr["village"].strip(), addr["district"].strip(), addr["state"].strip(), addr["pincode"].strip()))
    db.commit()
    return jsonify(ok=True, order_number=number, redirect=url_for("orders.order_success", number=number))


@bp.route("/order-success/<number>")
@login_required
def order_success(number):
    o = _get_order(number=number)
    return render_template("order-success.html", o=o)


@bp.route("/orders")
@login_required
def orders():
    rows = query("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (current_user()["id"],))
    data = [dict(o=o, items=query("SELECT * FROM order_items WHERE order_id=?", (o["id"],))) for o in rows]
    return render_template("orders.html", data=data)


@bp.route("/order/<int:oid>")
@login_required
def order_details(oid):
    o = _get_order(oid=oid)
    items = query("""SELECT oi.*, p.image FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id WHERE order_id=?""", (o["id"],))
    pay = query("SELECT * FROM payments WHERE order_id=?", (o["id"],), one=True)
    sub = sum(i["price"] * i["quantity"] for i in items)
    return render_template("order-details.html", o=o, items=items, pay=pay, sub=sub)


def _get_order(oid=None, number=None):
    user = current_user()
    o = query("SELECT * FROM orders WHERE id=?", (oid,), one=True) if oid else query("SELECT * FROM orders WHERE order_number=?", (number,), one=True)
    if not o or (o["user_id"] != user["id"] and user["role"] != "admin"):
        abort(404)
    return o


@bp.route("/order/<int:oid>/status", methods=["POST"])
@role_required("seller", "admin")
def update_status(oid):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ORDER_STATUSES:
        return jsonify(ok=False, error="Invalid status."), 400
    user = current_user()
    if user["role"] == "seller":
        owns = query("""SELECT 1 FROM order_items oi JOIN products p ON p.id=oi.product_id JOIN sellers s ON s.id=p.seller_id
                        WHERE oi.order_id=? AND s.user_id=?""", (oid, user["id"]), one=True)
        if not owns:
            return jsonify(ok=False, error="This order does not contain your products."), 403
    execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    if status == "Delivered":
        execute("UPDATE payments SET status='Paid' WHERE order_id=? AND status LIKE 'Pending%'", (oid,))
    return jsonify(ok=True, message=f"Order marked as {status}.")
