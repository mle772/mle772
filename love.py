"""A heart made of "I love you" in 20 languages.

Words are packed inside the parametric heart curve, fade in from the centre
outwards, and then the whole heart beats.
"""
import math as m
import random as r
import sys
import tkinter.font as tkf
import turtle as t

BG = "#05060f"
FONT = "Segoe UI" if sys.platform.startswith("win") else (
    "Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans")
SC = 23          # pixels per heart unit (heart is about 32 units wide)
OY = 0           # vertical offset in pixels
PALETTE = ["#ff2e4d", "#ff4d6d", "#ff3b3b", "#ff6b81", "#ff1f6b", "#ff5a36"]

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

s = t.Screen()
s.setup(800, 800)
s.bgcolor(BG)
s.title("Love Heart")
s.tracer(0)
cv = s.getcanvas()
rng = r.Random(11)          # fixed seed -> same heart every run

_fonts = {}


def font_for(size):
    """Cache one Font object per size (creating fonts is slow)."""
    if size not in _fonts:
        _fonts[size] = tkf.Font(root=cv, family=FONT, size=size, weight="bold")
    return _fonts[size]


def heart(a):
    """Parametric heart, returned in pixel coordinates (y up)."""
    x = 16 * m.sin(a) ** 3
    y = (13 * m.cos(a) - 5 * m.cos(2 * a)
         - 2 * m.cos(3 * a) - m.cos(4 * a))
    return x * SC, y * SC + OY


# --- point-in-heart test --------------------------------------------------
EDGES = []
_pts = [heart(2 * m.pi * i / 720) for i in range(720)]
for i, p in enumerate(_pts):
    EDGES.append((p, _pts[(i + 1) % len(_pts)]))
_row_cache = {}


def _intervals(y):
    """x-intervals of the heart on the horizontal line at height y."""
    key = round(y)
    if key not in _row_cache:
        xs = []
        for (x1, y1), (x2, y2) in EDGES:
            if (y1 <= key < y2) or (y2 <= key < y1):
                xs.append(x1 + (key - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        _row_cache[key] = list(zip(xs[0::2], xs[1::2]))
    return _row_cache[key]


def inside(x, y):
    return any(lo <= x <= hi for lo, hi in _intervals(y))


# --- fill the heart row by row --------------------------------------------
def span(y_top, y_bot):
    """x-intervals that are inside the heart on the whole band [y_bot, y_top]."""
    ys = (y_top, (y_top + y_bot) / 2, y_bot)
    out = _intervals(ys[0])
    for y in ys[1:]:
        out = [(max(a, c), min(b, d))
               for a, b in out for c, d in _intervals(y) if max(a, c) < min(b, d)]
    return out


def pack():
    """Rows of words, justified to the heart's outline (like the video)."""
    words = []
    y = 17 * SC
    while y > -17 * SC:
        size = rng.choice((9, 10, 11, 12, 13, 14))
        f = font_for(size)
        h = f.metrics("linespace") + 1
        for lo, hi in span(y, y - h):
            lo, hi = lo + 6, hi - 6
            row, used = [], 0
            while True:
                for _ in range(8):                       # find a phrase that fits
                    text = rng.choice(PHRASES)
                    w = f.measure(text) + 8
                    if used + w <= hi - lo:
                        break
                else:
                    break
                row.append((text, w))
                used += w
            if not row:
                continue
            gap = (hi - lo - used) / len(row)            # justify the row
            x = lo + gap / 2
            for text, w in row:
                words.append((text, x + w / 2, y - h / 2, size,
                              rng.uniform(-5, 5)))
                x += w + gap
        y -= h
    return words


def lerp_color(c1, c2, k):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * k)
                                   for i in range(3))


words = pack()
words.sort(key=lambda w: w[1] ** 2 + w[2] ** 2)   # centre first
items = []                                         # (canvas id, colour)


def reveal(i=0, batch=4):
    """Fade the words in, a few per frame."""
    for text, x, y, size, ang in words[i:i + batch]:
        col = rng.choice(PALETTE)
        item = cv.create_text(x, -y, text=text, fill="#ffffff",
                              font=font_for(size), angle=ang)
        items.append((item, col))
    # white-hot -> neon red for the most recent words
    for n, (item, col) in enumerate(items[-40:]):
        k = min(1, (len(items[-40:]) - n) / 40)
        cv.itemconfig(item, fill=lerp_color("#ffffff", col, 1 - k))
    s.update()
    if i + batch < len(words):
        cv.after(15, reveal, i + batch, batch)
    else:
        for item, col in items:
            cv.itemconfig(item, fill=col)
        beat(0)


def beat(frame):
    """Heartbeat: a quick double pulse, then rest."""
    k = frame % 60
    pulse = (m.exp(-((k - 6) / 3) ** 2) * 0.05
             + m.exp(-((k - 16) / 3) ** 2) * 0.035)
    prev = getattr(beat, "last", 0.0)
    k2 = (1 + pulse) / (1 + prev)       # undo previous scale, apply new one
    cv.scale("all", 0, 0, k2, k2)
    beat.last = pulse
    s.update()
    cv.after(20, beat, frame + 1)


reveal()
s.mainloop()
