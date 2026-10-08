"""Crop Doctor: photo/symptom based plant-health guidance.

* AI mode (ANTHROPIC_API_KEY set): Claude looks at the uploaded leaf/plant photo (processed in memory, never stored).
* Basic mode: symptom checklist -> general causes and integrated pest management (IPM) steps.
Always guidance only: no pesticide doses are given - follow the product label or ask a Krishi Vigyan Kendra (KVK)."""
import base64, json, re, time, urllib.request
from flask import Blueprint, render_template, request, jsonify, current_app
from backend.assistant import _find_products, _card

bp = Blueprint("cropdoctor", __name__)
_HITS = {}
CROPS = ["Tomato", "Chilli", "Rice (Paddy)", "Maize", "Cotton", "Potato", "Okra (Bhendi)", "Groundnut", "Other"]

SYMPTOMS = {
    "yellow_leaves": "Yellowing leaves",
    "brown_spots": "Brown / black spots on leaves",
    "white_powder": "White powder or patches on leaves",
    "leaf_curl": "Curled or crinkled leaves",
    "wilting": "Wilting even with enough water",
    "holes_chewed": "Holes or chewed leaves / fruit",
    "sticky_insects": "Tiny insects or sticky leaves",
    "stunted": "Stunted, weak growth",
    "fruit_rot": "Spots or rot on fruit / pods",
}
KB = {
    "yellow_leaves": [
        dict(issue="Nitrogen or micronutrient deficiency", why="Older leaves turning uniformly pale yellow usually point to low nitrogen; yellow leaves with green veins suggest iron/zinc/magnesium shortage.",
             todo=["Take a soil test before adding fertilizer.", "Apply a balanced fertilizer or a foliar micronutrient mix as per the label.", "Add compost / vermicompost to improve soil health."], kw=["npk", "urea", "vermicompost"]),
        dict(issue="Waterlogging or root problems", why="Poorly drained soil starves roots of oxygen, which also turns leaves yellow.",
             todo=["Improve drainage and avoid overwatering.", "Check roots for brown, soft or rotting parts."], kw=["trichoderma"]),
    ],
    "brown_spots": [
        dict(issue="Fungal leaf spot / blight", why="Brown or black spots, often with yellow rings, spread fast in warm humid weather.",
             todo=["Remove and destroy badly affected leaves.", "Avoid overhead irrigation and give plants space for airflow.", "Use a fungicide suited to the crop - follow the label and safety interval.", "Rotate crops next season."], kw=["fungicide", "trichoderma", "neem"]),
    ],
    "white_powder": [
        dict(issue="Powdery mildew", why="A white, floury coating on leaves, common in dry days with cool humid nights.",
             todo=["Remove heavily coated leaves.", "Improve airflow and avoid excess nitrogen.", "Spray a suitable fungicide or neem-based product as per the label."], kw=["fungicide", "neem oil"]),
    ],
    "leaf_curl": [
        dict(issue="Sucking pests (thrips, mites, whitefly) or leaf curl virus", why="Curling, crinkling or cupping leaves are typical of sap-sucking pests, which can also spread viruses.",
             todo=["Inspect the underside of leaves for tiny insects.", "Use yellow sticky traps and remove infected plants early.", "Neem-based sprays help at early stages; use an insecticide only if needed and exactly as labelled."], kw=["neem oil", "insecticide", "organic pesticide"]),
    ],
    "wilting": [
        dict(issue="Wilt disease (fungal/bacterial) or root rot", why="If plants wilt in the day and do not recover by evening even with moist soil, roots or stems may be infected.",
             todo=["Uproot and destroy affected plants to protect neighbours.", "Do not irrigate from affected beds to healthy ones.", "Use bio-control such as Trichoderma in soil and practise crop rotation."], kw=["trichoderma", "fungicide"]),
        dict(issue="Water stress or heat", why="Too little water or very hot spells cause temporary wilting.",
             todo=["Irrigate early morning or evening.", "Mulch to keep soil moisture steady."], kw=["drip", "mulching"]),
    ],
    "holes_chewed": [
        dict(issue="Caterpillars, borers or beetles", why="Ragged holes, chewed edges or bored fruit mean leaf-eating caterpillars or fruit/shoot borers.",
             todo=["Hand-pick larvae in small plots and destroy egg masses.", "Use pheromone / light traps to monitor.", "Neem-based or other recommended insecticide sprays in the evening, as per label."], kw=["neem", "insecticide", "organic pesticide"]),
    ],
    "sticky_insects": [
        dict(issue="Aphids, whiteflies or mealybugs", why="Sticky honeydew and sooty black mould appear where these small sap-suckers feed in colonies.",
             todo=["Wash off colonies with a strong water jet on small plants.", "Install yellow sticky traps.", "Neem oil or a recommended insecticide as per the label; protect beneficial insects."], kw=["neem oil", "insecticide"]),
    ],
    "stunted": [
        dict(issue="Nutrient shortage, compacted soil or nematodes", why="Slow, weak plants often lack nutrients or have poor roots.",
             todo=["Soil test for NPK and micronutrients.", "Loosen compacted soil and add organic matter.", "Check roots for knots (nematodes)."], kw=["npk", "vermicompost", "neem cake"]),
    ],
    "fruit_rot": [
        dict(issue="Fruit rot / anthracnose or calcium shortage", why="Dark sunken spots or rot on fruit come from fungal infection in wet weather or uneven watering.",
             todo=["Remove and destroy infected fruit.", "Keep fruit off wet soil; water evenly.", "Use a suitable fungicide at the right stage per label."], kw=["fungicide", "mulching"]),
    ],
}


