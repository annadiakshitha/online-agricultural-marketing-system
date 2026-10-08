"""Generates the bundled product artwork (static/images/art/**.svg).
Run:  python tools/make_art.py      (only needed if you edit the artwork)
Every file shows its own subject - tomato art for tomato products, a tractor for the tractor, etc.
Real photos downloaded with download_images.py automatically take priority over this artwork."""
import os, math, random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "images", "art")
W, H = 800, 600

def grad(i, stops, kind="radial", extra=""):
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    if kind == "radial":
        return f'<radialGradient id="{i}" cx=".35" cy=".3" r=".8" {extra}>{st}</radialGradient>'
    return f'<linearGradient id="{i}" x1="0" y1="0" x2="0" y2="1" {extra}>{st}</linearGradient>'

def lin(i, a, b, horizontal=True):
    d = 'x1="0" y1="0" x2="1" y2="0"' if horizontal else 'x1="0" y1="0" x2="0" y2="1"'
    return f'<linearGradient id="{i}" {d}><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'

def wrap(body, defs="", tint="#39D353", ground=True):
    shadow = '<ellipse cx="400" cy="508" rx="250" ry="26" fill="#000" opacity=".5" filter="url(#blur)"/>' if ground else ""
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#fff" opacity=".07"/>' for x in range(30, 800, 40) for y in range(30, 600, 40))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img"><defs>'
            f'<radialGradient id="bg" cx=".5" cy=".42" r=".75"><stop offset="0" stop-color="{tint}" stop-opacity=".30"/><stop offset=".55" stop-color="#0B120D"/><stop offset="1" stop-color="#050805"/></radialGradient>'
            f'<radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{tint}" stop-opacity=".35"/><stop offset="1" stop-color="{tint}" stop-opacity="0"/></radialGradient>'
            f'<filter id="blur"><feGaussianBlur stdDeviation="9"/></filter>{defs}</defs>'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>{dots}'
            f'<circle cx="400" cy="290" r="270" fill="url(#halo)"/>{shadow}{body}</svg>')

def leaf(x, y, rot, s=1.0, c1="#4ade80", c2="#15803d"):
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})"><path d="M0 0C40-30 110-30 150 0C110 30 40 30 0 0Z" fill="{c1}"/>'
            f'<path d="M0 0C40-30 110-30 150 0C110 30 40 30 0 0Z" fill="url(#leafshade)" opacity=".5"/>'
            f'<path d="M5 0H140" stroke="{c2}" stroke-width="3" opacity=".7"/></g>')

LEAF_DEF = '<linearGradient id="leafshade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></linearGradient>'

def ball(cx, cy, r, c1, c2, c3, gid):
    return (f'<radialGradient id="{gid}" cx=".35" cy=".3" r=".85"><stop offset="0" stop-color="{c1}"/><stop offset=".55" stop-color="{c2}"/><stop offset="1" stop-color="{c3}"/></radialGradient>',
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/><ellipse cx="{cx-r*.35}" cy="{cy-r*.42}" rx="{r*.22}" ry="{r*.12}" fill="#fff" opacity=".35" transform="rotate(-30 {cx-r*.35} {cy-r*.42})"/>')

def calyx(cx, cy, r):
    pts = ""
    for k in range(5):
        a = k * 72 - 90
        pts += f'<path d="M0 0C{r*.15} {-r*.1} {r*.45} {-r*.12} {r*.6} {-r*.02}C{r*.4} {r*.12} {r*.2} {r*.1} 0 0Z" fill="#3fae49" transform="translate({cx},{cy}) rotate({a})"/>'
    return pts + f'<rect x="{cx-4}" y="{cy-r*.35}" width="8" height="{r*.3}" rx="4" fill="#2f8a3a"/>'

def seeds_scatter(color="#f3e3b5", n=14, seed=1, box=(250, 470, 550, 520)):
    r = random.Random(seed); out = ""
    for _ in range(n):
        x = r.uniform(box[0], box[2]); y = r.uniform(box[1], box[3]); a = r.uniform(0, 180)
        out += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="9" ry="5.5" fill="{color}" stroke="#00000033" transform="rotate({a:.0f} {x:.0f} {y:.0f})"/>'
    return out

# ---------------------------------------------------------------- crops
def m_tomato(seeds=False):
    d, b = LEAF_DEF, leaf(400, 220, -150, 1.1) + leaf(400, 220, -30, 1.1)
    for (x, y, r, g) in [(400, 330, 128, "t1"), (545, 392, 84, "t2"), (262, 396, 74, "t3")]:
        gd, gb = ball(x, y, r, "#ff8a7a", "#e53935", "#8e1b17", g); d += gd; b += gb + calyx(x, y - r * .86, r * .75)
    return d, b + (seeds_scatter(seed=3) if seeds else "")

def pod(x, y, rot, s, c1, c2, gid):
    d = lin(gid, c1, c2)
    b = (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})"><path d="M-26 0C-40 90-18 190 42 262C22 190 30 90 26 0Z" fill="url(#{gid})"/>'
         '<path d="M-14 20C-20 90 0 160 30 220" stroke="#fff" stroke-opacity=".35" stroke-width="6" fill="none" stroke-linecap="round"/>'
         '<path d="M-26 0C-20-14 20-14 26 0C20 10-20 10-26 0Z" fill="#2f9e44"/><path d="M0-6C4-30 14-44 30-50" stroke="#2f9e44" stroke-width="9" fill="none" stroke-linecap="round"/></g>')
    return d, b

