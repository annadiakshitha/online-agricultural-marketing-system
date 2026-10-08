"""Farmer interface: a first-class farmer account with a farm profile."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from backend import query, execute, current_user, account_required
from backend.geo import locate
from backend.assistant import _find_products, _card
from backend.cropdoctor import CROPS as CROP_NAMES

bp = Blueprint("farmer", __name__)
CROP_KEY = {"Rice (Paddy)": "rice", "Rice": "rice", "Maize": "maize", "Cotton": "cotton", "Tomato": "tomato", "Chilli": "chilli",
            "Potato": "potato", "Okra (Bhendi)": "okra", "Okra": "okra", "Groundnut": "groundnut"}
CHOICES = [c for c in CROP_NAMES if c != "Other"]


@bp.route("/farmer-dashboard")
@account_required("farmer")
def dashboard():
    u = current_user()
    fp = query("SELECT * FROM farmer_profiles WHERE user_id=?", (u["id"],), one=True)
    if not fp:
        return render_template("farmer-dashboard.html", fp=None, choices=CHOICES, crops=[])
    crops = [c for c in (fp["crops"] or "").split(",") if c]
    hit = locate(fp["district"], fp["village"], fp["state"]) or (17.385, 78.487, "Hyderabad")
    picks, seen = [], set()
    for c in crops[:3]:
        for p in _find_products(c.split(" (")[0] + " seeds", 2):
            if p["id"] not in seen:
                seen.add(p["id"]); picks.append(_card(p))
    stats = dict(
        orders=query("SELECT COUNT(*) c FROM orders WHERE user_id=?", (u["id"],), one=True)["c"],
        spent=query("SELECT COALESCE(SUM(total_amount),0) s FROM orders WHERE user_id=?", (u["id"],), one=True)["s"],
        rentals=query("SELECT COUNT(*) c FROM rental_bookings WHERE user_id=? AND status IN ('Requested','Confirmed')", (u["id"],), one=True)["c"])
    return render_template("farmer-dashboard.html", fp=fp, crops=crops, choices=CHOICES, crop_key=CROP_KEY, stats=stats, picks=picks,
                           lat=hit[0], lng=hit[1],
                           orders=query("SELECT id, order_number, status, total_amount FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 3", (u["id"],)),
                           bookings=query("""SELECT b.start_date, b.end_date, b.status, r.name FROM rental_bookings b JOIN rental_items r ON r.id=b.item_id
                                             WHERE b.user_id=? ORDER BY b.created_at DESC LIMIT 3""", (u["id"],)))


@bp.route("/farmer/profile", methods=["POST"])
@account_required("farmer")
def save_profile():
    f, u = request.form, current_user()
    try:
        acres = float(f.get("farm_acres") or 1)
        if not (0 < acres <= 5000):
            raise ValueError
    except ValueError:
        flash("Enter a farm size between 0 and 5000 acres.", "error")
        return redirect(url_for("farmer.dashboard"))
    crops = ",".join(c for c in f.getlist("crops") if c in CHOICES)
    vals = (f.get("village", "").strip()[:60], f.get("district", "").strip()[:60], f.get("state", "").strip()[:60], acres, crops, f.get("irrigation", "")[:30])
    if query("SELECT 1 FROM farmer_profiles WHERE user_id=?", (u["id"],), one=True):
        execute("UPDATE farmer_profiles SET village=?, district=?, state=?, farm_acres=?, crops=?, irrigation=? WHERE user_id=?", (*vals, u["id"]))
    else:
        execute("INSERT INTO farmer_profiles (village,district,state,farm_acres,crops,irrigation,user_id) VALUES (?,?,?,?,?,?,?)", vals + (u["id"],))
    flash("Farm profile saved.", "success")
    return redirect(url_for("farmer.dashboard"))