def _rate_ok():
    k, now = request.remote_addr or "x", time.time()
    hits = [t for t in _HITS.get(k, []) if now - t < 600]
    if len(hits) >= 12:
        return False
    _HITS[k] = hits + [now]
    return True


def _image_type(b):
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    return None


def _basic(crop, symptoms):
    picks = [s for s in symptoms if s in KB]
    if not picks:
        return None
    causes, todo, kws = [], [], []
    for s in picks:
        for e in KB[s]:
            causes.append(dict(name=e["issue"], why=e["why"]))
            todo += [t for t in e["todo"] if t not in todo]
            kws += e["kw"]
    return dict(mode="basic", crop=crop, condition=" / ".join(c["name"] for c in causes[:2]), confidence="n/a",
                summary="Based on the symptoms you selected, these are the most common causes. A photo-based diagnosis needs AI mode.",
                causes=causes, actions=todo[:8], prevention=["Scout the field twice a week.", "Use certified seed and rotate crops.", "Avoid working in wet fields to limit spread."],
                see_expert=True, keywords=list(dict.fromkeys(kws))[:5])


def _clean_spots(raw):
    """Validate damage boxes from the model: percentages inside the image."""
    out = []
    for sp in (raw if isinstance(raw, list) else [])[:6]:
        try:
            x, y, w, h = (float(sp[k]) for k in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            continue
        x, y = max(0.0, min(x, 99.0)), max(0.0, min(y, 99.0))
        w, h = max(2.0, min(w, 100 - x)), max(2.0, min(h, 100 - y))
        sev = sp.get("severity") if sp.get("severity") in ("low", "medium", "high") else "medium"
        out.append(dict(label=str(sp.get("label", "Damaged area"))[:40], severity=sev, x=round(x, 1), y=round(y, 1), w=round(w, 1), h=round(h, 1)))
    return out


def _claude(photo, mime, crop, symptoms, note):
    cfg = current_app.config
    system = ("You are an agronomy assistant for Indian smallholder farmers. Examine the plant photo and/or the symptoms and reply with ONLY one JSON object, no prose, with keys: "
              '"is_plant" (bool), "crop" (string), "condition" (most likely problem, or "Looks healthy"), "confidence" ("low"|"medium"|"high"), "summary" (2 sentences, simple English), '
              '"causes" (list of {"name","why"}, max 3), "actions" (list of up to 6 practical steps, organic/IPM first), "prevention" (list of up to 4), "see_expert" (bool), '
              '"keywords" (up to 5 short product search words such as "neem oil", "fungicide", "npk"). If a photo is given, also include \"spots\": a list of up to 6 objects marking EACH visibly damaged area (lesions, spots, holes, chewed or discoloured/dry patches, pests, rotten fruit) as {\"label\": short name e.g. \"Brown leaf spot\", \"severity\": \"low\"|\"medium\"|\"high\", \"x\": left edge, \"y\": top edge, \"w\": width, \"h\": height}, where x, y, w, h are PERCENTAGES (0-100) of the image width/height measured from the top-left corner; draw tight boxes around only the damaged area, not the whole leaf. Use an empty list if nothing is damaged. Never state pesticide doses or mixing rates; tell the farmer to follow the product label. '
              "If the image is not a plant, set is_plant false. Be honest about uncertainty; a photo alone cannot be conclusive.")
    content = []
    if photo:
        content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(photo).decode()}})
    content.append({"type": "text", "text": f"Crop: {crop or 'unknown'}\nSymptoms selected: {', '.join(SYMPTOMS.get(s, s) for s in symptoms) or 'none'}\nFarmer's note: {note or 'none'}"})
    body = json.dumps({"model": cfg["ANTHROPIC_MODEL"], "max_tokens": 1400, "system": system, "messages": [{"role": "user", "content": content}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "content-type": "application/json", "x-api-key": cfg["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = "".join(b.get("text", "") for b in json.loads(r.read()).get("content", []) if b.get("type") == "text")
    j = json.loads(text[text.index("{"): text.rindex("}") + 1])
    if not j.get("is_plant", True):
        return dict(mode="ai", not_plant=True)
    j["mode"] = "ai"
    j["causes"] = [c for c in j.get("causes", []) if isinstance(c, dict)][:3]
    j["actions"] = [str(a) for a in j.get("actions", [])][:6]
    j["prevention"] = [str(a) for a in j.get("prevention", [])][:4]
    j["keywords"] = [str(k)[:30] for k in j.get("keywords", [])][:5]
    j["spots"] = _clean_spots(j.get("spots")) if photo else []
    return j


@bp.route("/crop-doctor")
def crop_doctor():
    return render_template("crop-doctor.html", crops=CROPS, symptoms=SYMPTOMS, ai=bool(current_app.config.get("ANTHROPIC_API_KEY")))


@bp.route("/api/crop-doctor", methods=["POST"])
def diagnose():
    if not _rate_ok():
        return jsonify(ok=False, error="Too many checks in a short time. Please wait a few minutes."), 429
    crop = request.form.get("crop", "")[:30]
    symptoms = [s for s in request.form.get("symptoms", "").split(",") if s in SYMPTOMS]
    note = request.form.get("note", "")[:300]
    f = request.files.get("photo")
    photo = mime = None
    if f and f.filename:
        photo = f.read(4 * 1024 * 1024 + 1)
        mime = _image_type(photo)
        if len(photo) > 4 * 1024 * 1024 or not mime:
            return jsonify(ok=False, error="Please upload a JPG, PNG or WebP photo under 4 MB."), 400
    if not photo and not symptoms:
        return jsonify(ok=False, error="Upload a clear photo of the affected leaf or select at least one symptom."), 400

    result, notice = None, None
    if current_app.config.get("ANTHROPIC_API_KEY"):
        try:
            result = _claude(photo, mime, crop, symptoms, note)
        except Exception as e:
            current_app.logger.warning("crop doctor: Claude call failed (%s)", e)
            notice = "The AI service was unavailable, so this is the general symptom-based guide."
    elif photo:
        notice = "Photo analysis needs AI mode (an Anthropic API key on the server). Showing the general guide for the symptoms you selected."
    if result is None:
        result = _basic(crop, symptoms)
        if result is None:
            return jsonify(ok=False, error=notice or "Please select at least one symptom so I can give guidance."), 400
    if result.get("not_plant"):
        return jsonify(ok=True, not_plant=True, mode="ai")
    prods, seen = [], set()
    for kw in result.get("keywords", []):
        for p in _find_products(kw, 2):
            if p["id"] not in seen and len(prods) < 4:
                seen.add(p["id"]); prods.append(_card(p))
    result["products"] = prods
    result["notice"] = notice
    return jsonify(ok=True, **result)