def m_chilli(seeds=False):
    d = b = ""
    for i, (x, y, r, s, c1, c2) in enumerate([(330, 230, 14, 1.05, "#ff5a4a", "#a50f0f"), (440, 215, -6, 1.2, "#ff3d2e", "#8e0b0b"), (545, 245, -22, 1.0, "#ff6a55", "#b01212")]):
        gd, gb = pod(x, y, r, s, c1, c2, f"p{i}"); d += gd; b += gb
    return d, b + (seeds_scatter(seed=5) if seeds else "")

def m_maize(seeds=False):
    d = LEAF_DEF + lin("cob", "#ffe066", "#f59f00") + lin("husk", "#7ddf64", "#2b8a3e", False)
    b = '<g transform="translate(400,300) rotate(12)">'
    b += '<path d="M-110 120C-170 20-150-90-40-150C-60-60-70 40-30 130Z" fill="url(#husk)"/><path d="M110 120C170 20 150-90 40-150C60-60 70 40 30 130Z" fill="url(#husk)"/>'
    b += '<rect x="-62" y="-170" width="124" height="300" rx="62" fill="url(#cob)"/>'
    for r_ in range(11):
        for c_ in range(5):
            x = -42 + c_ * 21 + (r_ % 2) * 10; y = -140 + r_ * 24
            b += f'<ellipse cx="{x}" cy="{y}" rx="10" ry="11" fill="#ffd43b" stroke="#e8a900" stroke-width="1.5"/><ellipse cx="{x-3}" cy="{y-4}" rx="3" ry="4" fill="#fff" opacity=".5"/>'
    b += '<path d="M-90 140C-60 60-20 40 0 -20C20 40 60 60 90 140Z" fill="url(#husk)" opacity=".95"/></g>'
    return d, b + (seeds_scatter("#ffd43b", 16, 7) if seeds else "")

def m_rice():
    d = lin("gr", "#f6d365", "#d99a1d")
    b = ""
    for (x0, bend, h) in [(330, -90, 330), (420, 60, 360), (510, 140, 320)]:
        b += f'<path d="M{x0} 500C{x0} 420 {x0+bend*.3} 330 {x0+bend} {500-h}" stroke="#7fb069" stroke-width="7" fill="none" stroke-linecap="round"/>'
        for k in range(15):
            t = k / 14; px = x0 + bend * (.55 + .45 * t) + math.sin(t * 5) * 8; py = 500 - h + 25 + t * 140
            for side in (-1, 1):
                b += f'<ellipse cx="{px + side*12:.0f}" cy="{py:.0f}" rx="7" ry="16" fill="url(#gr)" stroke="#b7791f" stroke-width="1.5" transform="rotate({side*22} {px:.0f} {py:.0f})"/>'
    b += leaf(300, 505, -75, 1.5, "#7fb069", "#2f6f3a") + leaf(560, 505, -105, 1.5, "#7fb069", "#2f6f3a")
    b += seeds_scatter("#f5e6b8", 26, 2, (280, 495, 530, 535))
    return d + LEAF_DEF, b

def m_cotton():
    b = '<path d="M400 520V300" stroke="#6b8e23" stroke-width="10" stroke-linecap="round"/>'
    b += leaf(400, 430, -150, 1.0, "#6bbf59", "#2f7d32") + leaf(400, 400, -30, 1.0, "#6bbf59", "#2f7d32")
    for (cx, cy, s) in [(400, 230, 1.25), (300, 330, .95), (505, 320, .95)]:
        b += f'<g transform="translate({cx},{cy}) scale({s})"><path d="M-62 40L0 110L62 40L40-10L-40-10Z" fill="#7a5230"/>'
        for (x, y, r) in [(0, -50, 52), (-52, -10, 48), (52, -10, 48), (-30, 28, 46), (30, 28, 46), (0, -4, 50)]:
            b += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fafafa"/><circle cx="{x-r*.25}" cy="{y-r*.25}" r="{r*.55}" fill="#fff"/><circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#d8dee9" stroke-width="2"/>'
        b += '</g>'
    return LEAF_DEF, b

def m_potato(seeds=False):
    d, b = LEAF_DEF + ball(0, 0, 1, "#e9c58a", "#c08a4a", "#7a4f24", "pg")[0], ""
    for (x, y, rx, ry, rot) in [(400, 360, 150, 105, -8), (270, 410, 100, 72, 18), (545, 410, 105, 76, -20), (380, 250, 92, 66, 25)]:
        b += f'<g transform="translate({x},{y}) rotate({rot})"><ellipse rx="{rx}" ry="{ry}" fill="url(#pg)" transform="scale(1)"/>'
        b += f'<ellipse cx="{-rx*.3}" cy="{-ry*.4}" rx="{rx*.28}" ry="{ry*.13}" fill="#fff" opacity=".25"/>'
        for (ex, ey) in [(-.4, .1), (.2, -.3), (.45, .25), (0, .35)]:
            b += f'<ellipse cx="{ex*rx}" cy="{ey*ry}" rx="6" ry="4" fill="#5b3a1a" opacity=".8"/>'
        b += '</g>'
    b += leaf(390, 205, -120, .9) + leaf(400, 210, -40, .9)
    return d, b

