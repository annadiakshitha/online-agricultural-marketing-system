"""Central configuration + image catalogue for AgroConnect."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
    DATABASE = os.path.join(BASE_DIR, "database", "database.db")
    SCHEMA = os.path.join(BASE_DIR, "database", "schema.sql")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024          # 4 MB upload limit
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Pricing rules (mirrored in static/js/cart.js through window.AGRO)
    FREE_DELIVERY_ABOVE = 2000
    DELIVERY_FEE = 50
    TAX_PERCENT = 5


# ---------------------------------------------------------------------------
# Images
# Every image is a path relative to static/images/ and is named after its subject
# (products/tomato-seeds.jpg shows tomatoes, products/tractor.jpg shows a tractor).
#
# How an image is resolved (see backend.image_url):
#   1. local file in static/images/  ->  used (this is what `python download_images.py` fills)
#   2. GENERIC_REMOTE (hero / banners / portraits only, where any farm photo fits)
#   3. otherwise a dark placeholder labelled with the product name  ->  never a WRONG photo
#
# IMAGE_QUERIES holds the Unsplash search used for each file so the photo matches the
# product. Run `python download_images.py` (needs a free Unsplash API key) and then open
# image-checklist.html to confirm every product -> photo pair by eye.
# ---------------------------------------------------------------------------
UNSPLASH = "https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1600&q=80"

IMAGE_QUERIES = {
    # hero / banners / people (generic by nature)
    "hero/hero-farmer-field.jpg": "farmer green crop field sunrise",
    "banners/deals.jpg": "agricultural field harvest landscape",
    "banners/marketplace.jpg": "farmer inspecting crops field",
    "farmers/farmer-01.jpg": "indian farmer portrait field",
    "farmers/farmer-02.jpg": "farmer portrait smiling crops",
    "farmers/farmer-03.jpg": "farmer portrait rural",
    # blog (each matches its article)
    "blog/tomato-seed-guide.jpg": "tomato plants ripe tomatoes greenhouse",
    "blog/drip-irrigation-techniques.jpg": "drip irrigation field",
    "blog/organic-farming-basics.jpg": "organic vegetable farm",
    "blog/fertilizer-selection-guide.jpg": "fertilizer granules hand soil",
    # categories
    "categories/seeds.jpg": "seeds in hands sowing",
    "categories/fertilizers.jpg": "fertilizer granules",
    "categories/crop-protection.jpg": "spraying crops pesticide farm",
    "categories/farming-tools.jpg": "gardening hand tools soil",
    "categories/irrigation.jpg": "irrigation system field water",
    "categories/machinery.jpg": "tractor ploughing field",
    "categories/organic.jpg": "compost organic farming",
    "categories/animal-feed.jpg": "cattle feed farm",
    # products
    "products/maize-seeds.jpg": "maize corn cobs seeds",
    "products/rice-seeds.jpg": "rice paddy grains seeds",
    "products/cotton-seeds.jpg": "cotton plant bolls field",
    "products/tomato-seeds.jpg": "tomato seeds tomatoes",
    "products/chilli-seeds.jpg": "red chilli peppers plant",
    "products/okra-seeds.jpg": "okra lady finger vegetable",
    "products/potato-seeds.jpg": "potatoes seed potatoes soil",
    "products/groundnut-seeds.jpg": "groundnut peanuts plant",
    "products/npk-fertilizer.jpg": "npk fertilizer granules",
    "products/urea-fertilizer.jpg": "urea fertilizer white granules",
    "products/dap-fertilizer.jpg": "granular fertilizer bag farm",
    "products/potash-fertilizer.jpg": "potash fertilizer red granules",
    "products/neem-oil.jpg": "neem leaves neem oil",
    "products/fungicide.jpg": "fungicide spray crop leaves",
    "products/herbicide.jpg": "spraying herbicide weeds field",
    "products/insecticide.jpg": "insecticide spraying crop",
    "products/farming-tools.jpg": "garden hand tool set trowel",
    "products/hand-sprayer.jpg": "garden pressure sprayer",
    "products/knapsack-sprayer.jpg": "knapsack sprayer farmer spraying",
    "products/pruning-shears.jpg": "pruning shears secateurs",
    "products/drip-irrigation-kit.jpg": "drip irrigation pipes emitters",
    "products/sprinkler.jpg": "sprinkler irrigation field",
    "products/hdpe-pipe.jpg": "black irrigation pipe roll",
    "products/mulching-film.jpg": "plastic mulch film vegetable rows",
    "products/power-weeder.jpg": "power tiller weeder farm machine",
    "products/brush-cutter.jpg": "brush cutter grass trimmer",
    "products/power-tiller.jpg": "power tiller cultivator farm",
    "products/water-pump.jpg": "water pump irrigation motor",
    "products/battery-sprayer.jpg": "battery sprayer agriculture backpack",
    "products/tractor.jpg": "tractor farm field",
    "products/vermicompost.jpg": "vermicompost earthworms compost",
    "products/organic-pesticide.jpg": "organic pest control spray plants",
    "products/neem-cake.jpg": "organic manure soil fertilizer",
    "products/trichoderma.jpg": "bio fungicide powder soil",
    "products/cattle-feed.jpg": "cattle feed pellets cow",
    "products/poultry-feed.jpg": "poultry feed hens farm",
    "products/mineral-mixture.jpg": "mineral supplement cattle lick",
}

# Generic scenery only (a farm photo is "correct" for these). IDs are not verified:
# if one 404s the page falls back to a dark gradient, never to a mismatched product photo.
_GENERIC_IDS = {
    "hero/hero-farmer-field.jpg": "1500937386664-56d1dfef3854",
    "banners/deals.jpg": "1464226184884-fa280b87c399",
    "banners/marketplace.jpg": "1597916829826-02e5bb4a54e0",
    "farmers/farmer-01.jpg": "1589923188900-85dae523342b",
    "farmers/farmer-02.jpg": "1595508064774-5ff825520bbd",
    "farmers/farmer-03.jpg": "1597916829826-02e5bb4a54e0",
}
GENERIC_REMOTE = {k: UNSPLASH.format(id=v) for k, v in _GENERIC_IDS.items()}


# ---------------------------------------------------------------------------
# AI assistant (optional). Without a key the assistant still works in "basic" mode
# using your own catalogue + order data. Set ANTHROPIC_API_KEY for full AI answers.
# ---------------------------------------------------------------------------
Config.ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
Config.ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
