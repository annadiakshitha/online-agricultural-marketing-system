"""Additive schema for the v2 features (rentals, coupons). Safe to run on every start and on old databases."""
import sqlite3
from werkzeug.security import generate_password_hash

SQL = """
CREATE TABLE IF NOT EXISTS rental_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
  name TEXT NOT NULL, kind TEXT NOT NULL, description TEXT, image TEXT, price_per_day REAL NOT NULL, deposit REAL DEFAULT 0,
  units INTEGER DEFAULT 1, district TEXT, state TEXT, active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS rental_bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL REFERENCES rental_items(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, start_date TEXT NOT NULL, end_date TEXT NOT NULL, days INTEGER NOT NULL,
  rent REAL NOT NULL, deposit REAL DEFAULT 0, total REAL NOT NULL, status TEXT DEFAULT 'Requested',
  customer_name TEXT, phone TEXT, address TEXT, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_rb_item ON rental_bookings(item_id, start_date, end_date);
CREATE TABLE IF NOT EXISTS coupons (
  id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE, kind TEXT NOT NULL CHECK(kind IN ('percent','flat')), value REAL NOT NULL,
  min_order REAL DEFAULT 0, max_discount REAL, expires TEXT, usage_limit INTEGER, used_count INTEGER DEFAULT 0, active INTEGER DEFAULT 1,
  description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS coupon_redemptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, coupon_id INTEGER NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL, order_id INTEGER NOT NULL, UNIQUE(coupon_id, user_id));
CREATE TABLE IF NOT EXISTS farmer_profiles (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, village TEXT, district TEXT, state TEXT,
  farm_acres REAL DEFAULT 1, crops TEXT DEFAULT '', irrigation TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_extras (order_id INTEGER PRIMARY KEY REFERENCES orders(id) ON DELETE CASCADE, coupon_code TEXT, coupon_discount REAL DEFAULT 0);
"""

RENTALS = [  # (seller index, name, kind, description, image, per day, deposit, units, district, state)
    (0, "Mini Tractor 25 HP with Driver", "Tractor", "Compact diesel tractor for ploughing, puddling and haulage. Fuel extra; operator available on request.", "products/tractor.jpg", 2200, 10000, 2, "Warangal", "Telangana"),
    (1, "Power Tiller 7 HP", "Tiller", "Petrol/diesel power tiller for seedbed preparation in small and terraced plots.", "products/power-tiller.jpg", 900, 4000, 3, "Guntur", "Andhra Pradesh"),
    (2, "Power Weeder 4-stroke", "Weeder", "Lightweight weeder for inter-row weeding in vegetables, maize and cotton.", "products/power-weeder.jpg", 600, 3000, 4, "Mysuru", "Karnataka"),
    (3, "Brush Cutter 2-stroke", "Cutter", "Cuts grass, bunds and light crop residue. Includes blade and harness.", "products/brush-cutter.jpg", 350, 1500, 5, "Nashik", "Maharashtra"),
    (0, "Water Pump 1 HP (Monoblock)", "Pump", "Portable monoblock pump with suction and delivery pipes for lifting water from wells or channels.", "products/water-pump.jpg", 250, 1200, 6, "Warangal", "Telangana"),
    (1, "Battery Sprayer 16 L", "Sprayer", "Rechargeable backpack sprayer, about 6 hours of spraying per charge. Cleaned after every rental.", "products/battery-sprayer.jpg", 150, 800, 8, "Guntur", "Andhra Pradesh"),
    (3, "Knapsack Sprayer 16 L", "Sprayer", "Manual lever sprayer with adjustable nozzle for pesticide and foliar nutrient sprays.", "products/knapsack-sprayer.jpg", 100, 500, 8, "Nashik", "Maharashtra"),
]