def m_okra():
    d = lin("ok", "#8ce99a", "#2b8a3e", False); b = ""
    for (x, y, rot, s) in [(300, 190, 18, 1.0), (390, 170, 4, 1.15), (480, 190, -10, 1.05), (570, 215, -22, .95)]:
        b += (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})"><path d="M-22 0C-34 110-14 230 6 330C26 230 34 110 22 0Z" fill="url(#ok)"/>'
              '<path d="M0 0C0 110 4 230 6 330" stroke="#1f6f33" stroke-width="3" opacity=".6" fill="none"/><path d="M-12 10C-16 110 -6 220 4 300" stroke="#fff" stroke-opacity=".3" stroke-width="5" fill="none"/>'
              '<path d="M-26 0C-22-14 22-14 26 0Z" fill="#2f8a3a"/><rect x="-5" y="-34" width="10" height="26" rx="5" fill="#2f8a3a"/></g>')
    return d, b

def m_groundnut():
    b = leaf(380, 300, -160, 1.0) + leaf(420, 300, -20, 1.0)
    for (x, y, rot, s) in [(330, 400, -25, 1.15), (470, 430, 18, 1.05), (410, 340, 70, 1.0)]:
        b += (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})"><path d="M-95 0C-95-45-40-52 0-26C40-52 95-45 95 0C95 45 40 52 0 26C-40 52-95 45-95 0Z" fill="#d8a86a" stroke="#a9742f" stroke-width="3"/>')
        for i in range(-4, 5):
            b += f'<path d="M{i*20} -28L{i*20+10} 28" stroke="#b9854a" stroke-width="2" opacity=".7"/>'
        b += '<ellipse cx="-50" cy="-18" rx="26" ry="8" fill="#fff" opacity=".25"/></g>'
    return LEAF_DEF, b

# ---------------------------------------------------------------- inputs
def m_sack(label, c1, c2, granule="#f1f3f5", sub=""):
    d = lin("sk", c1, c2, False)
    b = (f'<g transform="translate(400,300)"><path d="M-130-150L130-150L150-120L150 170C150 195 130 205 100 205H-100C-130 205-150 195-150 170V-120Z" fill="url(#sk)"/>'
         '<path d="M-130-150L130-150L150-120H-150Z" fill="#000" opacity=".22"/><path d="M-120-140H120" stroke="#fff" stroke-opacity=".35" stroke-width="3" stroke-dasharray="6 8"/>'
         '<rect x="-100" y="-70" width="200" height="150" rx="14" fill="#fff"/>'
         f'<text y="10" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="800" font-size="{54 if len(label) < 6 else 40}" fill="{c2}">{label}</text>'
         f'<text y="52" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="600" font-size="22" fill="#495057">{sub}</text>'
         '<rect x="-100" y="-70" width="200" height="14" rx="7" fill="#39D353"/></g>')
    r = random.Random(4)
    for _ in range(46):
        x = r.gauss(400, 85); y = 505 - abs(r.gauss(0, 14)); b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.uniform(4,7):.1f}" fill="{granule}" stroke="#00000030"/>'
    return "" if False else d, b

def m_bottle(color, label, sub="", leaves=False, cap="#212529", liquid=None):
    d = lin("bt", color, "#000", True)
    b = (f'<g transform="translate(400,320)"><rect x="-26" y="-205" width="52" height="46" rx="8" fill="{cap}"/><rect x="-30" y="-165" width="60" height="22" rx="6" fill="{cap}" opacity=".85"/>'
         f'<path d="M-30-143H30C30-110 100-96 100-50V190C100 215 86 225 66 225H-66C-86 225-100 215-100 190V-50C-100-96-30-110-30-143Z" fill="{liquid or color}" opacity=".95"/>'
         '<path d="M-84-40V190" stroke="#fff" stroke-opacity=".3" stroke-width="10" stroke-linecap="round"/>'
         '<rect x="-100" y="-20" width="200" height="150" fill="#fff"/>'
         f'<rect x="-100" y="-20" width="200" height="22" fill="{color}"/>'
         f'<text y="60" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="800" font-size="{34 if len(label) < 8 else 25}" fill="#212529">{label}</text>'
         f'<text y="96" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="600" font-size="20" fill="#495057">{sub}</text></g>')
    if leaves:
        b += neem_sprig(60, 470, -12, .85) + neem_sprig(745, 485, 192, .8)
    return d, b

def neem_sprig(x, y, rot, s=1.0):
    out = f'<g transform="translate({x},{y}) rotate({rot}) scale({s})"><path d="M0 0C60-10 130-10 200 0" stroke="#4a7c2f" stroke-width="6" fill="none"/>'
    for i in range(7):
        px = 25 + i * 26
        out += f'<ellipse cx="{px}" cy="-17" rx="10" ry="22" fill="#5cb85c" transform="rotate(-25 {px} -17)"/><ellipse cx="{px}" cy="17" rx="10" ry="22" fill="#4ca64c" transform="rotate(25 {px} 17)"/>'
    return out + '<ellipse cx="205" cy="0" rx="22" ry="10" fill="#5cb85c"/></g>'

