#!/usr/bin/env python3
"""
🎬 Todo Budget — Cartoon Story Reel
A story-driven animated short with a character going through their day.

Story arc:
  1. Morning Wake Up — alarm, groggy character
  2. Chaos Montage — bills, tasks, notes flying everywhere, stress
  3. Breaking Point — character overwhelmed, head spinning
  4. Discovery — phone glows, Todo Budget appears
  5. Transformation — everything organizes itself, relief
  6. Happy Ending — character relaxed, everything in order
  7. CTA — download

Character: Simple geometric person with expressive face
Style: Clean, colorful, cartoon-like with smooth animations

python3 build_cartoon.py
"""

import os, math, random, shutil, subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H = 1080, 1920
FPS = 30
BPM = 120
BEAT = 60.0 / BPM

BASE = Path(__file__).parent
OUT_DIR = BASE / "cartoon"
OUT_DIR.mkdir(exist_ok=True)
OUTPUT = BASE / "instagram-reels-cartoon.mp4"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ─── Palette ─────────────────────────────────────────────────────────────
SKY_BLUE    = (135, 206, 235)
NIGHT_BLUE  = (20, 24, 50)
WARM_BG     = (255, 248, 240)
OFFICE_BG   = (235, 235, 245)
SKIN        = (255, 213, 170)
HAIR        = (70, 50, 40)
SHIRT_BLUE  = (90, 130, 220)
PANTS       = (60, 70, 90)
WHITE       = (255, 255, 255)
BLACK       = (30, 30, 30)
RED         = (230, 80, 80)
GREEN       = (60, 200, 130)
PURPLE      = (108, 58, 224)
ORANGE      = (255, 160, 60)
YELLOW      = (255, 220, 80)
CYAN        = (60, 200, 230)
PINK        = (255, 150, 180)
DIM         = (150, 150, 170)
CARD_BG     = (245, 245, 250)
SHADOW      = (200, 200, 210)
FLOOR       = (220, 210, 200)
WALL        = (250, 245, 240)
BED_COLOR   = (180, 200, 230)
PILLOW      = (230, 235, 250)
DESK_COLOR  = (180, 140, 100)
SCREEN_BG   = (20, 20, 40)

_fc = {}
def fnt(size, bold=True):
    size = max(1, int(size))
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    return _fc[k]

# ─── Easing ──────────────────────────────────────────────────────────────
def ease_out(t): t=max(0,min(1,t)); return 1-(1-t)**3
def ease_in(t): t=max(0,min(1,t)); return t**3
def ease_in_out(t): t=max(0,min(1,t)); return 3*t*t - 2*t*t*t if t < 0.5 else 1 - ((-2*t+2)**3)/2 if t >= 0.5 else 3*t*t-2*t*t*t
def ease_back(t): t=max(0,min(1,t)); c=1.7; return 1+(c+1)*(t-1)**3+c*(t-1)**2
def ease_elastic(t):
    t=max(0,min(1,t))
    if t==0 or t==1: return t
    return 2**(-10*t)*math.sin((t*10-0.75)*2*math.pi/3)+1
def lerp(a,b,t): return a+(b-a)*max(0,min(1,t))
def col_lerp(c1,c2,t): t=max(0,min(1,t)); return tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))

def tw(d, text, f):
    bb = d.textbbox((0,0), text, font=f)
    return bb[2]-bb[0]

def draw_centered(d, y, text, f, fill=BLACK, shadow=False):
    w = tw(d, text, f)
    x = (W - w) // 2
    if shadow:
        d.text((x+2, y+2), text, font=f, fill=(0,0,0,80))
    d.text((x, y), text, font=f, fill=fill)

# ═══════════════════════════════════════════════════════════════════════════
# CHARACTER DRAWING
# ═══════════════════════════════════════════════════════════════════════════

