"""AgroConnect AI assistant. Additive blueprint: POST /api/assistant.

* With ANTHROPIC_API_KEY set -> answers come from Claude, grounded in your catalogue (and the signed-in
  customer's own orders).
* Without a key -> a built-in rule-based "basic mode" answers from the same data, so the feature always works.
"""
import json, re, time, urllib.request, urllib.error
from flask import Blueprint, request, jsonify, current_app, session, url_for
from backend import query, current_user, image_url, sale_price

bp = Blueprint("assistant", __name__)
_HITS = {}                                   # tiny in-memory rate limiter {key: [timestamps]}
STOP = set("a an the is are for of to in on and or my me i you can do does what which how best need want buy get show give any some with from at it this that please tell about price cost".split())

TIPS = {
    "tomato": "Tomato: sow in a nursery 4-5 weeks before transplanting, space plants 60x45 cm, stake early and water evenly (drip is ideal). Watch for early blight and fruit borer; balanced NPK with extra potash at fruiting helps quality.",
    "rice": "Rice (paddy): treat seed before sowing, transplant 21-25 day seedlings, keep 2-5 cm standing water in the vegetative stage and split nitrogen (urea) into 3 doses. Scout for stem borer and blast.",
    "paddy": "Rice (paddy): treat seed before sowing, transplant 21-25 day seedlings, keep 2-5 cm standing water in the vegetative stage and split nitrogen (urea) into 3 doses.",
    "maize": "Maize: sow at 60x20 cm, apply a basal dose of DAP/NPK and top-dress urea at knee-high and tasselling. Control fall armyworm early by scouting whorls weekly.",
    "chilli": "Chilli: raise seedlings in a nursery, transplant at 60x45 cm, avoid waterlogging and use mulch. Leaf curl (thrips/mites) is the main risk, so spray neem-based products early.",
    "cotton": "Cotton: sow after the first good rains at 90x60 cm, keep the field weed free for 45 days and scout for pink bollworm and whitefly. Avoid excess nitrogen late in the season.",
    "potato": "Potato: use certified, well-sprouted seed tubers, plant 20 cm apart in ridges and earth up at 30 days. Prevent late blight with timely preventive sprays in cool humid weather.",
    "okra": "Okra (bhendi): soak seed overnight, sow 60x30 cm, pick pods every 2-3 days while tender and watch for yellow vein mosaic and fruit borer.",
}
FAQ = [
    (r"\b(deliver|delivery|shipping|ship)\b", "Delivery is free above ₹2000, otherwise ₹50. Most pincodes get orders in 3-5 business days. You can check your pincode on any product page."),
    (r"\b(return|refund|replace|exchange)\b", "Unopened products can be returned within the return window shown in Contact → Returns. For damaged items, contact support with your order number."),
    (r"\b(pay|payment|upi|card|cod|cash)\b", "We accept UPI, credit/debit cards and Cash on Delivery. Card and UPI are simulated in this demo and no card details are stored."),
    (r"\b(sell|seller|become a seller|vendor)\b", "To sell on AgroConnect, register as a Seller. New products are reviewed by an admin before they go live."),
    (r"\b(gst|tax)\b", "A 5% GST is added at checkout and shown in your order summary."),
    (r"\b(hello|hi|hey|namaste|namaskaram|vanakkam)\b", "Hello! I can help you find seeds, fertilizers and tools, track an order, or answer farming questions. What do you need?"),
]
GENERIC = set("seed seeds fertilizer fertilizers tool tools machine machinery kit spray sprayer product products organic".split())
LANG_NAMES = {"en": "English", "te": "Telugu", "hi": "Hindi", "ta": "Tamil", "kn": "Kannada", "mr": "Marathi"}


def _rate_ok():
    key = request.remote_addr or "x"
    now = time.time()
    hits = [t for t in _HITS.get(key, []) if now - t < 600]
    if len(hits) >= 30:
        _HITS[key] = hits
        return False
    _HITS[key] = hits + [now]
    return True


def _find_products(text, limit=4):
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2][:6]
    if not words:
        return []
    score, params = [], []
    for w in words:
        like = f"%{w.rstrip('s')}%"
        score.append("(CASE WHEN p.name LIKE ? THEN 3 ELSE 0 END + CASE WHEN p.tags LIKE ? THEN 2 ELSE 0 END + CASE WHEN c.name LIKE ? THEN 1 ELSE 0 END + CASE WHEN p.description LIKE ? THEN 1 ELSE 0 END)")
        params += [like, like, like, like]
    rows = query(f"""SELECT p.*, c.name AS category, s.business_name AS seller, ({'+'.join(score)}) AS sc
                     FROM products p JOIN categories c ON c.id=p.category_id JOIN sellers s ON s.id=p.seller_id
                     WHERE p.status='approved' AND p.stock>0 ORDER BY sc DESC, p.discount DESC LIMIT 30""", tuple(params))
    rows = [r for r in rows if r["sc"] > 0]
    specific = [w.rstrip("s") for w in words if w not in GENERIC]
    if specific:                                  # "tomato seeds" must match tomato, not just the word "seeds"
        rows = [r for r in rows if any(w in (r["name"] + " " + (r["tags"] or "")).lower() for w in specific)]
    return rows[:limit]