def m_neem_oil():
    d, b = m_bottle("#2f9e44", "NEEM OIL", "1500 PPM", True, cap="#f59f00", liquid="#c9a227")
    return d, b

def m_tools():
    d = lin("steel", "#dee2e6", "#868e96") + lin("hand", "#f59f00", "#e8590c")
    b = ('<g transform="translate(300,300) rotate(-22)"><path d="M-40-150C-70-90-60-40 0 0C60-40 70-90 40-150Z" fill="url(#steel)" stroke="#495057" stroke-width="3"/><rect x="-14" y="0" width="28" height="40" fill="#868e96"/><rect x="-22" y="40" width="44" height="170" rx="22" fill="url(#hand)"/></g>'
         '<g transform="translate(500,310) rotate(18)"><rect x="-6" y="-170" width="12" height="150" fill="#adb5bd"/>'
         + "".join(f'<rect x="{-34+i*23}" y="-190" width="9" height="90" rx="4" fill="url(#steel)" stroke="#495057"/>' for i in range(4)) +
         '<rect x="-22" y="-20" width="44" height="40" fill="#868e96"/><rect x="-22" y="20" width="44" height="160" rx="22" fill="url(#hand)"/></g>'
         '<g transform="translate(410,470) rotate(-8)"><path d="M-110 0L110-26L110-6L-110 20Z" fill="url(#steel)" stroke="#495057"/><circle cx="-90" cy="8" r="9" fill="#e8590c"/></g>')
    return d, b

def m_shears():
    d = lin("steel", "#e9ecef", "#868e96")
    b = ('<g transform="translate(400,300) rotate(-35)"><path d="M0 0C40-60 60-140 50-230C30-170-6-80-30 0Z" fill="url(#steel)" stroke="#495057" stroke-width="3"/>'
         '<path d="M0 0C-40-60-60-140-50-230C-30-170 6-80 30 0Z" fill="#ced4da" stroke="#495057" stroke-width="3"/>'
         '<circle cx="0" cy="4" r="16" fill="#e8590c"/><path d="M-16 20C-110 90-120 190-60 230C-40 190-30 100 4 40Z" fill="#e8590c"/><path d="M16 20C110 90 120 190 60 230C40 190 30 100-4 40Z" fill="#212529"/></g>')
    return d, b

def tank(x, y, w, h, c1, c2, gid):
    return lin(gid, c1, c2), f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="url(#{gid})"/><rect x="{x+16}" y="{y+22}" width="14" height="{h-44}" rx="7" fill="#fff" opacity=".25"/>'

def m_hand_sprayer(battery=False, knap=False):
    d, b = tank(290, 200, 220, 300, "#2f9e44", "#0b6b2d", "tk")
    b += '<rect x="360" y="165" width="80" height="45" rx="10" fill="#212529"/><rect x="396" y="120" width="8" height="50" fill="#868e96"/><rect x="330" y="110" width="140" height="14" rx="7" fill="#212529"/>'
    b += '<path d="M440 190C560 160 600 230 610 320" stroke="#212529" stroke-width="12" fill="none"/><path d="M600 320L650 330L650 370L600 360Z" fill="#212529"/><path d="M652 345L730 330M652 350L735 350M652 356L730 372" stroke="#74c0fc" stroke-width="4" stroke-dasharray="6 8"/>'
    b += '<rect x="318" y="300" width="164" height="110" rx="12" fill="#fff"/><text x="400" y="368" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="34" fill="#0b6b2d">SPRAY</text>'
    return d, b

def m_knapsack(battery=False):
    d, b = tank(265, 140, 270, 340, "#2f9e44" if not battery else "#f59f00", "#0b6b2d" if not battery else "#c2410c", "tk")
    b += '<rect x="370" y="112" width="60" height="34" rx="8" fill="#212529"/>'
    b += '<path d="M290 190C230 260 235 380 295 450" stroke="#212529" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M510 190C570 260 565 380 505 450" stroke="#212529" stroke-width="22" fill="none" stroke-linecap="round"/>'
    b += '<path d="M535 330C620 330 650 380 700 440" stroke="#212529" stroke-width="10" fill="none"/><rect x="690" y="430" width="60" height="14" rx="7" fill="#868e96" transform="rotate(35 720 437)"/><path d="M742 470L790 520M752 462L800 500M730 480L770 540" stroke="#74c0fc" stroke-width="4" stroke-dasharray="5 8"/>'
    if battery:
        b += '<rect x="330" y="300" width="140" height="90" rx="12" fill="#212529"/><path d="M405 312L372 358H398L390 384L428 336H402Z" fill="#39D353"/>'
    else:
        b += '<rect x="320" y="290" width="160" height="110" rx="12" fill="#fff"/><text x="400" y="355" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="30" fill="#0b6b2d">16 L</text>'
    return d, b