CUSTOMER_CATEGORIES = [
    ("Fresh Vegetables", "fresh-vegetables", "categories/organic.jpg", "Farm-fresh vegetables sourced from trusted growers."),
    ("Fruits", "fruits", "categories/organic.jpg", "Fresh seasonal fruits and orchard produce."),
    ("Grains & Pulses", "grains-pulses", "categories/seeds.jpg", "Rice, maize, groundnuts and everyday farm-sourced staples."),
    ("Organic Produce", "organic-produce", "categories/organic.jpg", "Naturally grown produce and organic farm goods."),
]
FARMER_CATEGORY_AUDIENCE = {
    "seeds": "farmer", "fertilizers": "farmer", "crop-protection": "farmer",
    "farming-tools": "farmer", "irrigation": "farmer", "machinery": "farmer",
    "organic-products": "farmer", "animal-feed": "farmer",
}
CUSTOMER_PRODUCTS = [
    ("Fresh Tomatoes", "fresh-vegetables", 70, 5, 120, "Farm Fresh", "tomato,vegetable,fresh", 1, "products/tomato-seeds.jpg", "Fresh red tomatoes selected for everyday cooking.", "Pack: 1 kg|Grade: Fresh|Origin: Indian farms"),
    ("Fresh Potatoes", "fresh-vegetables", 45, 0, 180, "Farm Fresh", "potato,vegetable,fresh", 0, "products/potato-seeds.jpg", "Clean, firm potatoes sourced from local growers.", "Pack: 1 kg|Grade: Fresh|Origin: Indian farms"),
    ("Premium Rice", "grains-pulses", 85, 8, 150, "AgroConnect Select", "rice,paddy,grain", 0, "products/rice-seeds.jpg", "Quality rice sourced from Indian farming communities.", "Pack: 1 kg|Grade: Premium|Origin: Indian farms"),
    ("Groundnuts", "grains-pulses", 140, 5, 100, "AgroConnect Select", "groundnut,peanut,pulse", 0, "products/groundnut-seeds.jpg", "Fresh groundnuts suitable for roasting, cooking and snacks.", "Pack: 1 kg|Grade: Premium|Origin: Indian farms"),
    ("Organic Tomato Basket", "organic-produce", 120, 10, 70, "GreenGrow Organic", "organic,tomato,vegetable", 1, "products/tomato-seeds.jpg", "Naturally grown tomatoes from verified organic farming practices.", "Pack: 1 kg|Certification: Organic|Origin: Indian farms"),
]

COUPONS = [  # code, kind, value, min_order, max_discount, usage_limit, description
    ("AGRO10", "percent", 10, 500, 300, None, "10% off orders above ₹500 (up to ₹300)"),
    ("KISAN100", "flat", 100, 999, None, None, "Flat ₹100 off orders above ₹999"),
    ("WELCOME50", "flat", 50, 300, None, 1000, "₹50 off your order above ₹300"),
]


def ensure(db_path):
    db = sqlite3.connect(db_path)
    db.executescript(SQL)
    # Add role-aware category visibility to existing databases.
    cols = [r[1] for r in db.execute("PRAGMA table_info(categories)").fetchall()]
    if "audience" not in cols:
        db.execute("ALTER TABLE categories ADD COLUMN audience TEXT NOT NULL DEFAULT 'farmer'")
    for slug, audience in FARMER_CATEGORY_AUDIENCE.items():
        db.execute("UPDATE categories SET audience=? WHERE slug=?", (audience, slug))
    for name, slug, image, desc in CUSTOMER_CATEGORIES:
        db.execute("INSERT OR IGNORE INTO categories (name,slug,image,description,audience) VALUES (?,?,?,?,?)", (name, slug, image, desc, "customer"))

    # Keep the demo farmer identified by the existing farmer profile.
    farmer = db.execute("SELECT u.id FROM users u JOIN farmer_profiles f ON f.user_id=u.id WHERE u.email='farmer@agroconnect.com'").fetchone()
    if farmer:
        # Existing databases historically stored farmers as customers; the profile remains the source of truth.
        pass

    sellers = [r[0] for r in db.execute("SELECT id FROM sellers ORDER BY id").fetchall()]
    if sellers:
        for name, slug, price, discount, stock, brand, tags, organic, image, desc, specs in CUSTOMER_PRODUCTS:
            cid = db.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()[0]
            if not db.execute("SELECT 1 FROM products WHERE name=? AND category_id=?", (name, cid)).fetchone():
                db.execute("INSERT INTO products (name,description,category_id,seller_id,price,discount,stock,image,brand,tags,organic,specs,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (name, desc, cid, sellers[0], price, discount, stock, image, brand, tags, organic, specs, "approved"))

    if not db.execute("SELECT 1 FROM users WHERE email='farmer@agroconnect.com'").fetchone():
        uid = db.execute("INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,'customer')",
                         ("Ravi Kumar", "farmer@agroconnect.com", "9876501234", generate_password_hash("farmer123"))).lastrowid
        db.execute("INSERT INTO farmer_profiles (user_id,village,district,state,farm_acres,crops,irrigation) VALUES (?,?,?,?,?,?,?)",
                   (uid, "Chityal", "Nalgonda", "Telangana", 5, "Rice,Cotton,Chilli", "Borewell"))
    db.commit(); db.execute("PRAGMA foreign_keys=ON"); db.close()
