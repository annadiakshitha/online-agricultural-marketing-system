"""Create the SQLite database and fill it with realistic Indian demo data.
Run:  python database/seed.py   (or just start the app - it seeds on first run)."""
import os, sys, random, sqlite3, json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from config import Config  # noqa: E402

# Farmer catalogue categories. Customer categories are added by backend/migrate.py so
# both fresh installs and existing databases receive the same role-aware catalogue.
CATEGORIES = [
    ("Seeds", "seeds", "categories/seeds.jpg", "High-germination hybrid and open-pollinated seeds."),
    ("Fertilizers", "fertilizers", "categories/fertilizers.jpg", "Macro and micro nutrients for every crop stage."),
    ("Crop Protection", "crop-protection", "categories/crop-protection.jpg", "Insecticides, fungicides and herbicides."),
    ("Farming Tools", "farming-tools", "categories/farming-tools.jpg", "Hand tools, sprayers and everyday essentials."),
    ("Irrigation", "irrigation", "categories/irrigation.jpg", "Drip, sprinkler and water-saving systems."),
    ("Machinery", "machinery", "categories/machinery.jpg", "Power tillers, weeders, pumps and more."),
    ("Organic Products", "organic-products", "categories/organic.jpg", "Certified organic inputs for natural farming."),
    ("Animal Feed", "animal-feed", "categories/animal-feed.jpg", "Balanced feed for cattle, poultry and goats."),
]

SELLERS = [  # (name, email, business, location)
    ("Suresh Reddy", "seller@agroconnect.com", "GreenGrow Agro", "Warangal, Telangana"),
    ("Lakshmi Naidu", "lakshmi@agroconnect.com", "Kisan Seeds Co.", "Guntur, Andhra Pradesh"),
    ("Manjunath Gowda", "manju@agroconnect.com", "Mysore Agri Supplies", "Mysuru, Karnataka"),
    ("Prakash Patil", "prakash@agroconnect.com", "Sahyadri Farm Inputs", "Nashik, Maharashtra"),
    ("Murugan Selvam", "murugan@agroconnect.com", "Cauvery Agro Traders", "Thanjavur, Tamil Nadu"),
    ("Anil Kumar", "anil@agroconnect.com", "Malabar Organics", "Kozhikode, Kerala"),
    ("Venkat Rao", "venkat@agroconnect.com", "Telangana Irrigation Hub", "Karimnagar, Telangana"),
    ("Sunita Deshmukh", "sunita@agroconnect.com", "Vidarbha Agro Mart", "Nagpur, Maharashtra"),
    ("Ravi Teja", "ravi@agroconnect.com", "Godavari Crop Care", "Rajahmundry, Andhra Pradesh"),
    ("Basavaraj Hiremath", "basavaraj@agroconnect.com", "Dharwad Farm Machinery", "Dharwad, Karnataka"),
]

CUSTOMERS = [
    ("Ramesh Kumar", "customer@agroconnect.com", "Nalgonda", "Telangana", "508001"),
    ("Srinivas Goud", "srinivas@example.com", "Medak", "Telangana", "502110"),
    ("Padma Devi", "padma@example.com", "Krishna", "Andhra Pradesh", "521001"),
    ("Kiran Shetty", "kiran@example.com", "Udupi", "Karnataka", "576101"),
    ("Dnyaneshwar Jadhav", "dnyan@example.com", "Pune", "Maharashtra", "412105"),
    ("Karthik Raja", "karthik@example.com", "Madurai", "Tamil Nadu", "625001"),
    ("Shaji Thomas", "shaji@example.com", "Kottayam", "Kerala", "686001"),
    ("Anitha Rao", "anitha@example.com", "Hassan", "Karnataka", "573201"),
    ("Mahesh Babu", "mahesh@example.com", "Kurnool", "Andhra Pradesh", "518001"),
    ("Savitha Kulkarni", "savitha@example.com", "Belagavi", "Karnataka", "590001"),
]