def m_drip():
    d = ""
    b = '<rect x="90" y="470" width="620" height="60" rx="30" fill="#5f3b1e"/><rect x="90" y="470" width="620" height="14" rx="7" fill="#7a4f2a"/>'
    b += '<path d="M90 300C230 280 330 330 450 300C560 272 640 320 710 300" stroke="#1b1f23" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M90 292C230 272 330 322 450 292" stroke="#fff" stroke-opacity=".18" stroke-width="5" fill="none"/>'
    for i, x in enumerate([170, 290, 410, 530, 640]):
        y = 300 + (math.sin(x / 60) * 10)
        b += f'<rect x="{x-6}" y="{y+8:.0f}" width="12" height="28" rx="4" fill="#39D353"/><path d="M{x} {y+60:.0f}C{x-14} {y+84:.0f} {x-14} {y+100:.0f} {x} {y+104:.0f}C{x+14} {y+100:.0f} {x+14} {y+84:.0f} {x} {y+60:.0f}Z" fill="#74c0fc"/>'
        b += f'<path d="M{x} 470V430" stroke="#4ade80" stroke-width="6" stroke-linecap="round"/>' + leaf(x, 440, -150, .28) + leaf(x, 440, -30, .28)
    return LEAF_DEF, b

def m_sprinkler():
    b = '<rect x="380" y="330" width="40" height="170" rx="8" fill="#495057"/><rect x="360" y="300" width="80" height="44" rx="12" fill="#212529"/><rect x="345" y="478" width="110" height="30" rx="10" fill="#343a40"/>'
    b += '<rect x="410" y="290" width="86" height="22" rx="8" fill="#39D353" transform="rotate(-20 410 300)"/>'
    for k, (a, r) in enumerate([(-38, 260), (-22, 300), (-8, 330), (8, 330), (22, 300), (38, 260)]):
        rad = math.radians(a - 90 + 30)
        for j in range(9):
            t = j / 8; x = 470 + math.cos(rad) * r * t * 1.1; y = 300 - math.sin(abs(rad) + .6) * r * t * .9 + t * t * 120
            b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{4+ (1-t)*3:.1f}" fill="#74c0fc" opacity="{0.95-t*.5:.2f}"/>'
    return "", b

def m_pipe():
    b = ""
    for i in range(7):
        b += f'<ellipse cx="400" cy="{330-i*0}" rx="{250-i*26}" ry="{190-i*20}" fill="none" stroke="#{"14171a" if i%2==0 else "22272c"}" stroke-width="30"/>'
    b += '<ellipse cx="400" cy="330" rx="250" ry="190" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="3" transform="translate(0,-14)"/><path d="M640 360C690 400 740 410 790 400" stroke="#14171a" stroke-width="30" fill="none" stroke-linecap="round"/>'
    b += '<text x="400" y="340" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="34" fill="#39D353">HDPE 32 mm</text>'
    return "", b

def m_film():
    d = lin("fm", "#c0c6cc", "#4b5359", False)
    b = '<path d="M150 380L650 380L690 330L190 330Z" fill="#1c2227"/>'
    b += '<rect x="240" y="170" width="380" height="200" fill="url(#fm)"/><ellipse cx="240" cy="270" rx="46" ry="100" fill="#dfe3e6" stroke="#868e96" stroke-width="3"/><ellipse cx="240" cy="270" rx="16" ry="34" fill="#212529"/><ellipse cx="620" cy="270" rx="46" ry="100" fill="#adb5bd"/>'
    b += '<path d="M600 370C640 400 700 410 760 400L730 480L170 480L200 410Z" fill="url(#fm)" opacity=".9"/>'
    for x in (300, 420, 540, 650):
        b += f'<ellipse cx="{x}" cy="440" rx="22" ry="9" fill="#050805"/>' + leaf(x, 440, -150, .22, "#4ade80") + leaf(x, 440, -30, .22, "#4ade80")
    return d + LEAF_DEF, b

def wheel(cx, cy, r):
    out = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1a1d21" stroke="#2c3036" stroke-width="3"/>'
    for k in range(16):
        a = k * 22.5; out += f'<rect x="{cx-5}" y="{cy-r-6}" width="10" height="16" rx="3" fill="#0d0f11" transform="rotate({a} {cx} {cy})"/>'
    return out + f'<circle cx="{cx}" cy="{cy}" r="{r*.55}" fill="#f08c00"/><circle cx="{cx}" cy="{cy}" r="{r*.2}" fill="#343a40"/>'

def m_tractor(color="#2f9e44"):
    d = lin("tb", color, "#0b4a1f", False)
    b = '<path d="M180 330H520L560 420H220Z" fill="url(#tb)"/>'
    b += f'<rect x="150" y="296" width="200" height="106" rx="20" fill="url(#tb)"/><rect x="146" y="330" width="22" height="48" rx="6" fill="#ffe066"/><rect x="336" y="238" width="16" height="70" fill="#343a40"/>'
    b += '<rect x="392" y="190" width="170" height="150" rx="14" fill="#212529"/><rect x="408" y="206" width="138" height="100" rx="10" fill="#74c0fc" opacity=".75"/><path d="M420 214L470 214L430 300L420 300Z" fill="#fff" opacity=".25"/><rect x="380" y="180" width="194" height="18" rx="8" fill="url(#tb)"/>'
    b += wheel(235, 438, 62) + wheel(520, 410, 105)
    b += '<rect x="130" y="400" width="30" height="16" fill="#868e96"/>'
    return d, b

