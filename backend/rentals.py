"""Equipment rental: browse, check availability, book, manage (seller/admin)."""
import re
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash
from backend import query, execute, current_user, account_required, role_required

bp = Blueprint("rentals", __name__)
KINDS = ["Tractor", "Tiller", "Weeder", "Cutter", "Pump", "Sprayer"]
DEFAULT_IMAGE = {"Tractor": "products/tractor.jpg", "Tiller": "products/power-tiller.jpg", "Weeder": "products/power-weeder.jpg",
                 "Cutter": "products/brush-cutter.jpg", "Pump": "products/water-pump.jpg", "Sprayer": "products/battery-sprayer.jpg"}
MAX_DAYS = 14
BLOCKING = ("Requested", "Confirmed")


def _parse(s):
    try:
        return datetime.strptime(s or "", "%Y-%m-%d").date()
    except ValueError:
        return None


def free_units(item, start, end):
    """Units still free on every day of [start, end] (inclusive)."""
    rows = query("""SELECT start_date, end_date FROM rental_bookings WHERE item_id=? AND status IN ('Requested','Confirmed')
                    AND start_date <= ? AND end_date >= ?""", (item["id"], end.isoformat(), start.isoformat()))
    worst, d = 0, start
    while d <= end:
        iso = d.isoformat()
        worst = max(worst, sum(1 for r in rows if r["start_date"] <= iso <= r["end_date"]))
        d += timedelta(days=1)
    return item["units"] - worst


def _item(iid):
    it = query("""SELECT r.*, s.business_name, s.user_id AS owner_id FROM rental_items r JOIN sellers s ON s.id=r.seller_id WHERE r.id=?""", (iid,), one=True)
    if not it:
        abort(404)
    return it


def _check_dates(s, e):
    if not s or not e:
        return "Choose a start and end date."
    if s < date.today():
        return "Start date cannot be in the past."
    if e < s:
        return "End date must be on or after the start date."
    if (e - s).days + 1 > MAX_DAYS:
        return f"You can rent for up to {MAX_DAYS} days at a time."
    return None


# ---------------------------------------------------------------- pages
@bp.route("/rentals")
@account_required("farmer")
def rentals():
    kind, q = request.args.get("kind", ""), request.args.get("q", "").strip()
    sql, args = "SELECT r.*, s.business_name FROM rental_items r JOIN sellers s ON s.id=r.seller_id WHERE r.active=1", []
    if kind in KINDS:
        sql += " AND r.kind=?"; args.append(kind)
    if q:
        sql += " AND (r.name LIKE ? OR r.district LIKE ? OR r.state LIKE ?)"; args += [f"%{q}%"] * 3
    return render_template("rentals.html", items=query(sql + " ORDER BY r.price_per_day DESC", args), kinds=KINDS, kind=kind, q=q)


@bp.route("/rental/<int:iid>")
@account_required("farmer")
def rental_details(iid):
    it = _item(iid)
    if not it["active"]:
        abort(404)
    return render_template("rental-details.html", it=it, today=date.today().isoformat(), max_days=MAX_DAYS)


@bp.route("/my-rentals")
@account_required("farmer")
def my_rentals():
    rows = query("""SELECT b.*, r.name, r.image, r.district, r.state, s.business_name FROM rental_bookings b JOIN rental_items r ON r.id=b.item_id
                    JOIN sellers s ON s.id=r.seller_id WHERE b.user_id=? ORDER BY b.created_at DESC""", (current_user()["id"],))
    return render_template("my-rentals.html", rows=rows, today=date.today().isoformat())


@bp.route("/seller-rentals")
@role_required("seller", "admin")
def seller_rentals():
    u = current_user()
    where, args = ("", ()) if u["role"] == "admin" else ("WHERE s.user_id=?", (u["id"],))
    items = query(f"SELECT r.*, s.business_name FROM rental_items r JOIN sellers s ON s.id=r.seller_id {where} ORDER BY r.id DESC", args)
    bookings = query(f"""SELECT b.*, r.name AS item_name, u.name AS user_name FROM rental_bookings b JOIN rental_items r ON r.id=b.item_id
                         JOIN sellers s ON s.id=r.seller_id JOIN users u ON u.id=b.user_id {where} ORDER BY b.created_at DESC""", args)
    return render_template("seller-rentals.html", items=items, bookings=bookings, kinds=KINDS)


# ---------------------------------------------------------------- API
@bp.route("/api/rental/<int:iid>/availability")
def availability(iid):
    it = _item(iid)
    s, e = _parse(request.args.get("start")), _parse(request.args.get("end"))
    err = _check_dates(s, e)
    if err:
        return jsonify(ok=False, error=err), 400
    days = (e - s).days + 1
    free = free_units(it, s, e)
    return jsonify(ok=True, available=free > 0, free=max(free, 0), days=days, rent=it["price_per_day"] * days,
                   deposit=it["deposit"], total=it["price_per_day"] * days + it["deposit"])