# name, category, MRP, discount%, stock, brand, tags, organic, image, description, specs
P = [
 ("Hybrid Maize Seeds", "seeds", 850, 12, 120, "Kisan Gold", "maize,corn,hybrid,kharif", 0, "maize-seeds", "High-yielding single-cross hybrid maize with uniform cobs and strong stalk. Suited for kharif and rabi sowing.", "Pack: 4 kg|Germination: 95%|Maturity: 105-110 days|Season: Kharif / Rabi"),
 ("Seed Potatoes - Kufri Jyoti", "seeds", 720, 10, 80, "Namdhari", "potato,seed potato,tuber,rabi,vegetable", 0, "potato-seeds", "Certified disease-free seed tubers with uniform size and high sprouting rate. Suited for rabi planting.", "Pack: 10 kg|Variety: Kufri Jyoti|Tuber size: 35-55 mm|Maturity: 90-110 days"),
 ("Mini Tractor 25 HP", "machinery", 485000, 8, 4, "VST Shakti", "tractor,mini tractor,farm machinery,ploughing", 0, "tractor", "Compact 25 HP diesel tractor for ploughing, haulage and orchard work on small and medium farms.", "Engine: 25 HP diesel|Gears: 8F+2R|Lift capacity: 750 kg|Warranty: 2 years"),
 ("Rice Seeds (Paddy) - BPT 5204", "seeds", 720, 10, 200, "Kisan Gold", "rice,paddy,samba,kharif", 0, "rice-seeds", "Popular fine-grain paddy variety with excellent cooking quality and good tolerance to blast.", "Pack: 5 kg|Germination: 90%|Maturity: 145-150 days|Grain: Medium slender"),
 ("BT Cotton Seeds (450 g)", "seeds", 930, 8, 90, "Rasi Agri", "cotton,bt,hybrid,kharif", 0, "cotton-seeds", "Bollgard-II technology hybrid cotton seed with bollworm protection and high boll retention.", "Pack: 450 g|Technology: BG-II|Maturity: 150-160 days|Spacing: 90 x 60 cm"),
 ("F1 Hybrid Tomato Seeds", "seeds", 380, 15, 75, "Namdhari", "tomato,vegetable,hybrid,f1", 0, "tomato-seeds", "Determinate F1 tomato with firm, deep-red fruits and long shelf life, ideal for market transport.", "Pack: 10 g|Fruit weight: 90-110 g|First harvest: 65 days|Yield: 30-35 t/acre"),
 ("Hot Chilli Seeds - Teja", "seeds", 540, 10, 60, "Kisan Gold", "chilli,mirchi,teja,spice", 0, "chilli-seeds", "Pungent, deep-red Teja type chilli popular in Guntur markets. Good dry-weight recovery.", "Pack: 50 g|Pungency: High|Colour value: 100+ ASTA|Season: Kharif"),
 ("Okra (Bhendi) Seeds", "seeds", 210, 5, 140, "Mahyco", "okra,bhendi,vegetable", 0, "okra-seeds", "Dark-green, tender okra with resistance to yellow vein mosaic virus.", "Pack: 100 g|Pod length: 12-14 cm|First picking: 45 days|YVMV: Tolerant"),
 ("NPK 19:19:19 Water Soluble Fertilizer", "fertilizers", 1250, 8, 80, "IFFCO", "npk,19-19-19,water soluble,foliar", 0, "npk-fertilizer", "Fully water-soluble balanced fertilizer for fertigation and foliar spray across all crops.", "Pack: 5 kg|N-P-K: 19-19-19|Solubility: 100%|Use: Drip / Foliar"),
 ("Urea Fertilizer (46% N)", "fertilizers", 540, 0, 300, "Coromandel", "urea,nitrogen,basal", 0, "urea-fertilizer", "Prilled urea with 46% nitrogen for top dressing in paddy, maize, sugarcane and cotton.", "Pack: 45 kg|Nitrogen: 46%|Form: Prilled|Use: Top dressing"),
 ("DAP Fertilizer 18:46:0", "fertilizers", 1350, 0, 150, "IFFCO", "dap,phosphorus,basal", 0, "dap-fertilizer", "Diammonium phosphate for strong root development - best applied as basal dose at sowing.", "Pack: 50 kg|N-P: 18-46|Form: Granular|Use: Basal"),
 ("Potash (MOP) 60%", "fertilizers", 780, 5, 110, "Zuari", "potash,mop,potassium", 0, "potash-fertilizer", "Muriate of potash improves fruit quality, sugar content and drought tolerance.", "Pack: 25 kg|K2O: 60%|Form: Granular|Use: Basal / Top dress"),
 ("Neem Oil 1500 PPM", "crop-protection", 480, 20, 130, "Multiplex", "neem oil,pesticide,organic,azadirachtin", 1, "neem-oil", "Cold-pressed neem oil concentrate that controls aphids, whiteflies and mites on vegetables and fruit crops.", "Pack: 1 L|Azadirachtin: 1500 PPM|Dilution: 3 ml / L|Re-entry: 24 h"),
 ("Mancozeb 75% WP Fungicide", "crop-protection", 520, 12, 85, "Indofil", "fungicide,mancozeb,blight", 0, "fungicide", "Broad-spectrum protective fungicide against early and late blight, downy mildew and leaf spots.", "Pack: 1 kg|Active: Mancozeb 75% WP|Dose: 2.5 g / L|PHI: 7 days"),
 ("Systemic Herbicide 1 L", "crop-protection", 640, 10, 70, "Bayer", "herbicide,weed,glyphosate", 0, "herbicide", "Non-selective systemic herbicide for control of annual and perennial weeds in non-crop areas.", "Pack: 1 L|Active: Glyphosate 41% SL|Dose: 8 ml / L|Rainfast: 6 h"),
 ("Imidacloprid 17.8% SL Insecticide", "crop-protection", 360, 15, 95, "Dhanuka", "insecticide,imidacloprid,sucking pests", 0, "insecticide", "Systemic insecticide for sucking pests like jassids, aphids and whiteflies.", "Pack: 100 ml|Active: Imidacloprid 17.8%|Dose: 0.3 ml / L|PHI: 14 days"),
 ("Mini Garden Tool Kit (5 pcs)", "farming-tools", 1099, 18, 100, "Kisan Kraft", "garden,tool kit,trowel,hand tools", 0, "farming-tools", "Five-piece hardened-steel kit with ergonomic grip - trowel, cultivator, weeder, pruner and fork.", "Pieces: 5|Material: Carbon steel|Handle: Rubber grip|Warranty: 6 months"),
 ("Pressure Hand Sprayer 5 L", "farming-tools", 1450, 14, 65, "Neptune", "sprayer,hand sprayer,pump", 0, "hand-sprayer", "Compression sprayer with brass nozzle and pressure valve for kitchen gardens and nurseries.", "Capacity: 5 L|Nozzle: Brass|Tank: HDPE|Warranty: 1 year"),
 ("Knapsack Sprayer 16 L", "farming-tools", 2100, 16, 55, "Neptune", "sprayer,knapsack,manual", 0, "knapsack-sprayer", "Manual back-pack sprayer with padded straps and adjustable nozzle for field crops.", "Capacity: 16 L|Pressure: 3-4 bar|Weight: 3.2 kg|Warranty: 1 year"),
 ("Bypass Pruning Shears", "farming-tools", 340, 10, 180, "Falcon", "pruner,secateur,shears", 0, "pruning-shears", "Forged steel bypass shears for clean cuts on branches up to 20 mm.", "Length: 8 inch|Blade: SK-5 steel|Cut: 20 mm|Handle: Non-slip"),
 ("Drip Irrigation Kit (1 Acre)", "irrigation", 4200, 29, 40, "Jain Irrigation", "drip,irrigation kit,water saving", 0, "drip-irrigation-kit", "Complete drip set with lateral lines, emitters, filter and fittings. Saves up to 60% water.", "Coverage: 1 acre|Emitter: 4 LPH|Lateral: 16 mm|Warranty: 2 years"),
 ("Rotating Sprinkler Set (10 pcs)", "irrigation", 1850, 12, 50, "Finolex", "sprinkler,irrigation,lawn", 0, "sprinkler", "360-degree impact sprinklers with 12 m throw radius, suited to groundnut, vegetables and lawns.", "Pieces: 10|Throw: 12 m|Inlet: 3/4 inch|Material: UV-stabilised PP"),
 ("HDPE Pipe 32 mm (50 m)", "irrigation", 1750, 10, 45, "Supreme", "pipe,hdpe,irrigation", 0, "hdpe-pipe", "Flexible, UV-resistant HDPE pipe for sub-main and lateral water supply.", "Length: 50 m|Diameter: 32 mm|Pressure: 6 kgf|Colour: Black"),
 ("Mulching Film 25 micron (400 m)", "irrigation", 2400, 15, 35, "Garware", "mulch,film,weed control", 0, "mulching-film", "Silver-black mulching film that suppresses weeds, retains soil moisture and reduces pest incidence.", "Length: 400 m|Width: 1.2 m|Thickness: 25 micron|Colour: Silver / black"),
 ("Power Weeder 4-Stroke", "machinery", 28500, 12, 12, "Kisankraft", "power weeder,tiller,machine", 0, "power-weeder", "Lightweight 4-stroke petrol weeder for inter-cultivation in sugarcane, cotton and vegetables.", "Engine: 4-stroke, 3 HP|Working width: 60 cm|Fuel tank: 2.5 L|Warranty: 1 year"),
 ("Petrol Brush Cutter 52cc", "machinery", 9800, 18, 20, "Kisankraft", "brush cutter,grass,harvest", 0, "brush-cutter", "Side-pack brush cutter for harvesting paddy, clearing bunds and trimming grass.", "Engine: 52 cc 2-stroke|Power: 1.7 HP|Blade: 3T/8T|Warranty: 1 year"),
 ("Mini Power Tiller 7 HP", "machinery", 78000, 10, 5, "VST Shakti", "power tiller,tractor,machinery", 0, "power-tiller", "Diesel mini tiller for puddling and seedbed preparation in small and medium farms.", "Engine: 7 HP diesel|Working width: 70 cm|Gears: 2F+1R|Warranty: 2 years"),
 ("Centrifugal Water Pump 1 HP", "machinery", 5400, 14, 30, "Crompton", "pump,water pump,motor", 0, "water-pump", "Self-priming monoblock pump for borewell and canal lift irrigation.", "Power: 1 HP|Head: 25 m|Outlet: 1 inch|Warranty: 2 years"),
 ("Battery Operated Sprayer 18 L", "machinery", 3999, 20, 40, "Sun Agro", "battery sprayer,agricultural sprayer", 0, "battery-sprayer", "Rechargeable knapsack sprayer with 12V battery - up to 6 hours of spraying per charge.", "Capacity: 18 L|Battery: 12V 8Ah|Run time: 6 h|Warranty: 1 year"),
 ("Organic Vermicompost", "organic-products", 499, 10, 250, "Malabar Organics", "vermicompost,compost,organic,manure", 1, "vermicompost", "Nutrient-rich earthworm compost that improves soil structure and microbial activity.", "Pack: 10 kg|Organic carbon: 18%|Moisture: 20%|Certification: NPOP"),
 ("Organic Pesticide - Panchagavya Spray", "organic-products", 650, 12, 90, "Malabar Organics", "organic pesticide,bio,natural", 1, "organic-pesticide", "Ready-to-use fermented botanical spray that boosts plant immunity and repels common pests.", "Pack: 1 L|Dose: 30 ml / L|Origin: Cow-based|Certification: NPOP"),
 ("Neem Cake Organic Manure", "organic-products", 320, 8, 160, "Multiplex", "neem cake,manure,organic", 1, "neem-cake", "Soil conditioner that suppresses nematodes and supplies slow-release nitrogen.", "Pack: 5 kg|N: 4.5%|Form: Powder|Use: Basal"),
 ("Trichoderma Viride Bio-Fungicide", "organic-products", 390, 10, 100, "Multiplex", "trichoderma,bio fungicide,organic", 1, "trichoderma", "Beneficial fungus for seed treatment and soil application against wilt and root rot.", "Pack: 1 kg|CFU: 2x10^6 / g|Dose: 4 g / kg seed|Shelf life: 12 months"),
 ("Cattle Feed Pellets", "animal-feed", 1280, 5, 90, "Godrej Agrovet", "cattle feed,dairy,pellets", 0, "cattle-feed", "Balanced 20% protein pellets to improve milk yield and fat in cows and buffaloes.", "Pack: 50 kg|Protein: 20%|Form: Pellet|Fibre: 9%"),
 ("Poultry Layer Feed", "animal-feed", 980, 6, 110, "Suguna", "poultry,layer feed,chicken", 0, "poultry-feed", "Complete mash for laying hens with calcium and vitamin premix for strong shells.", "Pack: 25 kg|Protein: 17%|Calcium: 3.5%|Form: Mash"),
 ("Mineral Mixture for Cattle", "animal-feed", 260, 10, 140, "Virbac", "mineral mixture,cattle,supplement", 0, "mineral-mixture", "Chelated mineral supplement that improves fertility and prevents deficiency disorders.", "Pack: 1 kg|Dose: 30 g / day|Form: Powder|Shelf life: 18 months"),
]

