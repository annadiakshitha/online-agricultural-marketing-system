"""Download a real, subject-matched Unsplash photo for every image in config.IMAGE_QUERIES.

Setup (free, 2 minutes):
  1. Create an app at https://unsplash.com/developers  -> copy the "Access Key"
  2. Windows PowerShell:   $env:UNSPLASH_ACCESS_KEY="your_key"
     macOS / Linux:        export UNSPLASH_ACCESS_KEY="your_key"
  3. python download_images.py

Options:
  --pick N      use the N-th search result (default 1). Use with --only/--force to swap a photo.
  --only TEXT   only files whose path contains TEXT (e.g. --only tomato --pick 2 --force)
  --force       re-download even if the file already exists
  --checklist   just rebuild image-checklist.html (product -> filename -> photo) and exit

Unsplash's demo limit is 50 requests/hour; files you already have are skipped, so if it stops
at the limit just run it again an hour later. Photographer credits go to
static/images/CREDITS.txt (please keep it - Unsplash asks for attribution).
"""
import argparse, html, json, os, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request
from config import IMAGE_QUERIES, Config, BASE_DIR

ROOT = os.path.join(BASE_DIR, "static", "images")
UA = {"User-Agent": "AgroConnect-image-fetch/2.0"}


def get(url, headers=None, binary=False):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    return data if binary else json.loads(data)


def search_photo(query, key, pick):
    q = urllib.parse.urlencode({"query": query, "per_page": max(pick, 5), "orientation": "landscape", "content_filter": "high"})
    results = get(f"https://api.unsplash.com/search/photos?{q}", {"Authorization": f"Client-ID {key}"}).get("results", [])
    if not results:
        return None
    p = results[min(pick, len(results)) - 1]
    return dict(url=p["urls"]["raw"] + "&w=1600&q=80&fit=crop&auto=format", page=p["links"]["html"], who=p["user"]["name"])


def build_checklist():
    """HTML contact sheet: confirm by eye that every product matches its photo."""
    rows = []
    if os.path.exists(Config.DATABASE):
        db = sqlite3.connect(Config.DATABASE)
        rows += [("Product", n, i) for n, i in db.execute("SELECT name, image FROM products WHERE image LIKE 'products/%' ORDER BY id")]
        rows += [("Category", n, i) for n, i in db.execute("SELECT name, image FROM categories ORDER BY id")]
    rows += [("Blog", os.path.basename(k), k) for k in IMAGE_QUERIES if k.startswith("blog/")]
    cells = []
    for kind, name, rel in rows:
        art = "art/" + os.path.splitext(rel)[0] + ".svg"
        if os.path.exists(os.path.join(ROOT, rel)): img = f'<img src="static/images/{rel}" alt="">'
        elif os.path.exists(os.path.join(ROOT, art)): img = f'<img src="static/images/{art}" alt="">'
        else: img = '<div class="miss">no image yet</div>'
        cells.append(f'<figure>{img}<figcaption><b>{html.escape(name)}</b><br><small>{kind} &rarr; {html.escape(rel)}<br>'
                     f'search: {html.escape(IMAGE_QUERIES.get(rel, ""))}</small></figcaption></figure>')
    page = ("<!doctype html><meta charset=utf-8><title>AgroConnect image checklist</title>"
            "<style>body{background:#050805;color:#fff;font:14px Inter,Arial;margin:24px}h1{color:#39D353}"
            ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}"
            "figure{margin:0;background:#101812;border:1px solid #26352B;border-radius:12px;overflow:hidden}"
            "img,.miss{width:100%;height:170px;object-fit:cover;display:grid;place-items:center;color:#A7B3AA;background:#0B120D}"
            "figcaption{padding:10px}small{color:#A7B3AA}</style><h1>Does every photo match its name?</h1>"
            "<p>If one is wrong: <code>python download_images.py --only FILENAME --pick 2 --force</code></p>"
            "<div class=g>" + "".join(cells) + "</div>")
    out = os.path.join(BASE_DIR, "image-checklist.html")
    open(out, "w", encoding="utf-8").write(page)
    print("Wrote", out, "- open it in your browser to review.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pick", type=int, default=1)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--checklist", action="store_true")
    a = ap.parse_args()
    if a.checklist:
        return build_checklist()

    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if not key:
        print("UNSPLASH_ACCESS_KEY is not set - see the top of this file.\n"
              "Until then the site shows labelled placeholders for products (never a wrong photo).", file=sys.stderr)
        return 1

    os.makedirs(ROOT, exist_ok=True)
    credits_path = os.path.join(ROOT, "CREDITS.txt")
    credits = open(credits_path, encoding="utf-8").read() if os.path.exists(credits_path) else ""
    ok = skipped = failed = 0
    for rel, query in IMAGE_QUERIES.items():
        if a.only and a.only not in rel:
            continue
        dest = os.path.join(ROOT, rel)
        if os.path.exists(dest) and not a.force:
            skipped += 1
            continue
        try:
            hit = search_photo(query, key, a.pick)
            if not hit:
                print("NO RESULT", rel, "-", query); failed += 1; continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(get(hit["url"], binary=True))
            credits += f"{rel}: photo by {hit['who']} on Unsplash - {hit['page']}\n"
            ok += 1; print("saved", rel, "<-", query, f"({hit['who']})")
            time.sleep(0.4)
        except urllib.error.HTTPError as e:
            failed += 1; print("FAILED", rel, e.code, e.reason, file=sys.stderr)
            if e.code in (403, 429):
                print("Rate limit reached - run again in an hour; finished files are kept.", file=sys.stderr); break
        except Exception as e:
            failed += 1; print("FAILED", rel, e, file=sys.stderr)
    with open(credits_path, "w", encoding="utf-8") as f:
        f.write(credits)
    print(f"Done: {ok} downloaded, {skipped} already present, {failed} failed.")
    build_checklist()


if __name__ == "__main__":
    sys.exit(main() or 0)