def draw_character(draw, cx, cy, scale=1.0, emotion="neutral", look_dir=0,
                   arm_angle=0, body_tilt=0, jump=0, blink=False,
                   holding=None, shirt_color=SHIRT_BLUE):
    """
    Draw a simple cartoon character.
    cx, cy = center bottom (feet position)
    emotion: neutral, happy, sad, stressed, shocked, sleeping, love
    look_dir: -1 left, 0 center, 1 right
    arm_angle: 0=down, positive=up (degrees)
    body_tilt: lean angle in degrees
    jump: vertical offset upward
    """
    s = scale
    cy -= jump

    # Body tilt
    tilt_rad = math.radians(body_tilt)
    def tilt(x, y):
        rx = (x - cx) * math.cos(tilt_rad) - (y - cy) * math.sin(tilt_rad) + cx
        ry = (x - cx) * math.sin(tilt_rad) + (y - cy) * math.cos(tilt_rad) + cy
        return rx, ry

    # Shadow on ground
    shadow_w = int(60 * s)
    shadow_h = int(15 * s)
    draw.ellipse([cx - shadow_w, cy - shadow_h//2, cx + shadow_w, cy + shadow_h//2],
                 fill=(*SHADOW[:3], 80))

    # Legs
    leg_len = int(80 * s)
    leg_w = int(18 * s)
    hip_y = cy - leg_len
    # Left leg
    lx1, ly1 = tilt(cx - int(15*s), hip_y)
    lx2, ly2 = cx - int(20*s), cy
    draw.line([(lx1, ly1), (lx2, ly2)], fill=PANTS, width=leg_w)
    # Right leg
    rx1, ry1 = tilt(cx + int(15*s), hip_y)
    rx2, ry2 = cx + int(20*s), cy
    draw.line([(rx1, ry1), (rx2, ry2)], fill=PANTS, width=leg_w)
    # Shoes
    shoe_w = int(28 * s)
    shoe_h = int(14 * s)
    draw.ellipse([lx2 - shoe_w, ly2 - shoe_h, lx2 + shoe_w//2, ly2 + shoe_h//2], fill=BLACK)
    draw.ellipse([rx2 - shoe_w//2, ry2 - shoe_h, rx2 + shoe_w, ry2 + shoe_h//2], fill=BLACK)

    # Body (torso)
    body_top = hip_y - int(90 * s)
    bx, by = tilt(cx, body_top)
    bhx, bhy = tilt(cx, hip_y)
    body_w = int(55 * s)
    # Rounded rectangle for torso
    draw.rounded_rectangle([bx - body_w, by, bhx + body_w, bhy],
                           radius=int(20*s), fill=shirt_color)

    # Arms
    shoulder_y = body_top + int(20 * s)
    arm_len = int(70 * s)
    arm_w = int(14 * s)

    la_rad = math.radians(-arm_angle - 20 + body_tilt)
    ra_rad = math.radians(arm_angle + 20 - body_tilt)

    # Left arm
    lsx, lsy = tilt(cx - body_w, shoulder_y)
    lax = lsx + arm_len * math.sin(la_rad)
    lay = lsy + arm_len * math.cos(la_rad)
    draw.line([(lsx, lsy), (lax, lay)], fill=SKIN, width=arm_w)
    # Hand
    hand_r = int(10 * s)
    draw.ellipse([lax-hand_r, lay-hand_r, lax+hand_r, lay+hand_r], fill=SKIN)

    # Right arm
    rsx, rsy = tilt(cx + body_w, shoulder_y)
    rax = rsx - arm_len * math.sin(ra_rad)
    ray = rsy + arm_len * math.cos(ra_rad)
    draw.line([(rsx, rsy), (rax, ray)], fill=SKIN, width=arm_w)
    draw.ellipse([rax-hand_r, ray-hand_r, rax+hand_r, ray+hand_r], fill=SKIN)

    # Holding object (phone, paper, etc.)
    if holding == "phone":
        ph_w, ph_h = int(25*s), int(45*s)
        phx, phy = int(rax - ph_w//2), int(ray - ph_h)
        draw.rounded_rectangle([phx, phy, phx+ph_w, phy+ph_h], radius=int(5*s), fill=BLACK)
        draw.rounded_rectangle([phx+2, phy+4, phx+ph_w-2, phy+ph_h-4], radius=int(3*s), fill=SCREEN_BG)
        # Tiny app icon on screen
        draw.rounded_rectangle([phx+6, phy+12, phx+ph_w-6, phy+ph_h-12],
                               radius=int(3*s), fill=PURPLE)
        draw.text((phx+8, phy+16), "✓", font=fnt(int(14*s)), fill=WHITE)

    # Neck
    neck_y = body_top - int(10 * s)
    nx, ny = tilt(cx, neck_y)
    draw.rectangle([nx - int(10*s), ny, nx + int(10*s), by + int(10*s)], fill=SKIN)

    # Head
    head_r = int(50 * s)
    hx, hy = tilt(cx, neck_y - head_r)
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=SKIN)

    # Hair
    hair_h = int(30 * s)
    draw.ellipse([hx - head_r - int(3*s), hy - head_r - int(5*s),
                  hx + head_r + int(3*s), hy - head_r + hair_h], fill=HAIR)
    # Side hair
    draw.ellipse([hx - head_r - int(5*s), hy - head_r, hx - head_r + int(15*s), hy], fill=HAIR)
    draw.ellipse([hx + head_r - int(15*s), hy - head_r, hx + head_r + int(5*s), hy], fill=HAIR)

    # Eyes
    eye_y = hy - int(5 * s)
    eye_sep = int(20 * s)
    eye_r = int(10 * s)
    pupil_r = int(5 * s)
    look_off = int(look_dir * 4 * s)

    if blink or emotion == "sleeping":
        # Closed eyes (lines)
        for ex in [hx - eye_sep, hx + eye_sep]:
            draw.line([(ex - eye_r, eye_y), (ex + eye_r, eye_y)],
                      fill=BLACK, width=int(3*s))
    else:
        for ex in [hx - eye_sep, hx + eye_sep]:
            # White
            draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=WHITE)
            # Outline
            draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r],
                         outline=BLACK, width=max(1, int(2*s)))
            # Pupil
            px = ex + look_off
            py = eye_y
            if emotion == "stressed":
                # Tiny pupils
                pr = int(3 * s)
                draw.ellipse([px-pr, py-pr, px+pr, py+pr], fill=BLACK)
            elif emotion == "shocked":
                # Big pupils
                draw.ellipse([px-pupil_r-2, py-pupil_r-2, px+pupil_r+2, py+pupil_r+2], fill=BLACK)
                # Highlight
                draw.ellipse([px-2, py-pupil_r+1, px+3, py-pupil_r+5], fill=WHITE)
            elif emotion == "love":
                # Heart eyes
                draw_heart(draw, ex, eye_y, int(12*s), RED)
            else:
                draw.ellipse([px-pupil_r, py-pupil_r, px+pupil_r, py+pupil_r], fill=BLACK)
                # Highlight
                draw.ellipse([px-1, py-pupil_r+1, px+2, py-pupil_r+4], fill=WHITE)

    # Eyebrows
    brow_y = eye_y - int(15 * s)
    brow_w = int(14 * s)
    if emotion == "stressed" or emotion == "sad":
        # Worried brows (angled inward)
        draw.line([(hx-eye_sep-brow_w, brow_y-int(5*s)), (hx-eye_sep+brow_w, brow_y+int(3*s))],
                  fill=HAIR, width=int(3*s))
        draw.line([(hx+eye_sep-brow_w, brow_y+int(3*s)), (hx+eye_sep+brow_w, brow_y-int(5*s))],
                  fill=HAIR, width=int(3*s))
    elif emotion == "happy" or emotion == "love":
        # Raised happy brows
        draw.arc([hx-eye_sep-brow_w, brow_y-int(8*s), hx-eye_sep+brow_w, brow_y+int(4*s)],
                 180, 0, fill=HAIR, width=int(3*s))
        draw.arc([hx+eye_sep-brow_w, brow_y-int(8*s), hx+eye_sep+brow_w, brow_y+int(4*s)],
                 180, 0, fill=HAIR, width=int(3*s))
    elif emotion == "shocked":
        # High raised
        brow_y -= int(5*s)
        draw.arc([hx-eye_sep-brow_w, brow_y-int(10*s), hx-eye_sep+brow_w, brow_y],
                 180, 0, fill=HAIR, width=int(3*s))
        draw.arc([hx+eye_sep-brow_w, brow_y-int(10*s), hx+eye_sep+brow_w, brow_y],
                 180, 0, fill=HAIR, width=int(3*s))
    else:
        # Normal
        draw.line([(hx-eye_sep-brow_w, brow_y), (hx-eye_sep+brow_w, brow_y)],
                  fill=HAIR, width=int(3*s))
        draw.line([(hx+eye_sep-brow_w, brow_y), (hx+eye_sep+brow_w, brow_y)],
                  fill=HAIR, width=int(3*s))

    # Mouth
    mouth_y = hy + int(18 * s)
    mouth_w = int(15 * s)
    if emotion == "happy" or emotion == "love":
        draw.arc([hx-mouth_w, mouth_y-int(8*s), hx+mouth_w, mouth_y+int(10*s)],
                 0, 180, fill=BLACK, width=int(3*s))
    elif emotion == "sad" or emotion == "stressed":
        draw.arc([hx-mouth_w, mouth_y, hx+mouth_w, mouth_y+int(14*s)],
                 180, 0, fill=BLACK, width=int(3*s))
    elif emotion == "shocked":
        draw.ellipse([hx-int(10*s), mouth_y-int(5*s), hx+int(10*s), mouth_y+int(12*s)],
                     fill=BLACK)
    elif emotion == "sleeping":
        # Zzz mouth
        draw.line([(hx-mouth_w, mouth_y+3), (hx+mouth_w, mouth_y+3)],
                  fill=BLACK, width=int(2*s))
    else:
        draw.line([(hx-mouth_w, mouth_y), (hx+mouth_w, mouth_y)],
                  fill=BLACK, width=int(3*s))

    # Emotion extras
    if emotion == "stressed":
        # Sweat drops
        drop_x = hx + head_r + int(5*s)
        drop_y = hy - int(5*s)
        draw.polygon([(drop_x, drop_y - int(10*s)), (drop_x - int(5*s), drop_y + int(5*s)),
                       (drop_x + int(5*s), drop_y + int(5*s))], fill=CYAN)
        draw.ellipse([drop_x - int(5*s), drop_y + int(2*s),
                      drop_x + int(5*s), drop_y + int(10*s)], fill=CYAN)

    if emotion == "sleeping":
        # Zzz
        for i in range(3):
            zx = hx + head_r + int(15*s) + i * int(15*s)
            zy = hy - head_r - int(10*s) - i * int(20*s)
            szz = int((12 + i * 6) * s)
            draw.text((zx, zy), "Z", font=fnt(szz), fill=CYAN)

    if emotion == "love":
        # Floating hearts
        for i in range(3):
            hrt_x = hx + int((-20 + i * 30) * s)
            hrt_y = hy - head_r - int((20 + i * 15) * s)
            draw_heart(draw, hrt_x, hrt_y, int(10*s), PINK)

    return hx, hy  # return head center for speech bubbles


def draw_heart(draw, cx, cy, size, color):
    """Draw a simple heart shape."""
    s = size
    # Two circles + triangle
    draw.ellipse([cx - s, cy - s, cx, cy], fill=color)
    draw.ellipse([cx, cy - s, cx + s, cy], fill=color)
    draw.polygon([(cx - s, cy - s//3), (cx + s, cy - s//3), (cx, cy + s)], fill=color)


def draw_thought_bubble(draw, x, y, text, f, w=400, h=100):
    """Speech/thought bubble."""
    # Main bubble
    draw.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=WHITE, outline=DIM, width=2)
    # Tail (three circles)
    for i, (dx, dy, r) in enumerate([(w//2, h, 12), (w//2 - 20, h + 18, 8), (w//2 - 35, h + 30, 5)]):
        draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=WHITE, outline=DIM, width=1)
    # Text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        draw.text((x + 20, y + 15 + i * 28), line, font=f, fill=BLACK)


def draw_speech_bubble(draw, x, y, text, f, w=400, h=80, tail_dir="down"):
    """Speech bubble with pointed tail."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=WHITE, outline=DIM, width=2)
    # Pointed tail
    if tail_dir == "down":
        tx = x + w // 2
        ty = y + h
        draw.polygon([(tx - 10, ty - 2), (tx + 10, ty - 2), (tx, ty + 20)], fill=WHITE, outline=DIM)
        draw.line([(tx - 8, ty), (tx + 8, ty)], fill=WHITE, width=3)
    elif tail_dir == "left":
        tx = x
        ty = y + h // 2
        draw.polygon([(tx + 2, ty - 10), (tx + 2, ty + 10), (tx - 20, ty)], fill=WHITE, outline=DIM)
        draw.line([(tx, ty - 8), (tx, ty + 8)], fill=WHITE, width=3)
    draw.text((x + 18, y + 15), text, font=f, fill=BLACK)


def draw_floating_item(draw, x, y, text, color, angle=0, scale=1.0):
    """A floating sticky note / bill / task card."""
    s = scale
    w, h = int(130 * s), int(80 * s)
    # Slight rotation effect via offset
    ox = int(10 * math.sin(angle))
    oy = int(5 * math.cos(angle))
    draw.rounded_rectangle([x + ox, y + oy, x + w + ox, y + h + oy],
                           radius=8, fill=color, outline=(*BLACK[:3], 40), width=1)
    draw.text((x + 10 + ox, y + 15 + oy), text, font=fnt(int(16*s)), fill=BLACK)


# ═══════════════════════════════════════════════════════════════════════════
# SCENE BACKGROUNDS
# ═══════════════════════════════════════════════════════════════════════════

def bg_bedroom(draw, t):
    """Cozy bedroom background."""
    # Wall
    draw.rectangle([0, 0, W, H * 0.6], fill=WALL)
    # Floor
    draw.rectangle([0, int(H * 0.6), W, H], fill=FLOOR)
    # Baseboard
    draw.rectangle([0, int(H * 0.6) - 5, W, int(H * 0.6) + 8], fill=(180, 170, 160))
    # Window
    wx, wy = 650, 250
    ww, wh = 300, 350
    draw.rounded_rectangle([wx, wy, wx+ww, wy+wh], radius=10, fill=SKY_BLUE, outline=(180,180,180), width=4)
    draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill=(180,180,180), width=3)
    draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill=(180,180,180), width=3)
    # Sun in window
    draw.ellipse([wx+ww-90, wy+30, wx+ww-30, wy+90], fill=YELLOW)
    # Bed
    bx, by = 80, int(H * 0.6) - 200
    bw, bh = 500, 200
    # Bed frame
    draw.rounded_rectangle([bx-20, by+bh-30, bx+bw+20, by+bh+50], radius=10, fill=DESK_COLOR)
    # Mattress
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=15, fill=BED_COLOR)
    # Pillow
    draw.rounded_rectangle([bx+20, by+20, bx+160, by+80], radius=20, fill=PILLOW)
    # Blanket
    draw.rounded_rectangle([bx+10, by+bh//2, bx+bw-10, by+bh-10], radius=10, fill=(160, 185, 215))
    # Nightstand
    nx, ny = bx + bw + 40, by + bh - 120
    draw.rounded_rectangle([nx, ny, nx+100, ny+120], radius=8, fill=DESK_COLOR)
    # Alarm clock on nightstand
    draw.ellipse([nx+25, ny-40, nx+75, ny+10], fill=WHITE, outline=BLACK, width=2)
    draw.text((nx+35, ny-30), "7:00", font=fnt(14), fill=BLACK)


def bg_office(draw, t):
    """Office / desk background."""
    draw.rectangle([0, 0, W, H * 0.55], fill=(240, 240, 248))
    draw.rectangle([0, int(H * 0.55), W, H], fill=(210, 205, 200))
    draw.rectangle([0, int(H * 0.55) - 4, W, int(H * 0.55) + 6], fill=(190, 185, 180))
    # Desk
    dx, dy = 50, int(H * 0.55) - 80
    draw.rounded_rectangle([dx, dy, W - dx, dy + 40], radius=5, fill=DESK_COLOR)
    # Desk legs
    draw.rectangle([dx + 30, dy + 40, dx + 50, dy + 250], fill=(150, 115, 75))
    draw.rectangle([W - dx - 50, dy + 40, W - dx - 30, dy + 250], fill=(150, 115, 75))
    # Monitor
    mx, my = W//2 - 150, dy - 250
    draw.rounded_rectangle([mx, my, mx+300, my+200], radius=10, fill=BLACK)
    draw.rounded_rectangle([mx+8, my+8, mx+292, my+192], radius=6, fill=SCREEN_BG)
    # Monitor stand
    draw.rectangle([W//2 - 15, my+200, W//2 + 15, dy], fill=(100, 100, 110))
    draw.rounded_rectangle([W//2 - 60, dy - 10, W//2 + 60, dy], radius=3, fill=(100, 100, 110))
    # Keyboard
    draw.rounded_rectangle([W//2 - 100, dy - 60, W//2 + 100, dy - 30], radius=5, fill=(60, 60, 70))
    # Coffee mug
    draw.rounded_rectangle([W - 200, dy - 50, W - 150, dy], radius=5, fill=WHITE, outline=DIM, width=2)
    draw.arc([W - 148, dy - 42, W - 130, dy - 12], -90, 90, fill=DIM, width=3)


def bg_park(draw, t):
    """Happy outdoor park background."""
    # Sky gradient
    for y in range(int(H * 0.55)):
        p = y / (H * 0.55)
        c = col_lerp((135, 206, 250), (200, 230, 255), p)
        draw.rectangle([0, y, W, y + 1], fill=c)
    # Sun
    draw.ellipse([W - 250, 100, W - 100, 250], fill=YELLOW)
    # Rays
    for a in range(0, 360, 30):
        rad = math.radians(a)
        sx = W - 175 + int(90 * math.cos(rad))
        sy = 175 + int(90 * math.sin(rad))
        ex = W - 175 + int(130 * math.cos(rad))
        ey = 175 + int(130 * math.sin(rad))
        draw.line([(sx, sy), (ex, ey)], fill=(*YELLOW, 150), width=3)
    # Clouds
    for cx, cy, sc in [(200, 180, 1.0), (600, 120, 0.8), (900, 200, 0.7)]:
        r = int(50 * sc)
        for dx, dy in [(-r, 0), (0, -r//2), (r, 0), (r//2, r//3)]:
            draw.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=WHITE)
    # Grass
    draw.rectangle([0, int(H * 0.55), W, H], fill=(120, 200, 100))
    # Grass tufts
    for i in range(20):
        gx = (i * 60 + int(t * 10)) % (W + 40) - 20
        gy = int(H * 0.55) - 5
        for dx in [-5, 0, 5]:
            draw.line([(gx + dx, gy + 10), (gx + dx - 3, gy - 10)], fill=(80, 170, 70), width=2)
    # Trees
    for tx, ts in [(100, 1.2), (W - 150, 1.0)]:
        # Trunk
        tw_t = int(20 * ts)
        th = int(150 * ts)
        ty = int(H * 0.55) - th
        draw.rectangle([tx - tw_t, ty, tx + tw_t, int(H * 0.55) + 10], fill=(120, 80, 40))
        # Crown
        cr = int(80 * ts)
        draw.ellipse([tx - cr, ty - cr, tx + cr, ty + cr//2], fill=(60, 160, 80))
        draw.ellipse([tx - cr + 20, ty - cr - 20, tx + cr - 20, ty + cr//2 - 30], fill=(80, 180, 90))
    # Path
    draw.rounded_rectangle([W//2 - 100, int(H * 0.55), W//2 + 100, H],
                           radius=50, fill=(190, 180, 160))
    # Bench
    bx = W // 2 - 180
    by = int(H * 0.55) + 50
    draw.rounded_rectangle([bx, by, bx + 360, by + 20], radius=5, fill=(140, 100, 60))
    draw.rounded_rectangle([bx, by + 25, bx + 360, by + 40], radius=5, fill=(140, 100, 60))
    draw.rectangle([bx + 20, by + 40, bx + 35, by + 90], fill=(120, 80, 40))
    draw.rectangle([bx + 325, by + 40, bx + 340, by + 90], fill=(120, 80, 40))
    # Back rest
    draw.rounded_rectangle([bx, by - 60, bx + 360, by], radius=5, fill=(140, 100, 60))


def bg_glow_dark(draw, t):
    """Dark bg with animated glow for the app reveal."""
    draw.rectangle([0, 0, W, H], fill=NIGHT_BLUE)


# ═══════════════════════════════════════════════════════════════════════════
# STORY SCENES
# ═══════════════════════════════════════════════════════════════════════════

def scene_01_wake(t, dur):
    """ACT 1: Character sleeping, alarm goes off, wakes up groggy."""
    img = Image.new("RGB", (W, H), WALL)
    draw = ImageDraw.Draw(img)
    bg_bedroom(draw, t)

    char_x, char_y = 330, int(H * 0.6) + 20

    if t < 1.5:
        # Sleeping in bed
        draw_character(draw, 280, int(H * 0.6) - 40, scale=0.8,
                       emotion="sleeping", body_tilt=-80)
    elif t < 2.5:
        # Alarm! shake
        p = (t - 1.5) / 1.0
        shake = int(8 * math.sin(p * 30))
        draw_character(draw, 280 + shake, int(H * 0.6) - 40, scale=0.8,
                       emotion="shocked", body_tilt=-80 + 40 * ease_out(p))
        # Alarm text
        draw_speech_bubble(draw, 600, 680, "ДЗЫНЬ!! 7:00", fnt(22), w=280, h=55)
    else:
        # Getting up, groggy
        p = ease_out((t - 2.5) / 1.5)
        tilt = lerp(-40, 0, p)
        draw_character(draw, int(lerp(280, char_x, p)),
                       int(lerp(int(H*0.6)-40, char_y, p)),
                       scale=lerp(0.8, 1.0, p),
                       emotion="sad", body_tilt=tilt,
                       blink=(t % 1.0 < 0.15))
        if t > 3.5:
            draw_thought_bubble(draw, 450, 550, "Столько дел...\nСтолько счетов...", fnt(20, False))

    # Title overlay
    if t < 1.0:
        p = ease_out(t / 0.5)
        draw_centered(draw, int(lerp(-60, 100, p)), "Понедельник, 7:00", fnt(38),
                      fill=col_lerp(WALL, BLACK, p))

    return img


def scene_02_chaos(t, dur):
    """ACT 2: At desk, tasks & bills flying everywhere, STRESS."""
    img = Image.new("RGB", (W, H), (240, 240, 248))
    draw = ImageDraw.Draw(img)
    bg_office(draw, t)

    char_x = W // 2
    char_y = int(H * 0.55) + 200

    # Character getting more stressed
    stress_p = min(1.0, t / dur)
    arm = int(10 * math.sin(t * 3))
    tilt = int(5 * math.sin(t * 2))

    emotion = "neutral" if t < 1.5 else "stressed"
    draw_character(draw, char_x, char_y, scale=1.0,
                   emotion=emotion, arm_angle=arm, body_tilt=tilt,
                   look_dir=math.sin(t * 2))

    # Flying sticky notes and bills
    items = [
        ("₽12 000\nАренда", YELLOW, 0.3),
        ("Купить еду", (255, 200, 200), 0.8),
        ("СЧЁТ\n₽3 500", (200, 255, 200), 1.3),
        ("Отчёт!!!", (255, 220, 180), 1.8),
        ("₽850 интернет", (220, 200, 255), 2.3),
        ("Встреча 15:00", PINK, 2.8),
        ("ДЕДЛАЙН!", (255, 180, 180), 3.3),
        ("₽15 000\nНалоги", (180, 230, 255), 3.8),
    ]

    for txt, color, delay in items:
        bt = t - delay
        if bt <= 0: continue
        p = ease_out(bt / 0.5)
        # Items fly in from random positions
        rng = random.Random(hash(txt))
        start_x = rng.randint(-200, W + 200)
        start_y = rng.randint(-200, 300)
        end_x = rng.randint(50, W - 200)
        end_y = rng.randint(200, int(H * 0.5) - 100)
        x = int(lerp(start_x, end_x, p))
        y = int(lerp(start_y, end_y, p))
        angle = bt * 2 + rng.random() * 3
        draw_floating_item(draw, x, y, txt, color, angle=angle, scale=0.85)

    # Increasing chaos - more items spin
    if t > 3.0:
        # Exclamation marks
        for i in range(int((t - 3.0) * 3)):
            rng = random.Random(42 + i)
            ex = rng.randint(100, W - 100)
            ey = rng.randint(100, 600)
            draw.text((ex, ey), "!" if rng.random() > 0.5 else "?",
                      font=fnt(rng.randint(30, 60)), fill=RED)

    return img


def scene_03_breakdown(t, dur):
    """ACT 3: Breaking point — overwhelmed, head in hands."""
    img = Image.new("RGB", (W, H), (240, 240, 248))
    draw = ImageDraw.Draw(img)
    bg_office(draw, t)

    char_x = W // 2
    char_y = int(H * 0.55) + 200

    if t < 1.5:
        # Sinking posture
        p = ease_in(t / 1.5)
        draw_character(draw, char_x, char_y, scale=1.0,
                       emotion="stressed", body_tilt=int(lerp(0, 15, p)),
                       arm_angle=int(lerp(0, 60, p)))
        # Spinning symbols around head
        for i in range(5):
            angle = t * 3 + i * (2 * math.pi / 5)
            r = 80
            hx = char_x + int(r * math.cos(angle))
            hy = int(H * 0.55) - 50 + int(r * 0.5 * math.sin(angle))
            symbols = ["₽", "!", "?", "✗", "⏰"]
            draw.text((hx, hy), symbols[i], font=fnt(28), fill=RED)
    else:
        # Sad, slumped
        draw_character(draw, char_x, char_y, scale=1.0,
                       emotion="sad", body_tilt=15, arm_angle=50)
        # Thought bubble
        p = ease_out((t - 1.5) / 0.8)
        if p > 0:
            draw_thought_bubble(draw, 150, 350,
                                "Должен быть\nспособ проще...", fnt(22, False),
                                w=320, h=80)

    # Dim/vignette overlay
    if t > 2.0:
        vp = ease_out((t - 2.0) / 1.0)
        overlay = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.blend(img, overlay, min(0.3, vp * 0.3))

    return img


def scene_04_discovery(t, dur):
    """ACT 4: Phone notification — discovers Todo Budget!"""
    img = Image.new("RGB", (W, H), NIGHT_BLUE)
    draw = ImageDraw.Draw(img)

    # Dark with central glow
    cx, cy = W // 2, H // 2
    glow_r = int(lerp(0, 600, ease_out(t / 2.0)))
    for r in range(glow_r, 0, -3):
        a = 0.08 * (r / max(glow_r, 1))
        c = tuple(int(ch * a) for ch in PURPLE)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)

    # Phone in center, growing
    if t > 0.5:
        p = ease_back((t - 0.5) / 0.5)
        ps = lerp(0, 1, p)
        ph_w = int(200 * ps)
        ph_h = int(380 * ps)
        px = cx - ph_w // 2
        py = cy - ph_h // 2 - 100

        # Phone body
        draw.rounded_rectangle([px, py, px + ph_w, py + ph_h],
                               radius=int(20 * ps), fill=(30, 30, 40),
                               outline=(80, 80, 100), width=3)
        # Screen
        if ps > 0.3:
            sx, sy = px + 8, py + 30
            sw, sh = ph_w - 16, ph_h - 60
            draw.rounded_rectangle([sx, sy, sx + sw, sy + sh],
                                   radius=int(10 * ps), fill=SCREEN_BG)

            # App content appearing
            if t > 1.5:
                ap = ease_out((t - 1.5) / 0.8)
                # Purple header
                draw.rounded_rectangle([sx + 5, sy + 5, sx + sw - 5, sy + int(60 * ap)],
                                       radius=8, fill=PURPLE)
                if ap > 0.3:
                    draw.text((sx + 15, sy + 12), "Todo Budget", font=fnt(int(20*ps)), fill=WHITE)
                    draw.text((sx + 15, sy + 35), "✓", font=fnt(int(16*ps)), fill=WHITE)

                # Task cards
                if t > 2.3:
                    cp = ease_out((t - 2.3) / 0.6)
                    for i in range(3):
                        if cp > i * 0.3:
                            cy_card = sy + 75 + i * 50
                            draw.rounded_rectangle([sx+10, cy_card, sx+sw-10, cy_card+40],
                                                   radius=6, fill=(40, 40, 60))
                            colors = [GREEN, ORANGE, CYAN]
                            draw.rounded_rectangle([sx+15, cy_card+12, sx+25, cy_card+22],
                                                   radius=3, fill=colors[i])

                # Balance
                if t > 3.0:
                    bp = ease_out((t - 3.0) / 0.5)
                    by_b = sy + sh - int(80 * bp)
                    draw.rounded_rectangle([sx+10, by_b, sx+sw-10, by_b+60], radius=8, fill=(20, 50, 35))
                    if bp > 0.3:
                        draw.text((sx+20, by_b+8), "₽42 350", font=fnt(int(22*ps)), fill=GREEN)
                        draw.text((sx+20, by_b+35), "↑ +12%", font=fnt(int(12*ps)), fill=GREEN)

        # Phone glow pulse
        glow_p = 0.5 + 0.5 * math.sin(t * 4)
        for gr in range(80, 0, -2):
            ga = glow_p * 0.02 * (gr / 80)
            gc = tuple(int(ch * ga) for ch in PURPLE)
            draw.ellipse([px + ph_w//2 - gr, py + ph_h//2 - gr,
                          px + ph_w//2 + gr, py + ph_h//2 + gr], fill=gc)

    # Character looking at phone (from side)
    if t > 1.0:
        cp = ease_out((t - 1.0) / 0.8)
        char_x = int(lerp(W + 100, cx + 200, cp))
        char_y = cy + 350
        emotion = "neutral" if t < 2.5 else "shocked" if t < 3.5 else "happy"
        draw_character(draw, char_x, char_y, scale=0.9,
                       emotion=emotion, look_dir=-1,
                       holding="phone" if t < 1.5 else None)

    # Text reveal
    if t > 3.5:
        tp = ease_out((t - 3.5) / 0.5)
        draw_centered(draw, int(lerp(H - 100, cy + 280, tp)),
                      "Todo Budget", fnt(52), col_lerp(NIGHT_BLUE, WHITE, tp))
        if t > 4.0:
            tp2 = ease_out((t - 4.0) / 0.5)
            draw_centered(draw, cy + 350, "Задачи · Бюджет · Помодоро · Заметки",
                          fnt(24, False), col_lerp(NIGHT_BLUE, DIM, tp2))

    return img


def scene_05_transform(t, dur):
    """ACT 5: Transformation montage — organizing with the app."""
    img = Image.new("RGB", (W, H), WARM_BG)
    draw = ImageDraw.Draw(img)

    # Clean, warm background
    # Subtle pattern
    for i in range(0, W, 60):
        draw.line([(i, 0), (i, H)], fill=(*SHADOW, 20), width=1)
    for i in range(0, H, 60):
        draw.line([(0, i), (W, i)], fill=(*SHADOW, 20), width=1)

    center_y = H // 2

    if t < 2.5:
        # Phase 1: Task being organized
        draw_centered(draw, 200, "✅ Задачи", fnt(50), PURPLE)

        tasks = [
            ("Оплатить аренду", RED, "Высокий"),
            ("Купить продукты", ORANGE, "Средний"),
            ("Позвонить маме", GREEN, "Низкий"),
        ]
        for i, (task, col, prio) in enumerate(tasks):
            bt = t - 0.3 - i * BEAT
            if bt <= 0: continue
            p = ease_back(bt / 0.3)
            y = 350 + i * 140
            x_off = int(lerp(W + 50, 0, p))
            # Card
            draw.rounded_rectangle([80 + x_off, y, 1000 + x_off, y + 110],
                                   radius=18, fill=WHITE, outline=(*col, 60), width=2)
            # Checkbox
            draw.rounded_rectangle([110 + x_off, y + 35, 140 + x_off, y + 65],
                                   radius=6, outline=col, width=3)
            if i == 1 and bt > 0.8:
                # Check animation
                cp = ease_out((bt - 0.8) / 0.3)
                draw.text((112 + x_off, y + 28), "✓", font=fnt(28), fill=col_lerp(WHITE, GREEN, cp))
            draw.text((160 + x_off, y + 30), task, font=fnt(26), fill=BLACK)
            draw.text((160 + x_off, y + 65), f"Приоритет: {prio}", font=fnt(16, False), fill=DIM)
            # Priority dot
            draw.ellipse([920 + x_off, y + 42, 950 + x_off, y + 62], fill=col)

    elif t < 5.0:
        # Phase 2: Budget tracking
        phase_t = t - 2.5
        draw_centered(draw, 200, "💰 Финансы", fnt(50), GREEN)

        # Balance card
        bp = ease_back(phase_t / 0.3)
        y_off = int(lerp(100, 0, bp))
        draw.rounded_rectangle([80, 350 + y_off, 1000, 530 + y_off],
                               radius=22, fill=WHITE, outline=(*GREEN, 40), width=2)
        draw.text((130, 380 + y_off), "Баланс", font=fnt(22, False), fill=DIM)
        # Counter
        val = int(42350 * min(1, max(0, phase_t - 0.3) / 0.8))
        if val > 0:
            draw.text((130, 420 + y_off), f"₽{val:,}".replace(",", " "),
                      font=fnt(60), fill=GREEN)

        # Category bars
        cats = [
            ("Еда", 420, RED, "₽8 500"),
            ("Транспорт", 300, ORANGE, "₽5 200"),
            ("Развлечения", 200, CYAN, "₽3 100"),
        ]
        for i, (cat, max_w, col, amt) in enumerate(cats):
            ct = phase_t - 1.0 - i * 0.3
            if ct <= 0: continue
            p = ease_out(ct / 0.5)
            y = 600 + i * 70
            w = int(max_w * p)
            draw.text((130, y), cat, font=fnt(20, False), fill=DIM)
            draw.rounded_rectangle([260, y, 260 + w, y + 28], radius=10, fill=col)
            if p > 0.5:
                draw.text((270 + max_w, y + 2), amt, font=fnt(18, False), fill=DIM)

    else:
        # Phase 3: Pomodoro + Notes
        phase_t = t - 5.0
        draw_centered(draw, 200, "⏱ Помодоро + 📝 Заметки", fnt(40), RED)

        # Timer
        tp = ease_out(phase_t / 0.5)
        cx, cy_t = W // 2, 550
        r = int(140 * tp)
        if r > 5:
            draw.ellipse([cx - r, cy_t - r, cx + r, cy_t + r], outline=(*RED, 40), width=4)
            progress = ease_out(phase_t / dur) * 0.7
            draw.arc([cx - r, cy_t - r, cx + r, cy_t + r], -90, -90 + 360 * progress,
                     fill=RED, width=8)
            m = int(25 * (1 - progress))
            draw.text((cx - 60, cy_t - 25), f"{m:02d}:00", font=fnt(50), fill=BLACK)

        # Note card
        if phase_t > 1.0:
            np_ = ease_back((phase_t - 1.0) / 0.3)
            y_off = int(lerp(80, 0, np_))
            draw.rounded_rectangle([80, 780 + y_off, 1000, 930 + y_off],
                                   radius=18, fill=WHITE, outline=(*CYAN, 40), width=2)
            draw.text((130, 810 + y_off), "📝 Идея: Новый проект", font=fnt(24), fill=BLACK)
            draw.text((130, 850 + y_off), "Нужно обсудить с командой", font=fnt(18, False), fill=DIM)
            draw.text((130, 885 + y_off), "Сегодня, 14:32 · Голосовая заметка 🎤",
                      font=fnt(14, False), fill=CYAN)

    # Character at the side, progressively happier
    emotion = "neutral" if t < 2.0 else "happy" if t < 4.0 else "love"
    char_x = 900 if t < 2.5 else 160 if t < 5.0 else 900
    bob = int(5 * math.sin(t * 2))
    draw_character(draw, char_x, 1500 + bob, scale=0.7,
                   emotion=emotion, look_dir=-1 if char_x > W//2 else 1,
                   arm_angle=int(10 * math.sin(t * 1.5)))

    return img


def scene_06_happy(t, dur):
    """ACT 6: Happy ending — character in park, everything is great."""
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    bg_park(draw, t)

    char_x = W // 2
    char_y = int(H * 0.55) + 200
    bob = int(8 * math.sin(t * 2.5))
    jump = int(max(0, 30 * math.sin(t * 1.5))) if t > 1.5 else 0

    # Happy Character
    draw_character(draw, char_x, char_y + bob, scale=1.1,
                   emotion="happy" if t < 3.0 else "love",
                   jump=jump,
                   arm_angle=int(20 + 15 * math.sin(t * 2)),
                   holding="phone",
                   look_dir=0.3 * math.sin(t))

    # Floating feature badges
    if t > 1.0:
        badges = [
            ("✅ Задачи", GREEN, -250, -380),
            ("💰 Бюджет", ORANGE, 200, -350),
            ("⏱ Помодоро", RED, -280, -200),
            ("📝 Заметки", CYAN, 230, -180),
        ]
        for i, (txt, col, dx, dy) in enumerate(badges):
            bt = t - 1.0 - i * 0.3
            if bt <= 0: continue
            p = ease_back(bt / 0.4)
            bx = char_x + dx
            by = char_y + dy + int(8 * math.sin(t * 1.5 + i))
            scale_f = lerp(0, 1, p)
            if scale_f > 0.1:
                bw = int(200 * scale_f)
                bh = int(50 * scale_f)
                draw.rounded_rectangle([bx - bw//2, by - bh//2, bx + bw//2, by + bh//2],
                                       radius=bh//2, fill=WHITE, outline=col, width=3)
                if scale_f > 0.5:
                    draw.text((bx - tw(draw, txt, fnt(int(20*scale_f)))//2,
                               by - int(12*scale_f)), txt,
                              font=fnt(int(20*scale_f)), fill=col)

    # Floating hearts
    if t > 2.5:
        for i in range(5):
            rng = random.Random(700 + i)
            hx = rng.randint(100, W - 100)
            speed = rng.uniform(100, 200)
            hy = int(H * 0.55) - int((t - 2.5) * speed) % int(H * 0.6)
            sz = rng.randint(10, 20)
            draw_heart(draw, hx, hy, sz, PINK)

    # Text
    if t > 3.0:
        p = ease_out((t - 3.0) / 0.5)
        draw_centered(draw, int(lerp(120, 80, p)), "Всё под контролем!", fnt(44),
                      col_lerp(SKY_BLUE, BLACK, p))

    return img


def scene_07_cta(t, dur):
    """ACT 7: Final CTA screen."""
    img = Image.new("RGB", (W, H), NIGHT_BLUE)
    draw = ImageDraw.Draw(img)

    # Glow
    cx, cy = W // 2, H // 2
    pulse = 0.05 + 0.03 * math.sin(t * 3)
    for r in range(500, 0, -3):
        a = pulse * (r / 500)
        c = tuple(int(ch * a) for ch in PURPLE)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)

    # App icon
    p0 = ease_back(t / 0.4)
    sz = int(150 * p0)
    if sz > 5:
        r = sz // 2
        draw.rounded_rectangle([cx-r, 500-r, cx+r, 500+r], radius=max(5, int(sz*0.28)), fill=PURPLE)
        cf = fnt(int(sz * 0.55))
        draw.text((cx - tw(draw, "✓", cf)//2, 500 - 38), "✓", font=cf, fill=WHITE)

    # App name
    if t > 0.5:
        np_ = ease_back((t - 0.5) / 0.3)
        scale = max(1, lerp(2.5, 1, np_))
        draw_centered(draw, int(lerp(550, 640, ease_out((t-0.5)/0.3))),
                      "Todo Budget", fnt(int(72 * scale)), WHITE)
        if t < 0.6:
            img = ImageChops.offset(img, int(random.gauss(0, 15)), int(random.gauss(0, 15)))
            draw = ImageDraw.Draw(img)

    # Subtitle
    if t > 1.2:
        p = ease_out((t - 1.2) / 0.3)
        draw_centered(draw, 750, "Задачи · Бюджет · Помодоро · Заметки",
                      fnt(26, False), col_lerp(NIGHT_BLUE, DIM, p))

    # Stats
    if t > 2.0:
        stats = [("0 ₽", "Навсегда", GREEN), ("9 МБ", "Размер", CYAN), ("4 в 1", "Функции", PURPLE)]
        for i, (val, label, col) in enumerate(stats):
            st = t - 2.0 - i * 0.3
            if st <= 0: continue
            p = ease_elastic(st / 0.4)
            bx = 100 + i * 330
            by = 870
            draw.rounded_rectangle([bx, by, bx + 280, by + 110],
                                   radius=18, fill=(30, 30, 55))
            draw_f = fnt(int(42 * p))
            draw.text((bx + 140 - tw(draw, val, draw_f)//2, by + 10), val, font=draw_f, fill=col)
            draw.text((bx + 140 - tw(draw, label, fnt(18, False))//2, by + 65),
                      label, font=fnt(18, False), fill=DIM)

    # CTA Button
    if t > 3.0:
        bp = ease_back((t - 3.0) / 0.3)
        by = int(lerp(1200, 1080, bp))
        bw, bh = 520, 86
        draw.rounded_rectangle([cx - bw//2, by, cx + bw//2, by + bh],
                               radius=bh//2, fill=PURPLE)
        draw_centered(draw, by + 20, "📲 Скачать в RuStore", fnt(30), WHITE, shadow=False)

    # URL
    if t > 3.8:
        p = ease_out((t - 3.8) / 0.3)
        draw_centered(draw, 1200, "emil-a-dev.github.io/todofin",
                      fnt(22, False), col_lerp(NIGHT_BLUE, CYAN, p))

    # Link hint
    if t > 4.5:
        a = 0.5 + 0.5 * math.sin((t - 4.5) * 3)
        draw_centered(draw, 1300, "Ссылка в описании ↓",
                      fnt(22, False), col_lerp(NIGHT_BLUE, DIM, a))

    # Small character at bottom, waving
    if t > 2.5:
        cp = ease_out((t - 2.5) / 0.5)
        char_y = int(lerp(H + 100, H - 180, cp))
        draw_character(draw, cx, char_y, scale=0.55,
                       emotion="happy", arm_angle=int(40 + 20 * math.sin(t * 3)),
                       shirt_color=SHIRT_BLUE)

    return img


# ═══════════════════════════════════════════════════════════════════════════
# TIMELINE
# ═══════════════════════════════════════════════════════════════════════════

TIMELINE = [
    (scene_01_wake,      5.0,  "flash"),    # 0-5     Morning
    (scene_02_chaos,     5.0,  "glitch"),   # 5-10    Chaos
    (scene_03_breakdown, 3.5,  "flash"),    # 10-13.5 Breakdown
    (scene_04_discovery, 5.5,  "flash"),    # 13.5-19 Discovery
    (scene_05_transform, 7.5,  "flash"),    # 19-26.5 Transformation
    (scene_06_happy,     5.0,  "flash"),    # 26.5-31.5 Happy ending
    (scene_07_cta,       6.5,  "flash"),    # 31.5-38  CTA
]

TOTAL_DUR = sum(d for _, d, _ in TIMELINE)
TRANS_DUR = 0.15


# ═══════════════════════════════════════════════════════════════════════════
# MUSIC — Emotional arc: calm → tense → discovery → upbeat → peaceful
# ═══════════════════════════════════════════════════════════════════════════

def generate_story_music():
    """Generate music that follows the emotional arc."""
    from pydub import AudioSegment
    sr = 44100
    total_ms = int(TOTAL_DUR * 1000) + 3000

    def synth(freq, dur_ms, vol=0.3, attack=0.02, decay=0.1):
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env_a = np.minimum(t / attack, 1.0)
        env_d = np.exp(-np.maximum(t - (dur_ms/1000 - decay), 0) / decay * 5)
        env = env_a * env_d
        sig = env * np.sin(2 * np.pi * freq * t) * vol
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(),
                            frame_rate=sr, sample_width=2, channels=1)

    def make_kick(dur_ms=120):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = np.exp(-t * 25)
        freq = 50 * (1 + 5 * np.exp(-t * 30))
        sig = np.tanh(env * np.sin(2*np.pi*np.cumsum(freq)/sr) * 3) * 0.7
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_snare(dur_ms=80):
        n = int(sr*dur_ms/1000)
        t = np.linspace(0, dur_ms/1000, n)
        env = np.exp(-t * 25)
        sig = env * (np.random.uniform(-1,1,n)*0.6 + np.sin(2*np.pi*180*t)*0.4) * 0.5
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_hh(dur_ms=30):
        n = int(sr*dur_ms/1000)
        sig = np.random.uniform(-1,1,n) * np.exp(-np.linspace(0,12,n)) * 0.15
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_pad(dur_ms, freq, vol=0.1):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = (1-np.exp(-t*1.5)) * np.exp(-t*0.1)
        s = (np.sin(2*np.pi*freq*t) + np.sin(2*np.pi*freq*1.003*t) + np.sin(2*np.pi*freq*0.997*t))/3
        sig = env * s * vol
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_bell(freq, dur_ms=800, vol=0.15):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = np.exp(-t * 4)
        sig = env * (np.sin(2*np.pi*freq*t) + 0.5*np.sin(2*np.pi*freq*2*t) + 0.25*np.sin(2*np.pi*freq*3*t)) / 1.75 * vol
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_impact():
        dur_ms = 600
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        sig = np.exp(-t*6)*np.sin(2*np.pi*30*t)*0.8 + np.exp(-t*15)*np.random.uniform(-1,1,len(t))*0.4
        sig = np.tanh(sig*2)*0.9
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_riser(dur_ms=2000):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = (t / t[-1]) ** 2
        freq = 200 + 3000 * (t/t[-1])**3
        sig = env * np.sin(2*np.pi*np.cumsum(freq)/sr) * 0.25
        sig += env * np.random.uniform(-1,1,len(t)) * 0.08
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    track = AudioSegment.silent(duration=total_ms)
    kick = make_kick()
    snare = make_snare()
    hh = make_hh()
    impact = make_impact()
    riser = make_riser(2500)

    beat_ms = int(BEAT * 1000)
    half = beat_ms // 2

    # Scene start times
    scene_starts = []
    acc = 0
    for _, d, _ in TIMELINE:
        scene_starts.append(acc)
        acc += d
    # scene_starts: [0, 5, 10, 13.5, 19, 26.5, 31.5]

    # ── ACT 1: Calm morning (0-5s) — soft pad + gentle bell melody
    calm_pad = make_pad(5000, 220, vol=0.06)  # A3
    track = track.overlay(calm_pad, position=0)
    calm_pad2 = make_pad(5000, 165, vol=0.04)  # E3
    track = track.overlay(calm_pad2, position=500)
    # Bell melody
    melody_calm = [440, 523, 587, 523, 440]
    for i, note in enumerate(melody_calm):
        bell = make_bell(note, 600, vol=0.08)
        track = track.overlay(bell, position=1000 + i * 800)
    # Alarm at 1.5s
    alarm = synth(880, 300, vol=0.3)
    track = track.overlay(alarm, position=1500)
    track = track.overlay(alarm, position=1800)

    # ── ACT 2: Building tension (5-13.5s) — drums get louder, dissonant pads
    tense_start = int(scene_starts[1] * 1000)
    tense_end = int(scene_starts[3] * 1000)
    # Kick pattern — every beat, intensifying
    for b in range((tense_end - tense_start) // beat_ms + 1):
        pos = tense_start + b * beat_ms
        progress = b / max(1, (tense_end - tense_start) // beat_ms)
        k_vol = int(-6 + progress * 6)  # gets louder
        track = track.overlay(kick + k_vol, position=pos)
        if b % 2 == 1:
            track = track.overlay(snare + k_vol, position=pos)
        track = track.overlay(hh - 3, position=pos)
        track = track.overlay(hh - 6, position=pos + half)
    # Tense pad
    tense_pad = make_pad(8000, 110, vol=0.07)  # Low, ominous
    track = track.overlay(tense_pad, position=tense_start)
    tense_pad2 = make_pad(8000, 116.5, vol=0.05)  # Slightly dissonant
    track = track.overlay(tense_pad2, position=tense_start + 500)
    # Riser before discovery
    discovery_ms = int(scene_starts[3] * 1000)
    track = track.overlay(riser - 3, position=max(0, discovery_ms - 2500))

    # ── ACT 3: Discovery impact (13.5s)
    track = track.overlay(impact, position=discovery_ms)
    # Discovery pad — magical
    disc_pad = make_pad(6000, 330, vol=0.08)  # E4
    track = track.overlay(disc_pad, position=discovery_ms + 200)
    disc_pad2 = make_pad(6000, 440, vol=0.06)  # A4
    track = track.overlay(disc_pad2, position=discovery_ms + 500)
    # Bell melody — ascending, hopeful
    hope_notes = [330, 392, 440, 523, 587, 659]
    for i, note in enumerate(hope_notes):
        bell = make_bell(note, 800, vol=0.1)
        track = track.overlay(bell, position=discovery_ms + 500 + i * 600)

    # ── ACT 4: Upbeat transformation (19-31.5s) — full beat, major key
    upbeat_start = int(scene_starts[4] * 1000)
    upbeat_end = int(scene_starts[6] * 1000)
    for b in range((upbeat_end - upbeat_start) // beat_ms + 1):
        pos = upbeat_start + b * beat_ms
        track = track.overlay(kick, position=pos)
        if b % 4 in [1, 3]:
            track = track.overlay(snare, position=pos)
        track = track.overlay(hh, position=pos)
        track = track.overlay(hh - 4, position=pos + half)
        if b % 2 == 1:
            track = track.overlay(hh - 8, position=pos + half // 2)
    # Major key pad
    happy_pad = make_pad(12000, 220, vol=0.08)
    track = track.overlay(happy_pad, position=upbeat_start)
    happy_pad2 = make_pad(12000, 277, vol=0.06)  # C#4 — major third
    track = track.overlay(happy_pad2, position=upbeat_start + 200)
    happy_pad3 = make_pad(12000, 330, vol=0.05)  # E4 — fifth
    track = track.overlay(happy_pad3, position=upbeat_start + 400)
    # Melody line
    happy_melody = [440, 523, 587, 659, 587, 523, 440, 523, 587, 659, 784, 659]
    for i, note in enumerate(happy_melody):
        bell = make_bell(note, 500, vol=0.1)
        track = track.overlay(bell, position=upbeat_start + i * beat_ms)
    # Sub bass
    sub = synth(55, 300, vol=0.3)
    for b in range(0, (upbeat_end - upbeat_start) // beat_ms, 2):
        track = track.overlay(sub, position=upbeat_start + b * beat_ms)

    # ── Scene transition impacts
    for st in scene_starts[1:]:
        track = track.overlay(impact - 3, position=max(0, int(st * 1000) - 30))

    # ── ACT 5: CTA (31.5-38s) — powerful ending
    cta_start = int(scene_starts[6] * 1000)
    track = track.overlay(impact, position=cta_start)
    # Sustained pad
    final_pad = make_pad(7000, 220, vol=0.1)
    track = track.overlay(final_pad, position=cta_start)
    final_pad2 = make_pad(7000, 330, vol=0.08)
    track = track.overlay(final_pad2, position=cta_start + 200)
    # Gentle beat
    for b in range(7000 // beat_ms):
        pos = cta_start + b * beat_ms
        track = track.overlay(kick - 3, position=pos)
        if b % 2 == 1:
            track = track.overlay(snare - 3, position=pos)
        track = track.overlay(hh - 6, position=pos + half)

    # Global mix
    track = track.fade_in(500).fade_out(2500)
    track = track[:total_ms].normalize()

    path = str(OUT_DIR / "story_music.wav")
    track.export(path, format="wav")
    print(f"  Music: {len(track)/1000:.1f}s → {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════
# RENDER + ASSEMBLE
# ═══════════════════════════════════════════════════════════════════════════

def render():
    total_frames = int(TOTAL_DUR * FPS)
    frames_dir = OUT_DIR / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    print(f"  Rendering {total_frames} frames ({TOTAL_DUR:.1f}s)...")

    prev_img = None
    for fi in range(total_frames):
        global_t = fi / FPS
        random.seed(42 + fi)

        # Find scene
        t_acc = 0
        scene_idx = 0
        for idx, (rend, dur, trans) in enumerate(TIMELINE):
            if global_t < t_acc + dur:
                scene_idx = idx
                break
            t_acc += dur
        else:
            scene_idx = len(TIMELINE) - 1

        local_t = global_t - t_acc
        renderer, dur, trans = TIMELINE[scene_idx]
        img = renderer(local_t, dur)

        # Transitions
        if local_t < TRANS_DUR and scene_idx > 0 and prev_img is not None:
            p = local_t / TRANS_DUR
            if trans == "glitch":
                # RGB split
                arr = np.array(img)
                s = int(15 * (1 - p))
                if s > 0:
                    result = arr.copy()
                    result[:, s:, 0] = arr[:, :-s, 0]
                    result[:, :-s, 2] = arr[:, s:, 2]
                    img = Image.fromarray(result)
                img = Image.blend(prev_img, img, p)
            elif trans == "flash":
                img = Image.blend(prev_img, img, p)
                flash_i = 0.4 * (1 - p)
                if flash_i > 0.01:
                    white = Image.new("RGB", (W, H), WHITE)
                    img = Image.blend(img, white, min(1, flash_i))

        # Global fades
        if global_t < 0.5:
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, global_t / 0.5)
        if global_t > TOTAL_DUR - 1.5:
            p = (TOTAL_DUR - global_t) / 1.5
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, max(0, min(1, p)))

        img.save(str(frames_dir / f"f_{fi:05d}.png"), optimize=False)

        if local_t >= dur - 1.0/FPS:
            prev_img = img.copy()

        if fi % (FPS * 3) == 0:
            print(f"    {fi}/{total_frames} ({100*fi//total_frames}%)")

    print(f"  ✅ {total_frames} frames rendered")
    return str(frames_dir)


def assemble(frames_dir, audio_path):
    print(f"  Assembling final video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_dir}/f_%05d.png",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUTPUT)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        sz = os.path.getsize(OUTPUT) / (1024*1024)
        print(f"  ✅ {OUTPUT} ({sz:.1f} MB)")
    else:
        print(f"  ❌ {result.stderr[-400:]}")


def main():
    print("=" * 60)
    print("🎬 TODO BUDGET — CARTOON STORY")
    print("=" * 60)
    print(f"📐 {W}×{H} @ {FPS}fps")
    print(f"⏱  {TOTAL_DUR:.1f}s ({len(TIMELINE)} acts)")
    print(f"🎞  ~{int(TOTAL_DUR * FPS)} frames")
    print()

    print("Story arc:")
    names = ["Wake Up", "Chaos", "Breakdown", "Discovery",
             "Transformation", "Happy Ending", "CTA"]
    t = 0
    for i, (_, dur, trans) in enumerate(TIMELINE):
        print(f"  {t:5.1f}s → {t+dur:5.1f}s  [{names[i]}] ({trans})")
        t += dur
    print()

    print("━" * 40)
    print("1️⃣  Generating story music")
    print("━" * 40)
    audio = generate_story_music()
    print()

    print("━" * 40)
    print("2️⃣  Rendering frames")
    print("━" * 40)
    frames = render()
    print()

    print("━" * 40)
    print("3️⃣  Assembling video")
    print("━" * 40)
    assemble(frames, audio)

    # Cleanup
    shutil.rmtree(OUT_DIR / "frames", ignore_errors=True)
    try: os.remove(str(OUT_DIR / "story_music.wav"))
    except: pass

    print()
    print("=" * 60)
    print("✅ DONE! Cartoon story reel ready.")
    print(f"📁 {OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