def _card(p):
    return dict(id=p["id"], name=p["name"], price=round(sale_price(p["price"], p["discount"])), old=round(p["price"]) if p["discount"] else None,
                discount=p["discount"], seller=p["seller"], category=p["category"],
                image=image_url(p["image"]), url=url_for("products.product_details", pid=p["id"]) if "products.product_details" in current_app.view_functions else f"/product/{p['id']}")


def _my_orders(limit=5):
    u = current_user()
    if not u:
        return []
    return query("SELECT id, order_number, status, total_amount, created_at FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (u["id"], limit))


def _local_reply(msg):
    low = msg.lower()
    m = re.search(r"agc\d{6,}", low)
    if m or re.search(r"\b(track|where is|status|my order|order status)\b", low):
        u = current_user()
        if not u:
            return "Please log in to see your orders, then ask me again. You can also open My Orders to see the live map.", []
        orders = _my_orders(5)
        if m:
            orders = [o for o in orders if o["order_number"].lower() == m.group(0)] or orders
        if not orders:
            return "You have no orders yet. Browse the shop and I can suggest products.", []
        o = orders[0]
        return (f"Your latest order {o['order_number']} is currently “{o['status']}”. Open it from My Orders to see its position on the map: /order/{o['id']}"), []
    pin = re.search(r"\b[1-9]\d{5}\b", low)
    if pin:
        days = {"5": "2-3", "6": "3-4", "4": "3-5"}.get(pin.group(0)[0], "4-6")
        return f"Delivery is available to pincode {pin.group(0)}, usually in {days} business days.", []
    for pat, ans in FAQ:
        if re.search(pat, low):
            return ans, []
    tip = next((t for k, t in TIPS.items() if k in low), None)
    found = _find_products(msg)
    if tip:
        return tip + (" Here are matching products:" if found else ""), found
    if found:
        return "Here are the best matches from our catalogue:", found
    return ("I couldn't find that in the catalogue. Try a crop or product name such as “tomato seeds”, “drip irrigation” or “urea”, "
            "or ask about delivery, payments or tracking an order."), []


def _claude_reply(msg, history, lang, products):
    cfg = current_app.config
    catalogue = "\n".join(f"- id {p['id']}: {p['name']} | {p['category']} | seller {p['seller']} | ₹{round(sale_price(p["price"], p["discount"]))} (MRP ₹{round(p['price'])}, {p['discount']}% off) | stock {p['stock']}" for p in products) or "(no direct matches)"
    orders = "\n".join(f"- {o['order_number']}: {o['status']}, ₹{round(o['total_amount'])}" for o in _my_orders()) or "(not logged in or no orders)"
    system = ("You are AgroConnect's shopping and farming assistant for Indian farmers. Be concise (max ~120 words), practical and friendly. "
              f"Reply in {LANG_NAMES.get(lang, 'English')}. Recommend ONLY products from the catalogue list below and mention their exact names and prices in ₹; never invent products, prices or order details. "
              "Give general agronomy tips, and for serious crop disease or pesticide-dose questions advise consulting the local Krishi Vigyan Kendra or an agronomist. "
              "You cannot place orders or change accounts; tell users to use the Cart and Checkout. Order tracking is on the order page map.\n\n"
              f"CATALOGUE MATCHES:\n{catalogue}\n\nCUSTOMER ORDERS:\n{orders}")
    msgs = [{"role": h["role"], "content": str(h["content"])[:800]} for h in history[-8:] if h.get("role") in ("user", "assistant") and h.get("content")]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    msgs = [m for i, m in enumerate(msgs) if i == 0 or m["role"] != msgs[i - 1]["role"]]
    if not msgs or msgs[-1]["role"] != "user" or msgs[-1]["content"] != msg:
        msgs.append({"role": "user", "content": msg})
    body = json.dumps({"model": cfg["ANTHROPIC_MODEL"], "max_tokens": 500, "system": system, "messages": msgs}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "content-type": "application/json", "x-api-key": cfg["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


@bp.route("/api/assistant", methods=["POST"])
def assistant():
    data = request.get_json(silent=True) or {}
    msg = str(data.get("message", "")).strip()[:500]
    lang = data.get("lang") if data.get("lang") in LANG_NAMES else "en"
    if not msg:
        return jsonify(ok=False, error="Please type a question."), 400
    if not _rate_ok():
        return jsonify(ok=False, error="You are sending messages too quickly. Please wait a moment."), 429
    products = _find_products(msg, 5)
    mode, reply = "basic", None
    if current_app.config.get("ANTHROPIC_API_KEY"):
        try:
            reply = _claude_reply(msg, data.get("history") or [], lang, products)
            mode = "ai"
        except Exception as e:                                  # network / key / quota problem -> graceful fallback
            current_app.logger.warning("assistant: Claude call failed (%s); using basic mode", e)
    if not reply:
        reply, products = _local_reply(msg)
    elif mode == "ai":
        products = products[:4]
    return jsonify(ok=True, reply=reply, products=[_card(p) for p in products[:4]], mode=mode)


@bp.route("/api/assistant/status")
def assistant_status():
    return jsonify(ok=True, mode="ai" if current_app.config.get("ANTHROPIC_API_KEY") else "basic")