REVIEW_TEXT = [
    (5, "Excellent quality", "Product was exactly as described and delivered on time. Will order again."),
    (5, "Great value for money", "Better price than my local shop and the quality is genuine."),
    (4, "Good product", "Works well. Packaging could be slightly better but the product is good."),
    (4, "Reliable seller", "Seller responded quickly and the delivery was within 4 days."),
    (5, "Very good results", "Saw a noticeable difference in my field within a few weeks."),
    (3, "Okay", "Decent product, delivery took a bit longer than expected."),
]
STREETS = ["Main Road", "Temple Street", "Bus Stand Road", "Canal Road", "Market Yard"]


def build(db_path=None, reset=True):
    db_path = db_path or Config.DATABASE
    if reset and os.path.exists(db_path):
        os.remove(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(open(Config.SCHEMA, encoding="utf-8").read())
    rnd = random.Random(42)
    now = datetime.now()
    pw = generate_password_hash

    db.execute("INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
               ("AgroConnect Admin", "admin@agroconnect.com", "9876500000", pw("admin123"), "admin"))
    for c in CATEGORIES:
        db.execute("INSERT INTO categories (name,slug,image,description) VALUES (?,?,?,?)", c)
    cat_id = {c[1]: i + 1 for i, c in enumerate(CATEGORIES)}

    seller_ids = []
    for i, (name, email, biz, loc) in enumerate(SELLERS):
        password = "seller123" if email == "seller@agroconnect.com" else "seller123"
        uid = db.execute("INSERT INTO users (name,email,phone,password,role,created_at) VALUES (?,?,?,?,?,?)",
                         (name, email, f"98{rnd.randint(10000000, 99999999)}", pw(password), "seller",
                          (now - timedelta(days=300 - i * 12)).isoformat(" ", "seconds"))).lastrowid
        sid = db.execute("INSERT INTO sellers (user_id,business_name,location,verified,bio) VALUES (?,?,?,?,?)",
                         (uid, biz, loc, 1, f"{biz} supplies genuine agricultural inputs to farmers across South and Central India.")).lastrowid
        seller_ids.append(sid)

    cust_ids = []
    for i, (name, email, district, state, pin) in enumerate(CUSTOMERS):
        uid = db.execute("INSERT INTO users (name,email,phone,password,role,created_at) VALUES (?,?,?,?,?,?)",
                         (name, email, f"9{rnd.choice('6789')}{rnd.randint(10000000, 99999999)}", pw("customer123"), "customer",
                          (now - timedelta(days=250 - i * 15)).isoformat(" ", "seconds"))).lastrowid
        db.execute("INSERT INTO addresses (user_id,line1,village,district,state,pincode,is_default) VALUES (?,?,?,?,?,?,1)",
                   (uid, f"{rnd.randint(1, 60)}-{rnd.randint(1, 99)}, {rnd.choice(STREETS)}", f"{district} Town", district, state, pin))
        cust_ids.append(uid)

    # Products: first 6 belong to the demo seller (GreenGrow Agro); rest spread across sellers.
    for i, p in enumerate(P):
        name, cat, price, disc, stock, brand, tags, organic, img, desc, specs = p
        sid = seller_ids[0] if i % 5 == 0 else seller_ids[(i * 3) % len(seller_ids)]
        db.execute("""INSERT INTO products (name,description,category_id,seller_id,price,discount,stock,image,brand,tags,organic,specs,status,created_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'approved', ?)""",
                   (name, desc, cat_id[cat], sid, price, disc, stock, f"products/{img}.jpg", brand, tags, organic, specs,
                    (now - timedelta(days=rnd.randint(2, 200))).isoformat(" ", "seconds")))
    # a couple of pending items so the admin approval flow has data
    db.execute("""INSERT INTO products (name,description,category_id,seller_id,price,discount,stock,image,brand,tags,organic,specs,status)
                  VALUES ('Groundnut Seeds - TAG 24','Bold-kernel groundnut variety for kharif.',?,?,?,?,?,?,?,?,?,?,'pending')""",
               (cat_id["seeds"], seller_ids[0], 1450, 8, 60, "products/groundnut-seeds.jpg", "Kisan Gold", "groundnut,peanut", 0, "Pack: 10 kg|Maturity: 105 days"))
    n_products = len(P)

    # reviews (20)
    for i in range(20):
        r = REVIEW_TEXT[i % len(REVIEW_TEXT)]
        db.execute("INSERT INTO reviews (product_id,user_id,rating,title,body,created_at) VALUES (?,?,?,?,?,?)",
                   (rnd.randint(1, n_products), cust_ids[i % len(cust_ids)], r[0], r[1], r[2],
                    (now - timedelta(days=rnd.randint(1, 120))).isoformat(" ", "seconds")))
    for pid in range(1, n_products + 1):
        row = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE product_id=?", (pid,)).fetchone()
        base_cnt = rnd.randint(40, 320)
        rating = round(rnd.uniform(4.1, 4.8), 1)
        if row[0]:
            rating = round((rating * base_cnt + row[1] * row[0]) / (base_cnt + row[0]), 1)
        db.execute("UPDATE products SET rating=?, reviews_count=? WHERE id=?", (rating, base_cnt + row[0], pid))

    # orders (20)
    statuses = ["Order Placed", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered"]
    methods = ["Cash on Delivery", "UPI", "Credit/Debit Card"]
    for i in range(20):
        uid = cust_ids[0] if i < 6 else rnd.choice(cust_ids)
        addr = db.execute("SELECT * FROM addresses WHERE user_id=?", (uid,)).fetchone()
        user = db.execute("SELECT name,phone FROM users WHERE id=?", (uid,)).fetchone()
        created = (now - timedelta(days=rnd.randint(1, 170), hours=rnd.randint(0, 20))).isoformat(" ", "seconds")
        items = rnd.sample(range(1, n_products + 1), rnd.randint(1, 3))
        lines, total = [], 0
        for pid in items:
            pr = db.execute("SELECT name,price,discount FROM products WHERE id=?", (pid,)).fetchone()
            sp = round(pr[1] * (100 - pr[2]) / 100); q = rnd.randint(1, 3)
            lines.append((pid, pr[0], q, sp)); total += sp * q
        delivery = 0 if total >= Config.FREE_DELIVERY_ABOVE else Config.DELIVERY_FEE
        total += delivery + round(total * Config.TAX_PERCENT / 100)
        status = statuses[min(5, i % 7)] if i % 7 < 6 else "Delivered"
        oid = db.execute("""INSERT INTO orders (user_id,total_amount,status,payment_method,customer_name,phone,shipping_address,created_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                         (uid, total, status, methods[i % 3], user[0], user[1],
                          f"{addr[2]}, {addr[3]}, {addr[4]}, {addr[5]} - {addr[6]}", created)).lastrowid
        db.execute("UPDATE orders SET order_number=? WHERE id=?", (f"AGC{datetime.fromisoformat(created):%Y%m}{oid:05d}", oid))
        for pid, nm, q, sp in lines:
            db.execute("INSERT INTO order_items (order_id,product_id,name,quantity,price) VALUES (?,?,?,?,?)", (oid, pid, nm, q, sp))
        db.execute("INSERT INTO payments (order_id,method,status,reference,amount,created_at) VALUES (?,?,?,?,?,?)",
                   (oid, methods[i % 3], "Pending (COD)" if i % 3 == 0 and status != "Delivered" else "Paid",
                    f"TXN{rnd.randint(10**9, 10**10 - 1)}" if i % 3 else "COD", total, created))
    db.execute("INSERT INTO wishlist (user_id,product_id) VALUES (?,?)", (cust_ids[0], 7))
    db.commit(); db.close()
    return db_path


if __name__ == "__main__":
    print("Database created at", build())
    print("Demo logins: customer@/seller@/admin@agroconnect.com  (customer123 / seller123 / admin123)")
