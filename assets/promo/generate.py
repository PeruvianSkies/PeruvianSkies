#!/usr/bin/env python3
"""
gemul — terminal profile promo.

Renders `gemul-terminal.gif`: a short looping sequence that boots a terminal,
handshakes over ssh, answers `whoami` with an identity card, and signs off.

Palette and accent match the rest of the profile README (`#0D1117` ground,
`#58A6FF` accent), so the banner and the badges below it read as one system.

Deps: pillow >= 10
Run:  python3 assets/promo/generate.py
"""

from __future__ import annotations

import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------

W, H = 760, 320          # delivered size
DS = 2                    # supersample factor, discarded on export
FW, FH = W * DS, H * DS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gemul-terminal.gif")


def S(v: float) -> float:
    return v * DS


# --------------------------------------------------------------------------
# Palette — matches the README badges (#0D1117 ground, #58A6FF accent)
# --------------------------------------------------------------------------

BG      = (0x0d, 0x11, 0x17)
RAISED  = (0x16, 0x1b, 0x22)
LINE    = (0x30, 0x36, 0x3d)
FAINT   = (0x48, 0x4f, 0x58)
MUTED   = (0x6e, 0x76, 0x81)
BODY    = (0x91, 0x98, 0xa1)
HEADING = (0xe6, 0xed, 0xf3)
ACCENT  = (0x58, 0xa6, 0xff)
WHITE   = (0xff, 0xff, 0xff)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fade(c, t):
    return mix(BG, c, t)


def ramp(a, b, n):
    return [mix(a, b, k / max(1, n - 1)) for k in range(n)]


def brand_palette():
    cols = []
    cols += ramp(BG, RAISED, 6)
    cols += ramp(RAISED, LINE, 6)
    cols += ramp(LINE, FAINT, 6)
    cols += ramp(FAINT, MUTED, 6)
    cols += ramp(MUTED, BODY, 6)
    cols += ramp(BODY, HEADING, 8)
    cols += ramp(HEADING, WHITE, 3)
    cols += ramp(BG, ACCENT, 16)
    cols += ramp(ACCENT, WHITE, 6)
    cols += [BG, RAISED, LINE, FAINT, MUTED, BODY, HEADING, ACCENT, WHITE]
    seen, uniq = set(), []
    for c in cols:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq[:256]


def build_palette():
    flat: list[int] = []
    cols = brand_palette()
    for c in cols:
        flat += list(c)
    flat += [0, 0, 0] * (256 - len(cols))
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat)
    return pal


# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------

MONO = "/System/Library/Fonts/Menlo.ttc"
DISP = "/System/Library/Fonts/HelveticaNeue.ttc"


def font(path, size, index=0):
    return ImageFont.truetype(path, int(round(size * DS)), index=index)


F_MONO_XS = font(MONO, 10.5)
F_MONO_S = font(MONO, 12)
F_MONO = font(MONO, 14)
F_MONO_B = font(MONO, 14, index=1)
F_MONO_XL = font(MONO, 30, index=1)
F_DISP_XL = font(DISP, 38, index=1)
F_DISP_M = font(DISP, 15)

LH = 20.0


def text(d, x, y, s, f, fill, anchor="la"):
    d.text((S(x), S(y)), s, font=f, fill=fill, anchor=anchor)


def text_w(s, f) -> float:
    return f.getlength(s) / DS


def ctext(d, cx, y, s, f, fill):
    d.text((S(cx), S(y)), s, font=f, fill=fill, anchor="ma")


# --------------------------------------------------------------------------
# Easing
# --------------------------------------------------------------------------

def clamp01(t):
    return max(0.0, min(1.0, t))


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def seg(frame, start, length):
    return clamp01((frame - start) / float(length))


# --------------------------------------------------------------------------
# Chrome — corner ticks, bottom status bar, the mark
# --------------------------------------------------------------------------

def corner_ticks(d, k, inset=14.0, arm=22.0):
    col = fade(LINE, k)
    w = max(1, int(S(1)))
    for cx, cy, sx, sy in ((inset, inset, 1, 1), (W - inset, inset, -1, 1),
                           (inset, H - inset, 1, -1), (W - inset, H - inset, -1, -1)):
        d.line([S(cx), S(cy), S(cx + sx * arm), S(cy)], fill=col, width=w)
        d.line([S(cx), S(cy), S(cx), S(cy + sy * arm)], fill=col, width=w)


def status_bar(d, k, label):
    col = fade(LINE, k * 0.9)
    d.line([S(24), S(H - 26), S(W - 24), S(H - 26)], fill=col, width=max(1, int(S(1))))
    text(d, 24, H - 21, label, F_MONO_XS, fade(FAINT, k))
    text(d, W - 24, H - 21, "peruvianskies", F_MONO_XS, fade(FAINT, k), anchor="ra")


