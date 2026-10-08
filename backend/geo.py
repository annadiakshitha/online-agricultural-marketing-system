"""Small built-in gazetteer of Indian districts / cities (no external geocoding service needed)."""
import math

CITIES = {
    # Telangana
    "hyderabad": (17.385, 78.487), "warangal": (17.969, 79.594), "nalgonda": (17.057, 79.267), "medak": (18.047, 78.264),
    "karimnagar": (18.439, 79.129), "nizamabad": (18.673, 78.094), "khammam": (17.247, 80.151), "adilabad": (19.664, 78.532),
    "mahbubnagar": (16.749, 77.986), "rangareddy": (17.25, 78.1), "sangareddy": (17.62, 78.082), "siddipet": (18.102, 78.852), "suryapet": (17.14, 79.624),
    # Andhra Pradesh
    "guntur": (16.307, 80.437), "krishna": (16.188, 81.139), "vijayawada": (16.506, 80.648), "visakhapatnam": (17.687, 83.219),
    "kurnool": (15.828, 78.037), "anantapur": (14.682, 77.601), "chittoor": (13.217, 79.1), "nellore": (14.443, 79.987),
    "tirupati": (13.629, 79.419), "kadapa": (14.467, 78.824), "east godavari": (16.989, 82.248), "west godavari": (16.711, 81.095),
    "prakasam": (15.506, 80.05), "srikakulam": (18.295, 83.894), "kakinada": (16.989, 82.248), "eluru": (16.711, 81.095),
    # Karnataka
    "bengaluru": (12.972, 77.595), "bangalore": (12.972, 77.595), "mysuru": (12.296, 76.639), "mysore": (12.296, 76.639), "mandya": (12.522, 76.895),
    "hubballi": (15.365, 75.124), "belagavi": (15.85, 74.498), "mangaluru": (12.914, 74.856), "kalaburagi": (17.33, 76.834),
    "tumakuru": (13.341, 77.101), "davanagere": (14.464, 75.922), "shivamogga": (13.93, 75.568), "raichur": (16.208, 77.346), "ballari": (15.139, 76.921),
    # Maharashtra
    "mumbai": (19.076, 72.878), "pune": (18.52, 73.857), "nashik": (19.998, 73.79), "nagpur": (21.146, 79.088), "aurangabad": (19.876, 75.343),
    "kolhapur": (16.705, 74.243), "solapur": (17.66, 75.906), "ahmednagar": (19.095, 74.748), "satara": (17.681, 74.018),
    "latur": (18.409, 76.56), "jalgaon": (21.008, 75.563), "amravati": (20.937, 77.78),
    # Tamil Nadu
    "chennai": (13.083, 80.271), "coimbatore": (11.017, 76.956), "madurai": (9.925, 78.12), "salem": (11.664, 78.146),
    "tiruchirappalli": (10.79, 78.705), "erode": (11.341, 77.717), "thanjavur": (10.787, 79.138),
}
STATES = {
    "telangana": (17.85, 79.1), "andhra pradesh": (15.9, 79.7), "karnataka": (14.5, 75.7), "maharashtra": (19.4, 76.0),
    "tamil nadu": (11.1, 78.7), "kerala": (10.5, 76.5), "gujarat": (22.7, 71.6), "punjab": (31.0, 75.3), "madhya pradesh": (23.5, 78.0),
    "uttar pradesh": (26.8, 80.9), "rajasthan": (26.9, 74.2), "haryana": (29.0, 76.0), "odisha": (20.5, 84.5),
    "west bengal": (23.0, 87.9), "bihar": (25.6, 85.1), "chhattisgarh": (21.3, 81.8),
}
HUBS = ["Hyderabad", "Bengaluru", "Pune", "Chennai", "Nagpur", "Mumbai", "Vijayawada"]


def locate(*names):
    """First match among place names (district/city first, then state). Returns (lat, lng, label) or None."""
    for n in names:
        key = (n or "").strip().lower()
        for suffix in (" town", " district", " city", " rural", " urban"):
            if key.endswith(suffix):
                key = key[: -len(suffix)]
        if key in CITIES:
            return (*CITIES[key], key.title())
    for n in names:
        key = (n or "").strip().lower()
        if key in STATES:
            return (*STATES[key], key.title())
    return None


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def nearest_hub(pt):
    return min(HUBS, key=lambda h: km(pt, CITIES[h.lower()]))