def m_machine(kind):
    d = lin("mb", "#e03131", "#7a1111", False) if kind != "tiller" else lin("mb", "#2f9e44", "#0b4a1f", False)
    b = '<g>' + wheel(330, 430, 70).replace("#f08c00", "#495057") + '</g>'
    b += '<rect x="290" y="300" width="190" height="110" rx="20" fill="url(#mb)"/><rect x="310" y="270" width="110" height="46" rx="12" fill="#343a40"/><circle cx="470" cy="280" r="24" fill="#868e96"/>'
    b += '<path d="M470 330L640 190" stroke="#212529" stroke-width="14" stroke-linecap="round"/><path d="M620 170L690 215M640 190L700 250" stroke="#212529" stroke-width="14" stroke-linecap="round"/>'
    b += '<g transform="translate(250,470)">' + "".join(f'<path d="M0 0L{-46*math.cos(math.radians(a)):.0f} {-46*math.sin(math.radians(a)):.0f}" stroke="#adb5bd" stroke-width="9" stroke-linecap="round"/>' for a in range(0, 360, 40)) + '<circle r="12" fill="#495057"/></g>'
    return d, b

def m_brush():
    d = ""
    b = '<path d="M180 490L640 160" stroke="#343a40" stroke-width="16" stroke-linecap="round"/><rect x="130" y="440" width="150" height="90" rx="20" fill="#e03131" transform="rotate(-35 205 485)"/>'
    b += '<path d="M470 280C520 300 560 320 560 360" stroke="#212529" stroke-width="12" fill="none"/><circle cx="660" cy="150" r="70" fill="none" stroke="#dee2e6" stroke-width="8" stroke-dasharray="14 8"/><circle cx="660" cy="150" r="10" fill="#e03131"/>'
    for x in range(560, 780, 14): b += f'<path d="M{x} 520C{x+4} 470 {x-6} 430 {x+2} 400" stroke="#4ade80" stroke-width="5" fill="none" stroke-linecap="round"/>'
    return d, b

def m_pump():
    d = lin("pb", "#1c7ed6", "#0b3a73", False)
    b = '<rect x="170" y="330" width="330" height="150" rx="40" fill="url(#pb)"/>'
    for x in range(200, 480, 24): b += f'<rect x="{x}" y="340" width="8" height="130" rx="4" fill="#fff" opacity=".12"/>'
    b += '<circle cx="540" cy="400" r="95" fill="#e9ecef" stroke="#868e96" stroke-width="6"/><circle cx="540" cy="400" r="40" fill="#495057"/><rect x="520" y="250" width="40" height="80" fill="#868e96"/><rect x="600" y="372" width="140" height="56" fill="#868e96"/>'
    b += '<rect x="120" y="470" width="470" height="24" rx="8" fill="#343a40"/><text x="335" y="415" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="40" fill="#fff">1 HP</text>'
    for i, x in enumerate((760, 785, 770)): b += f'<path d="M{x} {420+i*30}c-10 16-10 26 0 30c10-4 10-14 0-30z" fill="#74c0fc"/>'
    return d, b

def m_compost():
    d = lin("soil", "#6b4423", "#2a170a", False)
    b = '<path d="M130 500C180 330 280 250 400 250C520 250 620 330 670 500Z" fill="url(#soil)"/>'
    r = random.Random(9)
    for _ in range(90):
        x = r.uniform(190, 610); y = r.uniform(300, 495)
        if y > 250 + abs(x - 400) * .75: b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.uniform(2,6):.1f}" fill="{r.choice(["#8a5a2d","#3b2210","#a06a35"])}"/>'
    b += '<path d="M400 255V190" stroke="#4ade80" stroke-width="8" stroke-linecap="round"/>' + leaf(400, 200, -155, .55) + leaf(400, 200, -25, .55)
    b += '<path d="M240 460C270 420 300 480 330 440C350 420 370 450 380 440" stroke="#e8a0a0" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M500 400C520 370 550 420 575 385" stroke="#e8a0a0" stroke-width="11" fill="none" stroke-linecap="round"/>'
    return d + LEAF_DEF, b

def m_neemcake():
    d = lin("nc", "#7a5230", "#3a2412", False)
    b = ""
    for (x, y, w, h, r) in [(230, 380, 190, 100, -4), (400, 372, 190, 100, 3), (320, 290, 190, 100, -2), (520, 395, 170, 90, 6)]:
        b += f'<g transform="rotate({r} {x+w/2} {y+h/2})"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="url(#nc)"/><rect x="{x}" y="{y}" width="{w}" height="14" rx="7" fill="#fff" opacity=".08"/>'
        for i in range(10): b += f'<circle cx="{x+20+i*16}" cy="{y+30+(i%3)*22}" r="4" fill="#2b190a"/>'
        b += '</g>'
    return d, b + neem_sprig(170, 280, -50, .8)

