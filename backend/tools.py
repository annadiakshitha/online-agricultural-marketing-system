"""Farmer tools hub, weather page and fertilizer calculator."""
from flask import Blueprint, render_template, request, jsonify
from backend import query, current_user, account_required
from backend.geo import locate
from backend.assistant import _find_products, _card

bp = Blueprint("tools", __name__)

# General guideline in kg of N / P2O5 / K2O per ACRE (typical ICAR-style recommendations; always adjust to a soil test).
CROPS = {
    "rice":      dict(name="Rice (Paddy)", n=48, p=24, k=16, splits=[("Basal (at transplanting)", .33), ("Tillering (about 25 days)", .33), ("Panicle initiation (about 45 days)", .34)], note="Apply all P and K as basal."),
    "maize":     dict(name="Maize", n=60, p=30, k=20, splits=[("Basal", .25), ("Knee-high (about 25 days)", .5), ("Tasselling (about 45 days)", .25)], note="Apply all P and K as basal."),
    "cotton":    dict(name="Cotton", n=48, p=24, k=24, splits=[("Basal", .25), ("Squaring (about 30 days)", .4), ("Flowering (about 60 days)", .35)], note="Apply P as basal; split K in two doses."),
    "tomato":    dict(name="Tomato", n=48, p=24, k=24, splits=[("Basal", .33), ("After 25 days", .33), ("At fruit set", .34)], note="Extra potash at fruiting improves quality."),
    "chilli":    dict(name="Chilli", n=48, p=24, k=24, splits=[("Basal", .33), ("After 30 days", .33), ("At flowering", .34)], note="Avoid excess nitrogen; it causes leafy growth."),
    "potato":    dict(name="Potato", n=60, p=24, k=40, splits=[("Basal (at planting)", .5), ("At earthing up (about 30 days)", .5)], note="Apply P and K as basal."),
    "okra":      dict(name="Okra (Bhendi)", n=40, p=20, k=20, splits=[("Basal", .5), ("At flowering", .5)], note="Apply P and K as basal."),
    "groundnut": dict(name="Groundnut", n=8, p=16, k=16, splits=[("Basal (all at sowing)", 1.0)], note="Add gypsum at flowering for pod filling (follow local advice)."),
}
HA_PER_ACRE = 0.404686


@bp.route("/tools")
@account_required("farmer")
def hub():
    return render_template("tools.html")


@bp.route("/weather")
@account_required("farmer")
def weather():
    default = dict(name="Hyderabad, Telangana", lat=17.385, lng=78.487)
    u = current_user()
    if u:
        a = query("SELECT district, state FROM addresses WHERE user_id=? ORDER BY is_default DESC, id DESC LIMIT 1", (u["id"],), one=True)
        hit = locate(a["district"], a["state"]) if a else None
        if hit:
            default = dict(name=f"{a['district']}, {a['state']}", lat=hit[0], lng=hit[1])
    return render_template("weather.html", default=default)


@bp.route("/fertilizer-calculator")
@account_required("farmer")
def fertilizer_calculator():
    return render_template("fertilizer-calculator.html", crops=CROPS)


@bp.route("/api/fertilizer-calc")
@account_required("farmer")
def fertilizer_calc():
    key = request.args.get("crop", "")
    try:
        size = float(request.args.get("size", "1"))
    except ValueError:
        size = 0
    unit = request.args.get("unit", "acre")
    if key not in CROPS or not (0 < size <= 1000) or unit not in ("acre", "hectare"):
        return jsonify(ok=False, error="Choose a crop and enter a field size between 0 and 1000."), 400
    c = CROPS[key]
    acres = size if unit == "acre" else size / HA_PER_ACRE
    n, p, k = c["n"] * acres, c["p"] * acres, c["k"] * acres
    dap = p / 0.46                       # DAP 18-46-0
    n_left = max(0.0, n - dap * 0.18)
    urea = n_left / 0.46                 # Urea 46% N
    mop = k / 0.60                       # Muriate of potash 60% K2O
    products = {}
    for label, kw in (("urea", "urea"), ("dap", "dap"), ("mop", "potash")):
        found = _find_products(kw, 1)
        products[label] = _card(found[0]) if found else None
    r = lambda x: round(x, 1)
    return jsonify(ok=True, crop=c["name"], acres=round(acres, 2),
                   nutrients=dict(n=r(n), p=r(p), k=r(k)),
                   fert=dict(urea=r(urea), dap=r(dap), mop=r(mop)),
                   bags=dict(urea=round(urea / 45, 1), dap=round(dap / 50, 1), mop=round(mop / 50, 1)),
                   schedule=[dict(stage=s, urea=r(urea * f), dap=r(dap if i == 0 else 0), mop=r(mop if i == 0 else 0)) for i, (s, f) in enumerate(c["splits"])],
                   note=c["note"], products=products,
                   disclaimer="General guideline only. Fertilizer need depends on your soil test, variety, yield target and state recommendation. Add 2-4 tonnes of farmyard manure or compost per acre if available.")
