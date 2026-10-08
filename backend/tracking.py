"""Order location tracking (map). Additive: reads existing orders/sellers tables, no schema changes.

The position of the parcel is *estimated from the order status* along a route
origin -> regional hub -> regional hub -> destination. For real GPS plug a courier API into
`build_tracking()` and return its coordinates instead."""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, abort
from backend import query, current_user, login_required, ORDER_STATUSES
from backend.geo import locate, km, nearest_hub, CITIES

bp = Blueprint("tracking", __name__)

# how far along the route each status is (0..1)
PROGRESS = {"Order Placed": 0.0, "Confirmed": 0.0, "Packed": 0.0, "Shipped": 0.4, "Out for Delivery": 0.93, "Delivered": 1.0}
DEFAULT_ORIGIN = ("Hyderabad", "Telangana")


def _parse_destination(address):
    """'line, village, district, state - 508001'  ->  (district, state, pincode)"""
    main, _, pin = (address or "").partition(" - ")
    parts = [p.strip() for p in main.split(",") if p.strip()]
    district = parts[-2] if len(parts) >= 2 else ""
    state = parts[-1] if parts else ""
    village = parts[-3] if len(parts) >= 3 else ""
    return district, state, pin.strip(), village


def _seller_origin(order_id):
    row = query("""SELECT s.business_name, s.location FROM order_items oi
                   JOIN products p ON p.id=oi.product_id JOIN sellers s ON s.id=p.seller_id
                   WHERE oi.order_id=? LIMIT 1""", (order_id,), one=True)
    if not row:
        return "AgroConnect Warehouse", DEFAULT_ORIGIN
    loc = [x.strip() for x in (row["location"] or "").split(",")]
    return row["business_name"], (loc[0], loc[1] if len(loc) > 1 else "")


def _along(points, frac):
    """Point at `frac` of the total length of the polyline."""
    segs = [km(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(segs) or 1
    target, run = frac * total, 0
    for i, s in enumerate(segs):
        if run + s >= target or i == len(segs) - 1:
            t = (target - run) / s if s else 0
            a, b = points[i], points[i + 1]
            return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
        run += s
    return list(points[-1])


def build_tracking(order):
    seller, (o_city, o_state) = _seller_origin(order["id"])
    d_district, d_state, pin, d_village = _parse_destination(order["shipping_address"])
    o = locate(o_city, o_state) or (*CITIES["hyderabad"], "Hyderabad")
    exact = locate(d_district, d_village)
    d = exact or locate(d_state)
    approximate = exact is None            # only the state centre was known
    if d is None:
        d = (*CITIES["hyderabad"], "Hyderabad")
    origin = dict(name=f"{seller} – {o[2]}", lat=o[0], lng=o[1])
    dest = dict(name=f"{d_district or d[2]}, {d_state}".strip(", "), lat=d[0], lng=d[1], pincode=pin)

    ho, hd = nearest_hub((o[0], o[1])), nearest_hub((d[0], d[1]))
    stops = [("Seller warehouse", origin["name"], [o[0], o[1]])]
    for h in dict.fromkeys([ho, hd]):                       # unique, keeps order
        c = CITIES[h.lower()]
        if all(km(c, s[2]) > 40 for s in stops) and km(c, (d[0], d[1])) > 40:
            stops.append(("Transit hub", f"AgroConnect Hub – {h}", [c[0], c[1]]))
    stops.append(("Delivery address", dest["name"], [d[0], d[1]]))
    pts = [s[2] for s in stops]
    dist = round(sum(km(pts[i], pts[i + 1]) for i in range(len(pts) - 1)))

    status = order["status"] if order["status"] in PROGRESS else "Order Placed"
    frac = PROGRESS[status]
    pos = _along(pts, frac)
    try:
        created = datetime.fromisoformat(order["created_at"])
    except Exception:
        created = datetime.utcnow()
    eta = created + timedelta(days=2 + round(dist / 350))
    idx = ORDER_STATUSES.index(status)
    hub_name = stops[1][1] if len(stops) > 2 else stops[0][1]
    where = [stops[0][1]] * 3 + [hub_name, stops[-1][1], stops[-1][1]]
    stages = [dict(status=s, done=i <= idx, current=i == idx, place=where[i]) for i, s in enumerate(ORDER_STATUSES)]
    return dict(ok=True, order_number=order["order_number"], status=status, delivered=status == "Delivered",
                origin=origin, destination=dest, stops=[dict(kind=k, name=n, lat=p[0], lng=p[1]) for k, n, p in stops],
                current=dict(lat=pos[0], lng=pos[1]), progress=frac, distance_km=dist,
                eta=eta.strftime("%d %b %Y"), stages=stages, approximate=approximate,
                note="Position is estimated from the order status. Live GPS needs a courier integration.")


@bp.route("/api/order/<int:oid>/tracking")
@login_required
def order_tracking(oid):
    user = current_user()
    o = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    if not o:
        abort(404)
    allowed = o["user_id"] == user["id"] or user["role"] == "admin"
    if not allowed and user["role"] == "seller":
        allowed = bool(query("""SELECT 1 FROM order_items oi JOIN products p ON p.id=oi.product_id JOIN sellers s ON s.id=p.seller_id
                                WHERE oi.order_id=? AND s.user_id=?""", (oid, user["id"]), one=True))
    if not allowed:
        abort(404)
    return jsonify(build_tracking(o))