def m_trichoderma():
    d = lin("pouch", "#2f9e44", "#0b6b2d", False)
    b = ('<g transform="translate(400,310)"><path d="M-120-170H120L140-130V180C140 205 120 215 100 215H-100C-120 215-140 205-140 180V-130Z" fill="url(#pouch)"/><path d="M-120-170H120L140-130H-140Z" fill="#000" opacity=".22"/>'
         '<rect x="-100" y="-90" width="200" height="210" rx="14" fill="#fff"/><text y="-30" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="34" fill="#0b6b2d">TRICHO</text><text y="8" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="34" fill="#0b6b2d">DERMA</text>'
         '<text y="48" text-anchor="middle" font-family="Inter,Arial" font-weight="600" font-size="20" fill="#495057">Bio-Fungicide</text><circle cx="0" cy="92" r="20" fill="#39D353"/></g>')
    return d, b + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#9be15d" opacity=".9"/>' for x, y, r in [(250, 505, 9), (290, 515, 6), (540, 508, 8), (580, 500, 6), (520, 520, 5)])

def m_feed(kind):
    c = {"cattle": ("#e8590c", "#9c3b05", "CATTLE", "FEED PELLETS"), "poultry": ("#f59f00", "#a86b00", "LAYER", "POULTRY FEED"), "mineral": ("#1c7ed6", "#0b3a73", "MINERAL", "FOR CATTLE")}[kind]
    d, b = m_sack(c[2], c[0], c[1], "#c68642" if kind == "cattle" else "#f1c27d", c[3])
    if kind == "poultry":
        b += "".join(f'<ellipse cx="{x}" cy="{y}" rx="26" ry="34" fill="#f8e7c9" stroke="#d9b98a" stroke-width="2" transform="rotate({r} {x} {y})"/>' for x, y, r in [(190, 480, -12), (230, 500, 10), (600, 485, 14), (640, 500, -8)])
    if kind == "cattle":
        b += "".join(f'<rect x="{x}" y="{y}" width="30" height="12" rx="6" fill="#8a5a2d" transform="rotate({r} {x} {y})"/>' for x, y, r in [(200, 495, 20), (240, 505, -10), (590, 490, 15), (630, 505, 0)])
    if kind == "mineral":
        b += '<rect x="560" y="430" width="120" height="76" rx="14" fill="#ced4da"/><rect x="574" y="418" width="92" height="24" rx="8" fill="#e9ecef"/>'
    return d, b

def m_seed_packet():
    d = lin("pk", "#39D353", "#168A3A", False)
    b = '<g transform="translate(400,300) rotate(-6)"><path d="M-130-170H130V190H-130Z" fill="url(#pk)"/><path d="M-130-170H130L130-148H-130Z" fill="#000" opacity=".25"/><rect x="-100" y="-110" width="200" height="190" rx="14" fill="#fff"/>'
    b += '<path d="M0 60V-10" stroke="#2f9e44" stroke-width="8" stroke-linecap="round"/><path d="M0-10C-40-20-60-60-50-90C-10-80 5-50 0-10Z" fill="#4ade80"/><path d="M0 10C40 0 60-40 50-70C10-60-5-30 0 10Z" fill="#2f9e44"/>'
    b += '<text y="125" text-anchor="middle" font-family="Inter,Arial" font-weight="800" font-size="32" fill="#fff">PREMIUM SEEDS</text></g>' + seeds_scatter("#f3e3b5", 18, 2, (200, 485, 600, 525))
    return "", b

# ---------------------------------------------------------------- scenes
def m_scene(variant=0):
    d = ('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1f12"/><stop offset=".6" stop-color="#1c5b2c"/><stop offset="1" stop-color="#f6c344"/></linearGradient>'
         '<radialGradient id="sun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff3b0"/><stop offset=".4" stop-color="#ffd43b" stop-opacity=".6"/><stop offset="1" stop-color="#ffd43b" stop-opacity="0"/></radialGradient>')
    sx = 560 if variant == 0 else 250
    b = f'<rect width="800" height="600" fill="url(#sky)"/><circle cx="{sx}" cy="300" r="170" fill="url(#sun)"/><circle cx="{sx}" cy="300" r="42" fill="#fff3b0"/>'
    b += '<path d="M0 340C140 290 260 330 400 300C540 270 660 320 800 290V600H0Z" fill="#0f3d1e"/>'
    b += '<path d="M0 380C160 340 300 380 450 350C580 325 700 360 800 340V600H0Z" fill="#14532d"/>'
    for i in range(14):
        t = i / 13; x0 = 400 + (t - .5) * 120; x1 = (t - .5) * 1900 + 400
        b += f'<path d="M{x0:.0f} 395L{x1:.0f} 600" stroke="#4ade80" stroke-opacity="{.25+.35*abs(t-.5)*2:.2f}" stroke-width="{3+abs(t-.5)*14:.1f}" fill="none"/>'
    for k in range(5):
        y = 410 + k * 42; b += f'<path d="M0 {y}H800" stroke="#052e16" stroke-opacity=".25" stroke-width="{2+k*2}"/>'
    return d, b + '<rect width="800" height="600" fill="#050805" opacity=".18"/>'

