"""Coupons: validation API, checkout hooks used by orders.place_order, and an admin page."""
from datetime import date
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from backend import query, execute, current_user, login_required, role_required, calc_totals, sale_price

bp = Blueprint("coupons", __name__)


def evaluate(code, net, user_id):
    """-> (coupon_row, discount_amount, error). `net` = cart value after product discounts, before delivery/GST."""
    code = (code or "").strip().upper()
    if not code:
        return None, 0, None
    c = query("SELECT * FROM coupons WHERE code=?", (code,), one=True)
    if not c or not c["active"]:
        return None, 0, "That coupon code is not valid."
    if c["expires"] and c["expires"] < date.today().isoformat():
        return None, 0, "This coupon has expired."
    if c["usage_limit"] is not None and c["used_count"] >= c["usage_limit"]:
        return None, 0, "This coupon has been fully redeemed."
    if net < (c["min_order"] or 0):
        return None, 0, f"Add items worth ₹{round(c['min_order'] - net)} more to use {code} (minimum ₹{round(c['min_order'])})."
    if query("SELECT 1 FROM coupon_redemptions WHERE coupon_id=? AND user_id=?", (c["id"], user_id), one=True):
        return None, 0, "You have already used this coupon."
    amt = net * c["value"] / 100 if c["kind"] == "percent" else c["value"]
    if c["max_discount"]:
        amt = min(amt, c["max_discount"])
    return c, round(min(amt, net)), None


def _net_for(items):
    lines = []
    for it in (items or [])[:50]:
        try:
            pid, qty = int(it["id"]), max(1, int(it["qty"]))
        except (KeyError, TypeError, ValueError):
            continue
        p = query("SELECT price, discount FROM products WHERE id=? AND status='approved'", (pid,), one=True)
        if p:
            lines.append((p["price"], p["discount"], qty))
    return lines


def apply_to_order(code, totals, user_id):
    """Used by place_order. Returns (info|None, error|None); mutates totals['total']."""
    if not (code or "").strip():
        return None, None
    net = totals["subtotal"] - totals["discount"]
    c, amt, err = evaluate(code, net, user_id)
    if err:
        return None, err
    totals["total"] -= amt
    return dict(id=c["id"], code=c["code"], amount=amt), None


def record(db, order_id, user_id, info):
    if not info:
        return
    db.execute("INSERT OR REPLACE INTO order_extras (order_id, coupon_code, coupon_discount) VALUES (?,?,?)", (order_id, info["code"], info["amount"]))
    db.execute("INSERT OR IGNORE INTO coupon_redemptions (coupon_id,user_id,order_id) VALUES (?,?,?)", (info["id"], user_id, order_id))
    db.execute("UPDATE coupons SET used_count = used_count + 1 WHERE id=?", (info["id"],))


@bp.route("/api/coupon/validate", methods=["POST"])
@login_required
def validate():
    data = request.get_json(silent=True) or {}
    lines = _net_for(data.get("items"))
    if not lines:
        return jsonify(ok=False, error="Your cart is empty."), 400
    t = calc_totals(lines)
    c, amt, err = evaluate(data.get("code"), t["subtotal"] - t["discount"], current_user()["id"])
    if err or not c:
        return jsonify(ok=False, error=err or "Enter a coupon code."), 400
    return jsonify(ok=True, code=c["code"], discount=amt, total=t["total"] - amt, description=c["description"])


@bp.route("/api/coupons/available")
def available():
    rows = query("SELECT code, description, min_order FROM coupons WHERE active=1 AND (expires IS NULL OR expires >= date('now')) ORDER BY id")
    return jsonify([dict(code=r["code"], description=r["description"]) for r in rows])


# ---------------------------------------------------------------- admin
@bp.route("/admin/coupons", methods=["GET", "POST"])
@role_required("admin")
def admin_coupons():
    if request.method == "POST":
        f = request.form
        code = (f.get("code") or "").strip().upper()
        try:
            kind, val = f.get("kind"), float(f.get("value") or 0)
            if not code.isalnum() or len(code) > 20 or kind not in ("percent", "flat") or val <= 0 or (kind == "percent" and val > 90):
                raise ValueError
            execute("INSERT INTO coupons (code,kind,value,min_order,max_discount,expires,usage_limit,description) VALUES (?,?,?,?,?,?,?,?)",
                    (code, kind, val, float(f.get("min_order") or 0), float(f["max_discount"]) if f.get("max_discount") else None,
                     f.get("expires") or None, int(f["usage_limit"]) if f.get("usage_limit") else None, (f.get("description") or "")[:120]))
            flash(f"Coupon {code} created.", "success")
        except Exception:
            flash("Could not create coupon. Use a unique letters/numbers code and valid numbers (percent max 90).", "error")
        return redirect(url_for("coupons.admin_coupons"))
    return render_template("admin-coupons.html", coupons=query("SELECT * FROM coupons ORDER BY id DESC"))


@bp.route("/admin/coupons/<int:cid>/toggle", methods=["POST"])
@role_required("admin")
def toggle(cid):
    execute("UPDATE coupons SET active = 1 - active WHERE id=?", (cid,))
    return redirect(url_for("coupons.admin_coupons"))