def draw_mark(d, cx, cy, size, k=1.0):
    """Two linked rings — the DevOps loop, abstracted."""
    r = size * 0.34
    off = r * 0.62
    sw = max(1, int(S(size * 0.055)))
    col = fade(ACCENT, k)
    for dx in (-off, off):
        bbox = [S(cx + dx - r), S(cy - r), S(cx + dx + r), S(cy + r)]
        d.ellipse(bbox, outline=col, width=sw)


# --------------------------------------------------------------------------
# Post-processing
# --------------------------------------------------------------------------

def bloom(img, radius=6 * DS, strength=0.5):
    small = img.resize((FW // 4, FH // 4), Image.BILINEAR)
    small = ImageChops.subtract(small, Image.new("RGB", small.size, (40, 40, 40)))
    small = small.filter(ImageFilter.GaussianBlur(radius))
    up = small.resize((FW, FH), Image.BILINEAR)
    up = up.point(lambda v: int(v * strength))
    return ImageChops.screen(img, up)


def build_screen_mask():
    m = Image.new("L", (W, H), 255)
    px = m.load()
    cx, cy = W / 2.0, H / 2.0
    maxd = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(H):
        scan = 0.90 if (y % 2) else 1.0
        for x in range(W):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / maxd
            vig = 1.0 - 0.12 * (d ** 2.0)
            px[x, y] = max(0, min(255, int(255 * scan * vig)))
    return Image.merge("RGB", (m, m, m))


SCREEN_MASK = build_screen_mask()


def finalize(img):
    """Bloom at device res, downscale to delivered size, apply screen mask."""
    img = bloom(img)
    small = img.resize((W, H), Image.LANCZOS)
    return ImageChops.multiply(small, SCREEN_MASK)


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------

NAME = "Tian Putra Nuhcahya"
TAGLINE = [
    "Leading DevOps for a PCI DSS fintech platform.",
    "DevSecOps and GitOps, and the guardrails between them.",
]
SPEC = [
    ("role", "technical lead · devops & platform engineering"),
    ("based", "indonesia"),
    ("building", "pci dss fintech payment platform · gke"),
    ("also", "devsecops · finops · mentoring"),
]

TERM_LINES = [
    # (start_frame, indent, segments[(text, colour)], typed?)
    (0, 0, [("gemul", MUTED), (" on ", FAINT), ("main", MUTED), (" [ok]", FAINT)], False),
    (3, 0, [("→ ", ACCENT), ("ssh gemul@github.com", BODY)], True),
    (22, 1, [("handshake ", FAINT), ("·" * 12, LINE), (" ok", BODY)], False),
    (26, 0, [("→ ", ACCENT), ("whoami", BODY)], True),
]

CPS = 1.4


def _cursor(d, x, y, f, k=0.85):
    if (f // 3) % 2 == 0:
        d.rectangle([S(x), S(y + 2), S(x + 8), S(y + LH * 0.8)], fill=fade(BODY, k))


def draw_terminal(d, f, lines, y0=70.0, tail_from=None):
    x0 = 46.0
    last_x = last_y = None
    for row, (start, indent, segments, typed) in enumerate(lines):
        if f < start:
            continue
        y = y0 + row * (LH + 5)
        x = x0 + indent * 14
        full = "".join(s for s, _ in segments)
        n = int((f - start) * CPS) if typed else len(full)
        if n <= 0:
            continue
        used = 0
        cx = x
        for s, col in segments:
            if used >= n:
                break
            take = min(len(s), n - used)
            chunk = s[:take]
            text(d, cx, y, chunk, F_MONO, fade(col, 1.0))
            cx += text_w(chunk, F_MONO)
            used += take
        last_x, last_y = cx, y
        if typed and used < len(full):
            _cursor(d, cx, y, f, 0.8)
            return
    if tail_from is not None and f >= tail_from and last_x is not None:
        _cursor(d, last_x, last_y, f, 0.9)


# --------------------------------------------------------------------------
# Scenes — each returns a list of (frame_image, duration_ms)
# --------------------------------------------------------------------------

def scene_power():
    out = []
    n = 8
    for i in range(n):
        t = ease_out((i + 1) / n)
        img = Image.new("RGB", (FW, FH), BG)
        d = ImageDraw.Draw(img)
        half = max(1.0, t * H * 0.55)
        cy = H / 2.0
        steps = 24
        for s in range(steps):
            f0, f1 = s / steps, (s + 1) / steps
            v = ((1 - f0) ** 2.4) * 0.6 * (1 - t)
            col = mix(BG, HEADING, v)
            if col != BG:
                d.rectangle([0, S(cy - half * f1), FW, S(cy - half * f0)], fill=col)
                d.rectangle([0, S(cy + half * f0), FW, S(cy + half * f1)], fill=col)
        if t < 0.95:
            lw = max(1, int(S(2.0 * (1 - t) + 0.6)))
            d.line([0, S(cy), FW, S(cy)], fill=mix(HEADING, WHITE, 1 - t), width=lw)
        out.append((finalize(img), 30))
    return out


def scene_terminal():
    out = []
    n = 46
    for f in range(n):
        img = Image.new("RGB", (FW, FH), BG)
        d = ImageDraw.Draw(img)
        corner_ticks(d, 0.85)
        status_bar(d, 0.8, "connecting")
        draw_terminal(d, f, TERM_LINES, tail_from=32)
        out.append((finalize(img), 32))
    # flash invert — the beat between `whoami` and the answer
    for i, t in enumerate((0, 1)):
        img = Image.new("RGB", (FW, FH), HEADING if i == 0 else mix(HEADING, BODY, 0.35))
        out.append((img.resize((W, H), Image.LANCZOS), 90))
    return out


def scene_identity():
    out = []
    n = 40
    x0 = 46.0
    for f in range(n):
        img = Image.new("RGB", (FW, FH), BG)
        d = ImageDraw.Draw(img)
        corner_ticks(d, 0.9)
        status_bar(d, 0.85, "identity")

        a_name = ease_out(seg(f, 0, 6))
        text(d, x0, 58, NAME, F_DISP_XL, fade(HEADING, a_name))

        e = ease_out(seg(f, 3, 7))
        d.line([S(x0), S(112), S(x0 + 260 * e), S(112)],
               fill=fade(ACCENT, 0.9 * (1 if e > 0 else 0)), width=max(1, int(S(1.5))))

        n1 = max(0, int((f - 6) * 3.6))
        l1, l2 = TAGLINE
        text(d, x0, 128, l1[:n1], F_DISP_M, MUTED)
        if n1 > len(l1):
            text(d, x0, 152, l2[:n1 - len(l1)], F_DISP_M, MUTED)

        for i, (k, v) in enumerate(SPEC):
            st = 18 + i * 3
            if f < st:
                continue
            a = ease_out(seg(f, st, 6))
            y = 190 + i * 20
            text(d, x0, y, k, F_MONO_S, fade(FAINT, a))
            text(d, x0 + 96, y, v, F_MONO_S, fade(BODY, a))

        if f >= 20:
            draw_mark(d, W - 76, 76, 42, ease_out(seg(f, 20, 8)))

        out.append((finalize(img), 32))
    out.append((out[-1][0], 2200))
    return out


def scene_signoff():
    out = []
    n = 34
    cx = W / 2.0
    for f in range(n):
        img = Image.new("RGB", (FW, FH), BG)
        d = ImageDraw.Draw(img)
        corner_ticks(d, 0.9)
        status_bar(d, 0.85, "open channel")

        a = ease_out(seg(f, 1, 6))
        draw_mark(d, cx, 118, 56, a)

        if f >= 4:
            b = ease_out(seg(f, 4, 5))
            ctext(d, cx, 158, "gemul", F_MONO_XL, fade(HEADING, b))

        if f >= 8:
            b = ease_out(seg(f, 8, 5))
            ctext(d, cx, 200, f"{NAME} — Technical Lead, DevOps & Platform Engineering",
                  F_MONO_S, fade(MUTED, b))

        if f >= 11:
            b = ease_out(seg(f, 11, 4))
            w = 190 * b
            d.line([S(cx - w), S(224), S(cx + w), S(224)], fill=fade(LINE, b),
                   width=max(1, int(S(1))))

        if f >= 14:
            b = ease_out(seg(f, 14, 4))
            left, right = "github.com/peruvianskies", "linkedin.com/in/tian-putra-nuhcahya"
            total = text_w(left, F_MONO_S) + text_w("  ·  ", F_MONO_S) + text_w(right, F_MONO_S)
            x = cx - total / 2
            text(d, x, 244, left, F_MONO_S, fade(BODY, b))
            x += text_w(left, F_MONO_S)
            text(d, x, 244, "  ·  ", F_MONO_S, fade(FAINT, b))
            x += text_w("  ·  ", F_MONO_S)
            text(d, x, 244, right, F_MONO_S, fade(ACCENT, b))

        out.append((finalize(img), 32))

    hold = out[-1][0]
    for _ in range(5):
        out.append((hold, 180))
    out.append((hold, 1800))

    # fade to black tail so the loop reads as a power cycle
    m = 8
    for i in range(m):
        k = 1 - (i + 1) / m
        dark = ImageChops.multiply(hold, Image.new("RGB", (W, H), (int(255 * k),) * 3))
        out.append((dark, 40))
    return out


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------

def render():
    frames_durs = scene_power() + scene_terminal() + scene_identity() + scene_signoff()
    frames = [f for f, _ in frames_durs]
    durations = [d for _, d in frames_durs]

    palette = build_palette()
    quantised = [fr.quantize(palette=palette, dither=Image.Dither.NONE) for fr in frames]
    quantised[0].save(
        OUT,
        save_all=True,
        append_images=quantised[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    size = os.path.getsize(OUT)
    print(f"done: {OUT} ({W}x{H}, {size / 1024:.0f} KB, "
          f"{len(frames)} frames, {sum(durations) / 1000:.1f}s)")


if __name__ == "__main__":
    render()