def m_avatar(i):
    cols = [("#39D353", "#0b6b2d"), ("#ffd43b", "#a86b00"), ("#74c0fc", "#1c7ed6")][i % 3]
    d = lin("av", cols[0], cols[1], False)
    return d + LEAF_DEF, f'<circle cx="400" cy="300" r="230" fill="url(#av)"/>' + leaf(400, 400, -125, 1.5, "#fff", "#0b6b2d").replace('fill="#fff"', 'fill="#ffffffee"') + leaf(400, 400, -55, 1.5, "#ffffffcc", "#0b6b2d") + '<path d="M400 410V250" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'

# ---------------------------------------------------------------- catalogue
P = {
 "maize-seeds": (lambda: m_maize(True), "#ffd43b"), "rice-seeds": (m_rice, "#f6c344"), "cotton-seeds": (m_cotton, "#e9ecef"),
 "tomato-seeds": (lambda: m_tomato(True), "#ff6b5b"), "chilli-seeds": (lambda: m_chilli(True), "#ff4d3d"), "okra-seeds": (m_okra, "#51cf66"),
 "potato-seeds": (m_potato, "#e0b36b"), "groundnut-seeds": (m_groundnut, "#d8a86a"),
 "npk-fertilizer": (lambda: m_sack("NPK", "#2f9e44", "#0b6b2d", "#e9ecef", "19:19:19"), "#39D353"),
 "urea-fertilizer": (lambda: m_sack("UREA", "#1c7ed6", "#0b3a73", "#f8f9fa", "46% N"), "#74c0fc"),
 "dap-fertilizer": (lambda: m_sack("DAP", "#e8590c", "#9c3b05", "#8a6d3b", "18:46:0"), "#ff922b"),
 "potash-fertilizer": (lambda: m_sack("MOP", "#c2255c", "#7a1038", "#c0392b", "POTASH 60%"), "#f06595"),
 "neem-oil": (m_neem_oil, "#9be15d"),
 "fungicide": (lambda: m_bottle("#7048e8", "FUNGICIDE", "Mancozeb 75% WP"), "#9775fa"),
 "herbicide": (lambda: m_bottle("#e8590c", "HERBICIDE", "Systemic 1 L"), "#ff922b"),
 "insecticide": (lambda: m_bottle("#c92a2a", "INSECTICIDE", "Imidacloprid"), "#ff6b6b"),
 "farming-tools": (m_tools, "#ffa94d"), "pruning-shears": (m_shears, "#ff922b"),
 "hand-sprayer": (m_hand_sprayer, "#51cf66"), "knapsack-sprayer": (m_knapsack, "#51cf66"), "battery-sprayer": (lambda: m_knapsack(True), "#ffa94d"),
 "drip-irrigation-kit": (m_drip, "#74c0fc"), "sprinkler": (m_sprinkler, "#74c0fc"), "hdpe-pipe": (m_pipe, "#adb5bd"), "mulching-film": (m_film, "#ced4da"),
 "power-weeder": (lambda: m_machine("weeder"), "#ff6b6b"), "power-tiller": (lambda: m_machine("tiller"), "#51cf66"),
 "brush-cutter": (m_brush, "#ff6b6b"), "water-pump": (m_pump, "#4dabf7"), "tractor": (m_tractor, "#51cf66"),
 "vermicompost": (m_compost, "#a9744a"), "organic-pesticide": (lambda: m_bottle("#2f9e44", "ORGANIC", "Panchagavya Spray", True, liquid="#6fbf4a"), "#8ce99a"),
 "neem-cake": (m_neemcake, "#a9744a"), "trichoderma": (m_trichoderma, "#8ce99a"),
 "cattle-feed": (lambda: m_feed("cattle"), "#ff922b"), "poultry-feed": (lambda: m_feed("poultry"), "#fcc419"), "mineral-mixture": (lambda: m_feed("mineral"), "#4dabf7"),
}
CATEGORIES = {"seeds": (m_seed_packet, "#39D353"), "fertilizers": P["npk-fertilizer"], "crop-protection": P["insecticide"], "farming-tools": P["farming-tools"],
              "irrigation": P["drip-irrigation-kit"], "machinery": P["tractor"], "organic": P["vermicompost"], "animal-feed": P["cattle-feed"]}
BLOG = {"tomato-seed-guide": P["tomato-seeds"], "drip-irrigation-techniques": P["drip-irrigation-kit"], "organic-farming-basics": P["vermicompost"], "fertilizer-selection-guide": P["npk-fertilizer"]}

def write(sub, name, spec, scene=False):
    fn, tint = spec
    defs, body = fn()
    svg = wrap(body, defs + LEAF_DEF, tint, ground=not scene)
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
    open(os.path.join(ROOT, sub, name + ".svg"), "w", encoding="utf-8").write(svg)

def main():
    for k, v in P.items(): write("products", k, v)
    for k, v in CATEGORIES.items(): write("categories", k, v)
    for k, v in BLOG.items(): write("blog", k, v)
    write("hero", "hero-farmer-field", (lambda: m_scene(0), "#ffd43b"), True)
    write("banners", "deals", (lambda: m_scene(1), "#ffd43b"), True)
    write("banners", "marketplace", (lambda: m_scene(0), "#39D353"), True)
    for i in (1, 2, 3): write("farmers", f"farmer-0{i}", ((lambda i=i: m_avatar(i)), "#39D353"), True)
    print("art written to", os.path.abspath(ROOT))

if __name__ == "__main__":
    main()