@bp.route("/api/rental/<int:iid>/book", methods=["POST"])
@account_required("farmer")
def book(iid):
    it = _item(iid)
    d = request.get_json(silent=True) or {}
    s, e = _parse(d.get("start")), _parse(d.get("end"))
    err = _check_dates(s, e)
    name, phone, addr = (d.get("name") or "").strip()[:80], (d.get("phone") or "").strip(), (d.get("address") or "").strip()[:250]
    if not err and (not name or not addr):
        err = "Please fill your name and the address where the equipment is needed."
    if not err and not re.fullmatch(r"(\+91[\s-]?)?[6-9]\d{9}", phone):
        err = "Enter a valid 10-digit Indian mobile number."
    if not err and not it["active"]:
        err = "This equipment is not available for rent."
    if not err and free_units(it, s, e) <= 0:
        err = "Sorry, this equipment is already booked for some of those dates. Try different dates."
    if err:
        return jsonify(ok=False, error=err), 400
    days = (e - s).days + 1
    rent = it["price_per_day"] * days
    bid = execute("""INSERT INTO rental_bookings (item_id,user_id,start_date,end_date,days,rent,deposit,total,customer_name,phone,address,note)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (iid, current_user()["id"], s.isoformat(), e.isoformat(), days, rent, it["deposit"],
                                                            rent + it["deposit"], name, phone, addr, (d.get("note") or "")[:200]))
    return jsonify(ok=True, id=bid, message="Booking request sent. The owner will confirm shortly.", redirect=url_for("rentals.my_rentals"))


@bp.route("/api/rental/booking/<int:bid>/cancel", methods=["POST"])
@account_required("farmer")
def cancel(bid):
    b = query("SELECT * FROM rental_bookings WHERE id=? AND user_id=?", (bid, current_user()["id"]), one=True)
    if not b:
        abort(404)
    if b["status"] not in BLOCKING or b["start_date"] <= date.today().isoformat():
        return jsonify(ok=False, error="Only upcoming bookings can be cancelled."), 400
    execute("UPDATE rental_bookings SET status='Cancelled' WHERE id=?", (bid,))
    return jsonify(ok=True)


@bp.route("/api/rental/booking/<int:bid>/status", methods=["POST"])
@role_required("seller", "admin")
def set_status(bid):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("Confirmed", "Rejected", "Completed"):
        return jsonify(ok=False, error="Invalid status."), 400
    u = current_user()
    b = query("""SELECT b.*, s.user_id AS owner_id FROM rental_bookings b JOIN rental_items r ON r.id=b.item_id JOIN sellers s ON s.id=r.seller_id WHERE b.id=?""", (bid,), one=True)
    if not b or (u["role"] != "admin" and b["owner_id"] != u["id"]):
        abort(404)
    execute("UPDATE rental_bookings SET status=? WHERE id=?", (status, bid))
    return jsonify(ok=True, status=status)


@bp.route("/rental-items", methods=["POST"])
@role_required("seller", "admin")
def add_item():
    f, u = request.form, current_user()
    seller = query("SELECT id FROM sellers WHERE user_id=?", (u["id"],), one=True) or (query("SELECT id FROM sellers ORDER BY id LIMIT 1", one=True) if u["role"] == "admin" else None)
    try:
        name, kind = f["name"].strip()[:80], f["kind"]
        price, dep, units = float(f["price_per_day"]), float(f.get("deposit") or 0), int(f.get("units") or 1)
        if not name or kind not in KINDS or price <= 0 or dep < 0 or not (1 <= units <= 50) or not seller:
            raise ValueError
        execute("INSERT INTO rental_items (seller_id,name,kind,description,image,price_per_day,deposit,units,district,state) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (seller["id"], name, kind, f.get("description", "")[:400], DEFAULT_IMAGE[kind], price, dep, units, f.get("district", "")[:60], f.get("state", "")[:60]))
        flash("Equipment listed for rent.", "success")
    except (KeyError, ValueError):
        flash("Please fill the equipment details correctly.", "error")
    return redirect(url_for("rentals.seller_rentals"))


@bp.route("/rental-items/<int:iid>/toggle", methods=["POST"])
@role_required("seller", "admin")
def toggle_item(iid):
    it, u = _item(iid), current_user()
    if u["role"] != "admin" and it["owner_id"] != u["id"]:
        abort(404)
    execute("UPDATE rental_items SET active = 1 - active WHERE id=?", (iid,))
    return redirect(url_for("rentals.seller_rentals"))
