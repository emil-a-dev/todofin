#!/usr/bin/env python3
"""
🎬 Todo Budget — 3D Cartoon Mini-Series (3 episodes × 60s)

Episodes:
  1. "Хаос"      — Meet Лёша, drowning in chaos, everything goes wrong
  2. "Открытие"  — Лёша discovers Todo Budget, life starts changing
  3. "Мастер"    — Лёша becomes a productivity guru, epic transformation

Tech: PIL frame-by-frame 2.5D isometric rendering + edge-tts voiceover + music + SFX

Usage:
  python3 build_series.py          # Build all 3 episodes
  python3 build_series.py 1        # Build episode 1 only
  python3 build_series.py 2 3      # Build episodes 2 and 3
"""

import os, sys, math, random, shutil, subprocess, asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np

W, H = 1080, 1920
FPS = 30
BEAT_MS = 500  # 120 BPM

BASE = Path(__file__).parent
SERIES_DIR = BASE / "series"
SERIES_DIR.mkdir(exist_ok=True)

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ── Palette ─────────────────────────────────────────────────────────────
PURPLE      = (108, 58, 224)
PURPLE_D    = (60, 30, 140)
GREEN       = (60, 200, 130)
CYAN        = (60, 200, 230)
RED         = (230, 80, 80)
ORANGE      = (255, 160, 60)
YELLOW      = (255, 220, 80)
PINK        = (255, 150, 180)
WHITE       = (255, 255, 255)
BLACK       = (30, 30, 30)
SKIN        = (255, 213, 170)
HAIR_BROWN  = (70, 50, 40)
HAIR_BLONDE = (220, 180, 100)
SHIRT_BLUE  = (90, 130, 220)
SHIRT_RED   = (200, 80, 90)
SHIRT_GREEN = (70, 170, 120)
PANTS_DARK  = (60, 70, 90)
SKY         = (135, 206, 235)
WALL        = (250, 245, 240)
FLOOR       = (220, 210, 200)
DESK_COL    = (180, 140, 100)
SHADOW_C    = (200, 200, 210)
DIM         = (150, 150, 170)
NIGHT       = (20, 24, 50)
WARM        = (255, 248, 240)
SCREEN_BG   = (20, 20, 40)

# Font cache
_fc = {}
def fnt(size, bold=True):
    size = max(1, int(size))
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, size)
    return _fc[k]

# ── Easing ──────────────────────────────────────────────────────────────
def ease_out(t): t=max(0,min(1,t)); return 1-(1-t)**3
def ease_in(t): t=max(0,min(1,t)); return t**3
def ease_back(t): t=max(0,min(1,t)); c=1.7; return 1+(c+1)*(t-1)**3+c*(t-1)**2
def ease_elastic(t):
    t=max(0,min(1,t))
    if t<=0 or t>=1: return t
    return 2**(-10*t)*math.sin((t*10-0.75)*2*math.pi/3)+1
def lerp(a,b,t): return a+(b-a)*max(0,min(1,t))
def col_lerp(c1,c2,t): t=max(0,min(1,t)); return tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))

def tw(d, text, f):
    bb = d.textbbox((0,0), text, font=f)
    return bb[2]-bb[0]

def draw_centered(d, y, text, f, fill=BLACK, shadow_col=None):
    w = tw(d, text, f)
    x = (W - w) // 2
    if shadow_col:
        d.text((x+2, y+2), text, font=f, fill=shadow_col)
    d.text((x, y), text, font=f, fill=fill)

# ═══════════════════════════════════════════════════════════════════════════
# VOICE GENERATION with edge-tts
# ═══════════════════════════════════════════════════════════════════════════

VOICE_MALE   = "ru-RU-DmitryNeural"
VOICE_FEMALE = "ru-RU-SvetlanaNeural"
VOICE_NARRATOR = VOICE_MALE  # narrator is also Dmitry but slower

async def generate_voice_line(text, voice, output_path, rate="+0%", pitch="+0Hz"):
    """Generate a single voice line using edge-tts."""
    import edge_tts
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await c.save(str(output_path))

def gen_voice(text, voice, path, rate="+0%", pitch="+0Hz"):
    """Synchronous wrapper for voice generation."""
    asyncio.run(generate_voice_line(text, voice, path, rate, pitch))

def generate_episode_voices(ep_num, lines, voice_dir):
    """
    Generate all voice lines for an episode.
    lines: list of (text, voice_id, rate, pitch, filename)
    Returns: dict of {filename: duration_ms}
    """
    from pydub import AudioSegment
    voice_dir.mkdir(parents=True, exist_ok=True)
    durations = {}

    for i, (text, voice, rate, pitch, fname) in enumerate(lines):
        path = voice_dir / fname
        if not path.exists():
            print(f"    Voice {i+1}/{len(lines)}: {text[:40]}...")
            gen_voice(text, voice, path, rate, pitch)
        audio = AudioSegment.from_mp3(str(path))
        durations[fname] = len(audio)

    return durations


# ═══════════════════════════════════════════════════════════════════════════
# CHARACTER SYSTEM — Reusable 2.5D characters
# ═══════════════════════════════════════════════════════════════════════════

def draw_char(draw, cx, cy, scale=1.0, emotion="neutral", look=-1,
              arm_angle=0, tilt=0, jump=0, blink=False, hair_col=HAIR_BROWN,
              shirt_col=SHIRT_BLUE, skin_col=SKIN, holding=None, walking_phase=0):
    """Universal character drawing with walking animation support."""
    s = scale
    cy -= jump

    # Shadow
    sw = int(55*s)
    sh = int(14*s)
    draw.ellipse([cx-sw, cy-sh//2, cx+sw, cy+sh//2], fill=(*SHADOW_C[:3], 70))

    # Walking leg offset
    lleg_off = int(15 * math.sin(walking_phase) * s) if walking_phase else 0
    rleg_off = int(15 * math.sin(walking_phase + math.pi) * s) if walking_phase else 0

    # Legs
    leg_l = int(80*s)
    leg_w = int(16*s)
    hip_y = cy - leg_l
    # Left
    lx1, ly1 = cx - int(15*s), hip_y
    lx2, ly2 = cx - int(18*s) + lleg_off, cy
    draw.line([(lx1,ly1),(lx2,ly2)], fill=PANTS_DARK, width=leg_w)
    draw.ellipse([lx2-int(24*s), ly2-int(10*s), lx2+int(12*s), ly2+int(8*s)], fill=BLACK)
    # Right
    rx1, ry1 = cx + int(15*s), hip_y
    rx2, ry2 = cx + int(18*s) + rleg_off, cy
    draw.line([(rx1,ry1),(rx2,ry2)], fill=PANTS_DARK, width=leg_w)
    draw.ellipse([rx2-int(12*s), ry2-int(10*s), rx2+int(24*s), ry2+int(8*s)], fill=BLACK)

    # Torso
    bt = hip_y - int(85*s)
    bw = int(50*s)
    tilt_r = math.radians(tilt)
    tilt_x = int(math.sin(tilt_r) * 30 * s)
    draw.rounded_rectangle([cx-bw+tilt_x, bt, cx+bw+tilt_x, hip_y], radius=int(18*s), fill=shirt_col)

    # Arms
    sh_y = bt + int(18*s)
    arm_l = int(65*s)
    aw = int(12*s)
    # Left arm
    la = math.radians(-arm_angle - 15 + tilt)
    lsx = cx - bw + tilt_x
    lax = lsx + arm_l * math.sin(la)
    lay = sh_y + arm_l * math.cos(la)
    draw.line([(lsx,sh_y),(lax,lay)], fill=skin_col, width=aw)
    hr = int(9*s)
    draw.ellipse([lax-hr, lay-hr, lax+hr, lay+hr], fill=skin_col)
    # Right arm
    ra = math.radians(arm_angle + 15 - tilt)
    rsx = cx + bw + tilt_x
    rax = rsx - arm_l * math.sin(ra)
    ray = sh_y + arm_l * math.cos(ra)
    draw.line([(rsx,sh_y),(rax,ray)], fill=skin_col, width=aw)
    draw.ellipse([rax-hr, ray-hr, rax+hr, ray+hr], fill=skin_col)

    # Holding phone
    if holding == "phone":
        pw, ph = int(22*s), int(40*s)
        px, py = int(rax-pw//2), int(ray-ph)
        draw.rounded_rectangle([px,py,px+pw,py+ph], radius=int(4*s), fill=BLACK)
        draw.rounded_rectangle([px+2,py+3,px+pw-2,py+ph-3], radius=int(2*s), fill=SCREEN_BG)
        draw.rounded_rectangle([px+4,py+8,px+pw-4,py+ph//2], radius=int(2*s), fill=PURPLE)
        draw.text((px+6,py+10), "✓", font=fnt(max(8,int(11*s))), fill=WHITE)

    # Neck
    nk_y = bt - int(8*s)
    draw.rectangle([cx-int(8*s)+tilt_x, nk_y, cx+int(8*s)+tilt_x, bt+int(8*s)], fill=skin_col)

    # Head
    hd_r = int(45*s)
    hx = cx + tilt_x
    hy = nk_y - hd_r
    draw.ellipse([hx-hd_r, hy-hd_r, hx+hd_r, hy+hd_r], fill=skin_col)

    # Hair
    hh = int(25*s)
    draw.ellipse([hx-hd_r-int(2*s), hy-hd_r-int(4*s), hx+hd_r+int(2*s), hy-hd_r+hh], fill=hair_col)
    draw.ellipse([hx-hd_r-int(4*s), hy-hd_r, hx-hd_r+int(12*s), hy], fill=hair_col)
    draw.ellipse([hx+hd_r-int(12*s), hy-hd_r, hx+hd_r+int(4*s), hy], fill=hair_col)

    # Eyes
    ey = hy - int(3*s)
    esep = int(18*s)
    er = int(9*s)
    pr = int(4*s)
    loff = int(look * 3 * s)

    if blink or emotion == "sleeping":
        for ex in [hx-esep, hx+esep]:
            draw.line([(ex-er, ey),(ex+er, ey)], fill=BLACK, width=max(1,int(2*s)))
    else:
        for ex in [hx-esep, hx+esep]:
            draw.ellipse([ex-er, ey-er, ex+er, ey+er], fill=WHITE, outline=BLACK, width=max(1,int(2*s)))
            if emotion == "stressed":
                pr2 = int(2*s)
                draw.ellipse([ex+loff-pr2, ey-pr2, ex+loff+pr2, ey+pr2], fill=BLACK)
            elif emotion == "shocked":
                draw.ellipse([ex+loff-pr-2, ey-pr-2, ex+loff+pr+2, ey+pr+2], fill=BLACK)
            else:
                draw.ellipse([ex+loff-pr, ey-pr, ex+loff+pr, ey+pr], fill=BLACK)
                draw.ellipse([ex+loff-1, ey-pr+1, ex+loff+2, ey-pr+3], fill=WHITE)

    # Eyebrows
    bry = ey - int(13*s)
    brw = int(12*s)
    if emotion in ("stressed","sad"):
        draw.line([(hx-esep-brw,bry-int(4*s)),(hx-esep+brw,bry+int(2*s))], fill=hair_col, width=max(1,int(3*s)))
        draw.line([(hx+esep-brw,bry+int(2*s)),(hx+esep+brw,bry-int(4*s))], fill=hair_col, width=max(1,int(3*s)))
    elif emotion in ("happy","love"):
        for ex in [hx-esep, hx+esep]:
            draw.arc([ex-brw, bry-int(6*s), ex+brw, bry+int(3*s)], 180, 0, fill=hair_col, width=max(1,int(3*s)))
    elif emotion == "shocked":
        bry -= int(4*s)
        for ex in [hx-esep, hx+esep]:
            draw.arc([ex-brw, bry-int(8*s), ex+brw, bry], 180, 0, fill=hair_col, width=max(1,int(3*s)))
    elif emotion == "angry":
        draw.line([(hx-esep-brw,bry+int(2*s)),(hx-esep+brw,bry-int(5*s))], fill=hair_col, width=max(1,int(3*s)))
        draw.line([(hx+esep-brw,bry-int(5*s)),(hx+esep+brw,bry+int(2*s))], fill=hair_col, width=max(1,int(3*s)))
    else:
        for ex in [hx-esep, hx+esep]:
            draw.line([(ex-brw, bry),(ex+brw, bry)], fill=hair_col, width=max(1,int(3*s)))

    # Mouth
    my = hy + int(15*s)
    mw = int(13*s)
    if emotion in ("happy","love"):
        draw.arc([hx-mw,my-int(6*s),hx+mw,my+int(8*s)], 0, 180, fill=BLACK, width=max(1,int(3*s)))
    elif emotion in ("sad","stressed"):
        draw.arc([hx-mw,my,hx+mw,my+int(12*s)], 180, 0, fill=BLACK, width=max(1,int(3*s)))
    elif emotion == "shocked":
        draw.ellipse([hx-int(8*s),my-int(4*s),hx+int(8*s),my+int(10*s)], fill=BLACK)
    elif emotion == "angry":
        draw.line([(hx-mw,my+int(3*s)),(hx+mw,my-int(3*s))], fill=BLACK, width=max(1,int(3*s)))
    elif emotion == "talking":
        # Animated mouth for speech
        mo = int(6*s * abs(math.sin(cy * 0.3)))  # pseudo-random based on position
        draw.ellipse([hx-int(8*s),my-mo//2,hx+int(8*s),my+mo], fill=BLACK)
    elif emotion == "sleeping":
        draw.line([(hx-mw,my+2),(hx+mw,my+2)], fill=BLACK, width=max(1,int(2*s)))
    else:
        draw.line([(hx-mw,my),(hx+mw,my)], fill=BLACK, width=max(1,int(3*s)))

    # Stress sweat
    if emotion == "stressed":
        dx = hx + hd_r + int(3*s)
        dy = hy - int(3*s)
        draw.polygon([(dx,dy-int(8*s)),(dx-int(4*s),dy+int(3*s)),(dx+int(4*s),dy+int(3*s))], fill=CYAN)
        draw.ellipse([dx-int(4*s),dy,dx+int(4*s),dy+int(7*s)], fill=CYAN)

    if emotion == "sleeping":
        for i in range(3):
            zx = hx + hd_r + int(12*s) + i*int(12*s)
            zy = hy - hd_r - int(8*s) - i*int(16*s)
            draw.text((zx,zy), "Z", font=fnt(max(8,int((10+i*5)*s))), fill=CYAN)

    if emotion == "love":
        for i in range(3):
            lhx = hx + int((-15+i*20)*s)
            lhy = hy - hd_r - int((15+i*12)*s)
            _draw_heart(draw, lhx, lhy, int(8*s), PINK)

    return hx, hy  # head center


def _draw_heart(draw, cx, cy, sz, col):
    draw.ellipse([cx-sz, cy-sz, cx, cy], fill=col)
    draw.ellipse([cx, cy-sz, cx+sz, cy], fill=col)
    draw.polygon([(cx-sz, cy-sz//3),(cx+sz, cy-sz//3),(cx, cy+sz)], fill=col)


def draw_speech_bubble(draw, x, y, text, f, w=380, h=70, tail="down"):
    draw.rounded_rectangle([x,y,x+w,y+h], radius=16, fill=WHITE, outline=DIM, width=2)
    if tail == "down":
        tx=x+w//2
        ty=y+h
        draw.polygon([(tx-8,ty-1),(tx+8,ty-1),(tx,ty+18)], fill=WHITE, outline=DIM)
        draw.line([(tx-6,ty),(tx+6,ty)], fill=WHITE, width=3)
    elif tail == "up":
        tx=x+w//2
        ty=y
        draw.polygon([(tx-8,ty+1),(tx+8,ty+1),(tx,ty-18)], fill=WHITE, outline=DIM)
        draw.line([(tx-6,ty),(tx+6,ty)], fill=WHITE, width=3)
    # Multi-line text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        draw.text((x+14, y+10+i*24), line, font=f, fill=BLACK)


def draw_subtitle(draw, y, text, f=None, fill=WHITE, bg_alpha=160):
    """Draw subtitle bar at bottom of screen."""
    if f is None: f = fnt(26, False)
    lines = text.split("\n")
    line_h = 32
    total_h = len(lines) * line_h + 20
    # Semi-transparent background
    for dy in range(total_h):
        alpha = bg_alpha
        draw.rectangle([0, y+dy, W, y+dy+1], fill=(*BLACK[:3], alpha))
    for i, line in enumerate(lines):
        lw = tw(draw, line, f)
        draw.text(((W-lw)//2, y+10+i*line_h), line, font=f, fill=fill)


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUNDS
# ═══════════════════════════════════════════════════════════════════════════

def bg_apartment(draw, time_of_day="morning"):
    """Apartment room background."""
    if time_of_day == "morning":
        wall = (250, 245, 240)
        light = YELLOW
    elif time_of_day == "night":
        wall = (40, 40, 60)
        light = (80, 80, 120)
    else:
        wall = WALL
        light = (255, 250, 230)

    draw.rectangle([0, 0, W, int(H*0.55)], fill=wall)
    draw.rectangle([0, int(H*0.55), W, H], fill=FLOOR)
    draw.rectangle([0, int(H*0.55)-4, W, int(H*0.55)+6], fill=(190,185,180))
    # Window
    wx, wy = 650, 200
    ww, wh = 300, 350
    sky = SKY if time_of_day == "morning" else NIGHT if time_of_day == "night" else (180, 210, 240)
    draw.rounded_rectangle([wx,wy,wx+ww,wy+wh], radius=8, fill=sky, outline=(180,180,180), width=3)
    draw.line([(wx+ww//2,wy),(wx+ww//2,wy+wh)], fill=(180,180,180), width=2)
    draw.line([(wx,wy+wh//2),(wx+ww,wy+wh//2)], fill=(180,180,180), width=2)
    if time_of_day == "morning":
        draw.ellipse([wx+ww-80,wy+25,wx+ww-25,wy+80], fill=YELLOW)
    elif time_of_day == "night":
        draw.ellipse([wx+40,wy+40,wx+90,wy+90], fill=(220,220,200))


def bg_office(draw):
    draw.rectangle([0,0,W,int(H*0.53)], fill=(240,240,248))
    draw.rectangle([0,int(H*0.53),W,H], fill=(210,205,200))
    draw.rectangle([0,int(H*0.53)-3,W,int(H*0.53)+5], fill=(190,185,180))
    # Desk
    dx = 50
    dy = int(H*0.53)-70
    draw.rounded_rectangle([dx,dy,W-dx,dy+35], radius=4, fill=DESK_COL)
    draw.rectangle([dx+25,dy+35,dx+45,dy+220], fill=(150,115,75))
    draw.rectangle([W-dx-45,dy+35,W-dx-25,dy+220], fill=(150,115,75))
    # Monitor
    mx = W//2-140
    my = dy-230
    draw.rounded_rectangle([mx,my,mx+280,my+185], radius=8, fill=BLACK)
    draw.rounded_rectangle([mx+6,my+6,mx+274,my+179], radius=5, fill=SCREEN_BG)
    draw.rectangle([W//2-12,my+185,W//2+12,dy], fill=(100,100,110))
    draw.rounded_rectangle([W//2-55,dy-8,W//2+55,dy], radius=3, fill=(100,100,110))


def bg_cafe(draw):
    draw.rectangle([0,0,W,int(H*0.5)], fill=(250,240,225))
    draw.rectangle([0,int(H*0.5),W,H], fill=(190,170,150))
    # Warm wood paneling
    for y in range(0, int(H*0.5), 80):
        draw.line([(0,y),(W,y)], fill=(230,220,200), width=1)
    # Cafe table
    tw_ = 500
    tx = (W-tw_)//2
    ty = int(H*0.5)-40
    draw.rounded_rectangle([tx,ty,tx+tw_,ty+25], radius=5, fill=(160,120,80))
    draw.rectangle([tx+40,ty+25,tx+60,ty+180], fill=(130,90,60))
    draw.rectangle([tx+tw_-60,ty+25,tx+tw_-40,ty+180], fill=(130,90,60))
    # Coffee cups
    for cx_ in [tx+100, tx+tw_-100]:
        draw.rounded_rectangle([cx_-18,ty-35,cx_+18,ty], radius=4, fill=WHITE, outline=DIM, width=2)
        draw.arc([cx_+16,ty-28,cx_+30,ty-10], -90, 90, fill=DIM, width=2)


def bg_park(draw, t=0):
    for y in range(int(H*0.53)):
        p = y/(H*0.53)
        c = col_lerp((135,206,250),(200,230,255),p)
        draw.rectangle([0,y,W,y+1], fill=c)
    draw.ellipse([W-240,90,W-110,220], fill=YELLOW)
    # Clouds
    for cx_,cy_,sc in [(180,160,1.0),(550,110,0.8),(850,180,0.7)]:
        r=int(45*sc)
        for dx_,dy_ in [(-r,0),(0,-r//2),(r,0),(r//2,r//3)]:
            draw.ellipse([cx_+dx_-r,cy_+dy_-r,cx_+dx_+r,cy_+dy_+r], fill=WHITE)
    draw.rectangle([0,int(H*0.53),W,H], fill=(120,200,100))
    # Trees
    for tx_,ts in [(80,1.1),(W-120,0.9),(W//2+200,0.7)]:
        tr=int(18*ts)
        th=int(130*ts)
        tty=int(H*0.53)-th
        draw.rectangle([tx_-tr,tty,tx_+tr,int(H*0.53)+8], fill=(120,80,40))
        cr=int(70*ts)
        draw.ellipse([tx_-cr,tty-cr,tx_+cr,tty+cr//2], fill=(60,160,80))


def bg_phone_screen(draw, t=0):
    """Full-screen phone UI."""
    draw.rectangle([0,0,W,H], fill=SCREEN_BG)
    # Status bar
    draw.rectangle([0,0,W,50], fill=(15,15,30))
    draw.text((30,12), "9:41", font=fnt(18), fill=WHITE)
    # App header
    draw.rounded_rectangle([0,50,W,160], radius=0, fill=PURPLE)
    draw.text((30,75), "Todo Budget", font=fnt(36), fill=WHITE)
    draw.text((30,118), "✅ Задачи · 💰 Бюджет · ⏱ Помодоро · 📝 Заметки", font=fnt(14,False), fill=(*WHITE,180))


def bg_dark_cinematic(draw):
    draw.rectangle([0,0,W,H], fill=NIGHT)


# ═══════════════════════════════════════════════════════════════════════════
# VOICE SCRIPTS for each episode
# ═══════════════════════════════════════════════════════════════════════════

def get_episode_voices(ep):
    """
    Returns list of (text, voice, rate, pitch, filename)
    """
    M = VOICE_MALE
    F = VOICE_FEMALE
    N = VOICE_NARRATOR

    if ep == 1:
        return [
            # Narrator intro
            ("Это Лёша. Обычный парень. Обычное утро.", N, "-5%", "-2Hz", "e1_01.mp3"),
            ("Ну, почти обычное.", N, "+5%", "+0Hz", "e1_02.mp3"),
            # Lyosha
            ("О нет, уже семь! Я же проспал!", M, "+15%", "+2Hz", "e1_03.mp3"),
            ("Так, что мне сегодня нужно сделать?", M, "+5%", "+0Hz", "e1_04.mp3"),
            # Narrator
            ("Лёша пытается вспомнить все свои дела.", N, "+0%", "+0Hz", "e1_05.mp3"),
            # Lyosha
            ("Оплатить аренду! Купить продукты! Отчёт на работе! Встреча в три!", M, "+20%", "+3Hz", "e1_06.mp3"),
            # Narrator
            ("Но наш герой записывал их... нигде.", N, "+0%", "-1Hz", "e1_07.mp3"),
            # Lyosha at office
            ("Начальник, отчёт будет... скоро. Наверное.", M, "+5%", "+1Hz", "e1_08.mp3"),
            # Boss (female)
            ("Лёша, дедлайн был вчера!", F, "+10%", "+0Hz", "e1_09.mp3"),
            # Narrator
            ("Счета тоже не ждут.", N, "+0%", "+0Hz", "e1_10.mp3"),
            # Lyosha
            ("Тысяча за интернет, три за электричество, двенадцать за аренду... когда всё это платить?!", M, "+10%", "+2Hz", "e1_11.mp3"),
            # Narrator
            ("К вечеру Лёша был на пределе.", N, "-5%", "-2Hz", "e1_12.mp3"),
            # Lyosha
            ("Должен быть способ проще. Должен.", M, "-5%", "-1Hz", "e1_13.mp3"),
            # Narrator cliffhanger
            ("И он был прав. Но об этом — в следующей серии.", N, "-10%", "-3Hz", "e1_14.mp3"),
        ]
    elif ep == 2:
        return [
            # Narrator recap
            ("Помните Лёшу? Того самого, который тонул в хаосе?", N, "+0%", "+0Hz", "e2_01.mp3"),
            # Lyosha
            ("Опять просыпаю. Опять ничего не помню.", M, "+5%", "+0Hz", "e2_02.mp3"),
            # Narrator
            ("Но сегодня всё изменится.", N, "+5%", "+0Hz", "e2_03.mp3"),
            # Friend (female)
            ("Лёш, скачай Todo Budget. Серьёзно, он изменил мою жизнь.", F, "+5%", "+0Hz", "e2_04.mp3"),
            # Lyosha
            ("Очередной планировщик? Ну давай, посмотрим.", M, "+0%", "+0Hz", "e2_05.mp3"),
            # Narrator
            ("Лёша скачал приложение. Всего девять мегабайт.", N, "+0%", "+0Hz", "e2_06.mp3"),
            # Lyosha - impressed
            ("Подожди. Тут и задачи, и бюджет, и таймер Помодоро, и заметки? В одном приложении?!", M, "+15%", "+3Hz", "e2_07.mp3"),
            # Narrator
            ("Лёша начал с задач. Записал всё, что крутилось в голове.", N, "+0%", "+0Hz", "e2_08.mp3"),
            # Lyosha
            ("Аренда — высокий приоритет. Продукты — средний. Позвонить маме... высокий!", M, "+10%", "+1Hz", "e2_09.mp3"),
            # Narrator
            ("Потом — бюджет. Впервые Лёша увидел, куда уходят деньги.", N, "+0%", "+0Hz", "e2_10.mp3"),
            # Lyosha
            ("Восемь тысяч на доставку еды?! В месяц?! Что?!", M, "+20%", "+4Hz", "e2_11.mp3"),
            # Narrator
            ("А таймер Помодоро помог ему сфокусироваться на отчёте.", N, "+0%", "+0Hz", "e2_12.mp3"),
            # Lyosha
            ("Двадцать пять минут фокуса, пять минут отдыха. Это реально работает!", M, "+10%", "+2Hz", "e2_13.mp3"),
            # Narrator
            ("К вечеру список был наполовину выполнен. Впервые за долгое время.", N, "-5%", "-1Hz", "e2_14.mp3"),
            # Lyosha
            ("Кажется, я начинаю всё контролировать.", M, "+0%", "+0Hz", "e2_15.mp3"),
            # Narrator
            ("Но главная трансформация — впереди.", N, "-10%", "-3Hz", "e2_16.mp3"),
        ]
    else:  # ep 3
        return [
            # Narrator
            ("Прошёл месяц. Тот же Лёша. Но совсем другой человек.", N, "+0%", "+0Hz", "e3_01.mp3"),
            # Lyosha - morning
            ("Доброе утро! Так, что у нас на сегодня?", M, "+10%", "+1Hz", "e3_02.mp3"),
            # Narrator
            ("Утро больше не начинается с паники. Все задачи — в приложении.", N, "+0%", "+0Hz", "e3_03.mp3"),
            # Lyosha
            ("Четыре задачи, две встречи, бюджет в плюсе. Красота!", M, "+10%", "+2Hz", "e3_04.mp3"),
            # Narrator
            ("На работе тоже заметили перемены.", N, "+5%", "+0Hz", "e3_05.mp3"),
            # Boss
            ("Лёша, отличный отчёт! Как ты так организовался?", F, "+5%", "+0Hz", "e3_06.mp3"),
            # Lyosha
            ("Секретное оружие. Todo Budget.", M, "+5%", "+1Hz", "e3_07.mp3"),
            # Narrator
            ("Бюджет? Под полным контролем.", N, "+0%", "+0Hz", "e3_08.mp3"),
            # Lyosha
            ("За месяц сэкономил двенадцать тысяч! Просто потому что вижу, куда уходят деньги.", M, "+10%", "+2Hz", "e3_09.mp3"),
            # Narrator
            ("Помодоро стал ежедневной привычкой.", N, "+0%", "+0Hz", "e3_10.mp3"),
            # Lyosha
            ("Ещё один двадцатипятиминутный спринт — и проект готов.", M, "+5%", "+0Hz", "e3_11.mp3"),
            # Narrator
            ("А заметки? Ни одна идея больше не теряется.", N, "+0%", "+0Hz", "e3_12.mp3"),
            # Lyosha - in park
            ("Знаешь что самое крутое? Приложение бесплатное. Всего девять мегабайт. И работает оффлайн.", M, "+5%", "+1Hz", "e3_13.mp3"),
            # Narrator - epic
            ("Todo Budget. Четыре инструмента. Одно приложение. Ноль хаоса.", N, "-10%", "-2Hz", "e3_14.mp3"),
            # Lyosha
            ("Скачивай в RuStore. Сделай как я — возьми жизнь под контроль.", M, "+5%", "+1Hz", "e3_15.mp3"),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# EPISODE SCENE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

def build_episode_timeline(ep, durations):
    """
    Build a timeline of events for the episode.
    Each event: (start_sec, end_sec, scene_func_name, voice_file_or_None, subtitle_text)
    """
    timeline = []
    cursor = 0.0

    def add(dur, scene, voice=None, sub=""):
        nonlocal cursor
        timeline.append((cursor, cursor + dur, scene, voice, sub))
        cursor += dur

    def voice_dur(fname):
        return durations.get(fname, 2000) / 1000.0 + 0.3  # Add small pause

    if ep == 1:
        # Title card
        add(3.0, "title_ep1")
        # Scene 1: Sleeping
        add(voice_dur("e1_01.mp3")+0.5, "sleeping", "e1_01.mp3", "Это Лёша. Обычный парень.\nОбычное утро.")
        add(voice_dur("e1_02.mp3"), "alarm", "e1_02.mp3", "Ну, почти обычное.")
        # Scene 2: Wake up panic
        add(voice_dur("e1_03.mp3")+0.3, "wake_panic", "e1_03.mp3", "О нет, уже семь!\nЯ же проспал!")
        add(voice_dur("e1_04.mp3")+0.3, "thinking", "e1_04.mp3", "Так, что мне сегодня\nнужно сделать?")
        # Scene 3: Tasks flying
        add(voice_dur("e1_05.mp3"), "narrator_tasks", "e1_05.mp3", "Лёша пытается вспомнить\nвсе свои дела.")
        add(voice_dur("e1_06.mp3")+0.5, "tasks_chaos", "e1_06.mp3", "Оплатить аренду! Купить продукты!\nОтчёт! Встреча в три!")
        add(voice_dur("e1_07.mp3")+0.3, "no_planner", "e1_07.mp3", "Но наш герой записывал\nих... нигде.")
        # Scene 4: Office
        add(voice_dur("e1_08.mp3"), "office_talk", "e1_08.mp3", "Начальник, отчёт\nбудет... скоро.")
        add(voice_dur("e1_09.mp3")+0.3, "boss_angry", "e1_09.mp3", "Лёша, дедлайн\nбыл вчера!")
        # Scene 5: Bills
        add(voice_dur("e1_10.mp3"), "bills_pile", "e1_10.mp3", "Счета тоже не ждут.")
        add(voice_dur("e1_11.mp3")+0.3, "bills_stress", "e1_11.mp3", "Тысяча за интернет,\nтри за электричество...")
        # Scene 6: Evening breakdown
        add(voice_dur("e1_12.mp3")+0.5, "evening_tired", "e1_12.mp3", "К вечеру Лёша был\nна пределе.")
        add(voice_dur("e1_13.mp3")+0.5, "hope", "e1_13.mp3", "Должен быть способ\nпроще. Должен.")
        # Cliffhanger
        add(voice_dur("e1_14.mp3")+1.0, "cliffhanger", "e1_14.mp3", "И он был прав. Но об этом —\nв следующей серии.")
        # End card
        remaining = max(2.0, 60.0 - cursor)
        add(remaining, "end_card_ep1")

    elif ep == 2:
        add(3.0, "title_ep2")
        add(voice_dur("e2_01.mp3")+0.3, "recap", "e2_01.mp3", "Помните Лёшу?\nТого, что тонул в хаосе?")
        add(voice_dur("e2_02.mp3")+0.3, "morning_again", "e2_02.mp3", "Опять просыпаю.\nОпять ничего не помню.")
        add(voice_dur("e2_03.mp3"), "transition", "e2_03.mp3", "Но сегодня всё изменится.")
        # Friend in cafe
        add(voice_dur("e2_04.mp3")+0.3, "cafe_friend", "e2_04.mp3", "Лёш, скачай Todo Budget.\nОн изменил мою жизнь.")
        add(voice_dur("e2_05.mp3")+0.2, "skeptical", "e2_05.mp3", "Очередной планировщик?\nНу давай, посмотрим.")
        add(voice_dur("e2_06.mp3")+0.2, "phone_download", "e2_06.mp3", "Лёша скачал приложение.\nВсего девять мегабайт.")
        # App exploration
        add(voice_dur("e2_07.mp3")+0.5, "app_wow", "e2_07.mp3", "Тут и задачи, и бюджет,\nи таймер, и заметки?!")
        add(voice_dur("e2_08.mp3"), "adding_tasks", "e2_08.mp3", "Лёша начал с задач.\nЗаписал всё из головы.")
        add(voice_dur("e2_09.mp3")+0.3, "priorities", "e2_09.mp3", "Аренда — высокий.\nПродукты — средний...")
        add(voice_dur("e2_10.mp3"), "budget_reveal", "e2_10.mp3", "Потом — бюджет.\nВпервые увидел расходы.")
        add(voice_dur("e2_11.mp3")+0.5, "budget_shock", "e2_11.mp3", "Восемь тысяч\nна доставку?! В месяц?!")
        add(voice_dur("e2_12.mp3"), "pomodoro_start", "e2_12.mp3", "А таймер Помодоро помог\nсфокусироваться на отчёте.")
        add(voice_dur("e2_13.mp3")+0.3, "pomodoro_works", "e2_13.mp3", "25 минут фокуса,\n5 минут отдыха. Работает!")
        add(voice_dur("e2_14.mp3")+0.3, "evening_progress", "e2_14.mp3", "К вечеру список наполовину\nвыполнен. Впервые!")
        add(voice_dur("e2_15.mp3")+0.3, "feeling_good", "e2_15.mp3", "Кажется, я начинаю\nвсё контролировать.")
        add(voice_dur("e2_16.mp3")+0.5, "cliffhanger2", "e2_16.mp3", "Но главная трансформация —\nвпереди.")
        remaining = max(2.0, 60.0 - cursor)
        add(remaining, "end_card_ep2")

    else:  # ep 3
        add(3.0, "title_ep3")
        add(voice_dur("e3_01.mp3")+0.3, "month_later", "e3_01.mp3", "Прошёл месяц. Тот же Лёша.\nНо совсем другой человек.")
        add(voice_dur("e3_02.mp3")+0.2, "happy_morning", "e3_02.mp3", "Доброе утро!\nЧто у нас на сегодня?")
        add(voice_dur("e3_03.mp3"), "organized", "e3_03.mp3", "Утро больше не начинается\nс паники. Всё в приложении.")
        add(voice_dur("e3_04.mp3")+0.3, "dashboard", "e3_04.mp3", "4 задачи, 2 встречи,\nбюджет в плюсе. Красота!")
        add(voice_dur("e3_05.mp3"), "office_good", "e3_05.mp3", "На работе тоже\nзаметили перемены.")
        add(voice_dur("e3_06.mp3")+0.2, "boss_happy", "e3_06.mp3", "Лёша, отличный отчёт!\nКак ты организовался?")
        add(voice_dur("e3_07.mp3")+0.3, "secret_weapon", "e3_07.mp3", "Секретное оружие.\nTodo Budget.")
        add(voice_dur("e3_08.mp3"), "budget_control", "e3_08.mp3", "Бюджет?\nПод полным контролем.")
        add(voice_dur("e3_09.mp3")+0.3, "savings", "e3_09.mp3", "За месяц сэкономил 12 тысяч!\nПросто вижу расходы.")
        add(voice_dur("e3_10.mp3"), "pomodoro_habit", "e3_10.mp3", "Помодоро стал\nежедневной привычкой.")
        add(voice_dur("e3_11.mp3")+0.3, "sprint", "e3_11.mp3", "Ещё один 25-мин спринт —\nи проект готов.")
        add(voice_dur("e3_12.mp3"), "notes_save", "e3_12.mp3", "А заметки? Ни одна идея\nбольше не теряется.")
        add(voice_dur("e3_13.mp3")+0.3, "park_pitch", "e3_13.mp3", "Бесплатное. 9 МБ.\nРаботает оффлайн.")
        add(voice_dur("e3_14.mp3")+0.5, "epic_tagline", "e3_14.mp3", "Todo Budget. 4 инструмента.\n1 приложение. 0 хаоса.")
        add(voice_dur("e3_15.mp3")+0.5, "final_cta", "e3_15.mp3", "Скачивай в RuStore.\nВозьми жизнь под контроль.")
        remaining = max(3.0, 60.0 - cursor)
        add(remaining, "end_card_ep3")

    return timeline


# ═══════════════════════════════════════════════════════════════════════════
# SCENE RENDERERS
# ═══════════════════════════════════════════════════════════════════════════

def render_scene(scene_name, t, dur, ep):
    """
    Master scene renderer. Returns PIL Image.
    t = local time within scene, dur = scene duration
    """
    img = Image.new("RGBA", (W, H), (*WALL, 255))
    draw = ImageDraw.Draw(img)
    p = t / max(0.01, dur)  # progress 0→1

    # ── Title cards ──
    if scene_name.startswith("title_ep"):
        ep_n = int(scene_name[-1])
        draw.rectangle([0,0,W,H], fill=NIGHT)
        # Gradient glow
        cx, cy = W//2, H//2
        for r in range(400, 0, -3):
            a = 0.06 * (r/400)
            c = tuple(int(ch*a) for ch in PURPLE)
            draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=c)
        # Ep number
        pp = ease_back(min(1, t/0.5))
        text = f"Серия {ep_n}"
        draw_centered(draw, int(lerp(-80, H//2-120, pp)), text, fnt(60), WHITE)
        # Title
        titles = {1: "Хаос", 2: "Открытие", 3: "Мастер"}
        if t > 0.8:
            tp = ease_elastic((t-0.8)/0.5)
            draw_centered(draw, H//2-20, titles[ep_n], fnt(int(90*tp)), WHITE)
        # Subtitle
        if t > 1.8:
            sp = ease_out((t-1.8)/0.5)
            draw_centered(draw, H//2+100, "Todo Budget", fnt(32, False), col_lerp(NIGHT, PURPLE, sp))
        return img

    # ── End cards ──
    if scene_name.startswith("end_card"):
        draw.rectangle([0,0,W,H], fill=NIGHT)
        cx = W//2
        for r in range(350, 0, -3):
            a = 0.05*(r/350)
            c = tuple(int(ch*a) for ch in PURPLE)
            draw.ellipse([cx-r,H//2-r,cx+r,H//2+r], fill=c)
        ep_n = int(scene_name[-1])
        if ep_n < 3:
            draw_centered(draw, H//2-80, "Продолжение следует...", fnt(44), WHITE)
            pulse = 0.5+0.5*math.sin(t*3)
            draw_centered(draw, H//2+20, f"Серия {ep_n+1} — скоро", fnt(30, False), col_lerp(NIGHT, DIM, pulse))
        else:
            # Final CTA
            pp = ease_back(min(1, t/0.4))
            sz = int(120*pp)
            r = sz//2
            if sz > 5:
                draw.rounded_rectangle([cx-r,400-r,cx+r,400+r], radius=max(3,int(sz*0.28)), fill=PURPLE)
                draw.text((cx-tw(draw,"✓",fnt(int(sz*0.5)))//2, 400-int(sz*0.25)), "✓", font=fnt(int(sz*0.5)), fill=WHITE)
            if t > 0.5:
                draw_centered(draw, 520, "Todo Budget", fnt(64), WHITE)
            if t > 1.0:
                sp = ease_out((t-1.0)/0.3)
                draw_centered(draw, 620, "Задачи · Бюджет · Помодоро · Заметки", fnt(24, False), col_lerp(NIGHT, DIM, sp))
            if t > 1.5:
                stats = [("0 ₽","Навсегда",GREEN),("9 МБ","Размер",CYAN),("4 в 1","Функции",PURPLE)]
                for i,(v,l,c) in enumerate(stats):
                    st = t-1.5-i*0.2
                    if st <= 0: continue
                    spp = ease_elastic(st/0.3)
                    bx = 80+i*330
                    by = 750
                    draw.rounded_rectangle([bx,by,bx+280,by+100], radius=16, fill=(30,30,55))
                    draw.text((bx+140-tw(draw,v,fnt(int(38*spp)))//2, by+8), v, font=fnt(int(38*spp)), fill=c)
                    draw.text((bx+140-tw(draw,l,fnt(16,False))//2, by+60), l, font=fnt(16,False), fill=DIM)
            if t > 2.5:
                bp = ease_back((t-2.5)/0.3)
                by = int(lerp(1050, 950, bp))
                bw, bh = 500, 80
                draw.rounded_rectangle([cx-bw//2,by,cx+bw//2,by+bh], radius=bh//2, fill=PURPLE)
                draw_centered(draw, by+18, "Скачать в RuStore", fnt(30), WHITE)
            if t > 3.0:
                ap = ease_out((t-3.0)/0.3)
                draw_centered(draw, 1080, "apps.rustore.ru/app/ru.todobudget.todo", fnt(18,False), col_lerp(NIGHT,CYAN,ap))
        return img

    # ── Episode 1 scenes ──
    if scene_name == "sleeping":
        bg_apartment(draw, "night")
        # Bed
        bx, by = 150, int(H*0.55)-180
        draw.rounded_rectangle([bx,by,bx+500,by+180], radius=12, fill=(180,200,230))
        draw.rounded_rectangle([bx+15,by+15,bx+140,by+70], radius=18, fill=(230,235,250))
        draw.rounded_rectangle([bx+5,by+90,bx+495,by+170], radius=8, fill=(160,185,215))
        # Character in bed
        draw_char(draw, 350, int(H*0.55)-20, scale=0.7, emotion="sleeping", tilt=-70, hair_col=HAIR_BROWN)
        return img

    if scene_name == "alarm":
        bg_apartment(draw, "morning")
        bx, by = 150, int(H*0.55)-180
        draw.rounded_rectangle([bx,by,bx+500,by+180], radius=12, fill=(180,200,230))
        draw.rounded_rectangle([bx+5,by+90,bx+495,by+170], radius=8, fill=(160,185,215))
        shake = int(6*math.sin(t*25))
        draw_char(draw, 350+shake, int(H*0.55)-20, scale=0.7, emotion="shocked", tilt=-40+20*ease_out(p), hair_col=HAIR_BROWN)
        # Alarm
        ax, ay = 730, int(H*0.55)-230
        draw.ellipse([ax,ay,ax+70,ay+70], fill=WHITE, outline=RED, width=3)
        draw.text((ax+12,ay+18), "7:00", font=fnt(16), fill=RED)
        # ДЗЫНЬ
        draw.text((ax-30+shake*2, ay-30), "ДЗЫНЬ!", font=fnt(28), fill=RED)
        return img

    if scene_name == "wake_panic":
        bg_apartment(draw, "morning")
        pp = ease_out(p)
        cx = int(lerp(350, W//2, pp))
        tilt = int(lerp(-40, 0, pp))
        draw_char(draw, cx, int(H*0.55)+180, scale=1.0, emotion="stressed", tilt=tilt,
                  arm_angle=int(20*math.sin(t*4)), hair_col=HAIR_BROWN)
        return img

    if scene_name == "thinking":
        bg_apartment(draw, "morning")
        blink = t % 2.0 < 0.15
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="stressed",
                  look=math.sin(t*1.5), arm_angle=5, blink=blink, hair_col=HAIR_BROWN)
        # Thought bubble
        if t > 0.3:
            bp = ease_out((t-0.3)/0.4)
            draw_speech_bubble(draw, int(lerp(W,350,bp)), 500, "Что я должен\nсделать сегодня?!", fnt(20, False), w=300, h=65, tail="down")
        return img

    if scene_name in ("narrator_tasks", "tasks_chaos"):
        bg_apartment(draw, "morning")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="stressed",
                  arm_angle=int(10*math.sin(t*3)), hair_col=HAIR_BROWN)
        # Flying task cards
        tasks = [("₽12 000\nАренда",YELLOW),("Купить еду",(255,200,200)),("ОТЧЁТ!!!",(255,180,180)),
                 ("₽3 500 счёт",(200,255,200)),("Встреча 15:00",PINK),("₽850 интернет",(220,200,255)),
                 ("ДЕДЛАЙН!",RED),("Позвонить маме",(200,230,255))]
        for i,(txt,col) in enumerate(tasks):
            bt = t - i*0.25
            if bt <= 0: continue
            rng = random.Random(100+i)
            start_x = rng.randint(-200, W+200)
            end_x = rng.randint(50, W-180)
            end_y = rng.randint(200, int(H*0.45))
            pp2 = ease_out(min(1, bt/0.4))
            x = int(lerp(start_x, end_x, pp2))
            y = int(lerp(-80, end_y, pp2))
            ang = bt*2 + rng.random()*3
            ox = int(8*math.sin(ang))
            oy = int(4*math.cos(ang))
            draw.rounded_rectangle([x+ox,y+oy,x+130+ox,y+65+oy], radius=8, fill=col, outline=(*BLACK[:3],40), width=1)
            draw.text((x+8+ox, y+10+oy), txt, font=fnt(14), fill=BLACK)
        return img

    if scene_name == "no_planner":
        bg_apartment(draw, "morning")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="sad",
                  arm_angle=5, hair_col=HAIR_BROWN)
        # Crossed out notebook
        nx, ny = 650, 550
        draw.rounded_rectangle([nx,ny,nx+180,ny+120], radius=6, fill=WHITE, outline=DIM, width=2)
        draw.text((nx+20,ny+15), "Планы:", font=fnt(18, False), fill=DIM)
        draw.text((nx+20,ny+45), "???", font=fnt(28), fill=DIM)
        draw.line([(nx-10,ny-10),(nx+190,ny+130)], fill=RED, width=4)
        draw.line([(nx+190,ny-10),(nx-10,ny+130)], fill=RED, width=4)
        return img

    if scene_name in ("office_talk", "boss_angry"):
        bg_office(draw)
        if scene_name == "office_talk":
            draw_char(draw, W//2-150, int(H*0.53)+200, scale=0.95, emotion="stressed",
                      arm_angle=10, hair_col=HAIR_BROWN, look=1)
            draw_char(draw, W//2+200, int(H*0.53)+180, scale=0.85, emotion="angry",
                      hair_col=HAIR_BLONDE, shirt_col=SHIRT_RED, look=-1)
        else:
            draw_char(draw, W//2-150, int(H*0.53)+200, scale=0.95, emotion="sad",
                      hair_col=HAIR_BROWN, look=1)
            draw_char(draw, W//2+200, int(H*0.53)+180, scale=0.85, emotion="angry",
                      arm_angle=30, hair_col=HAIR_BLONDE, shirt_col=SHIRT_RED, look=-1)
            draw_speech_bubble(draw, W//2, 500, "Дедлайн был\nВЧЕРА!", fnt(22), w=260, h=65, tail="down")
        return img

    if scene_name in ("bills_pile", "bills_stress"):
        bg_apartment(draw, "day")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0,
                  emotion="stressed" if scene_name=="bills_stress" else "sad",
                  arm_angle=int(5*math.sin(t*2)), hair_col=HAIR_BROWN)
        # Bills
        bills = [("₽12 000",YELLOW,100,350),("₽3 500",(200,255,200),300,280),
                 ("₽850",(220,200,255),550,320),("₽1 500",PINK,700,360),
                 ("₽4 200",(255,200,200),450,400)]
        for txt,col,bx,by in bills:
            wobble = int(3*math.sin(t*2+bx*0.01))
            draw.rounded_rectangle([bx,by+wobble,bx+130,by+70+wobble], radius=6, fill=col)
            draw.text((bx+10,by+15+wobble), txt, font=fnt(20), fill=BLACK)
            draw.text((bx+10,by+42+wobble), "СЧЁТ", font=fnt(12,False), fill=DIM)
        return img

    if scene_name == "evening_tired":
        bg_apartment(draw, "night")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="sad",
                  tilt=10, arm_angle=40, hair_col=HAIR_BROWN)
        # Dark vignette
        vp = min(0.25, p*0.25)
        overlay = Image.new("RGBA", (W,H), (0,0,0,int(vp*255)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        return img

    if scene_name == "hope":
        bg_apartment(draw, "night")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="sad",
                  look=0, hair_col=HAIR_BROWN)
        # Small phone glow
        if t > 0.5:
            gp = ease_out((t-0.5)/0.5)
            gx, gy = W//2+250, int(H*0.55)+50
            for r in range(int(80*gp), 0, -2):
                a = int(15 * (r/(80*gp+0.01)))
                draw.ellipse([gx-r,gy-r,gx+r,gy+r], fill=(*PURPLE[:3],a))
        return img

    if scene_name == "cliffhanger":
        # Dark fade
        bg_apartment(draw, "night")
        fade_p = ease_in(p)
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="neutral",
                  look=1, hair_col=HAIR_BROWN)
        overlay = Image.new("RGBA", (W,H), (0,0,0,int(fade_p*200)))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        if p > 0.3:
            draw_centered(draw, H//2-30, "Продолжение следует...", fnt(42), WHITE)
        return img

    # ── Episode 2 scenes ──
    if scene_name == "recap":
        bg_apartment(draw, "night")
        draw_char(draw, W//2, int(H*0.55)+180, scale=0.9, emotion="stressed", hair_col=HAIR_BROWN)
        # Flashback vignette
        overlay = Image.new("RGBA", (W,H), (0,0,0,60))
        img = Image.alpha_composite(img, overlay)
        return img

    if scene_name == "morning_again":
        bg_apartment(draw, "morning")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="sad",
                  tilt=5, hair_col=HAIR_BROWN, blink=t%1.5<0.12)
        return img

    if scene_name == "transition":
        # Text on dark
        draw.rectangle([0,0,W,H], fill=NIGHT)
        pp = ease_out(min(1, t/0.4))
        draw_centered(draw, int(lerp(H//2+50,H//2-20,pp)), "Но сегодня", fnt(50), WHITE)
        if t > 0.5:
            draw_centered(draw, H//2+60, "всё изменится.", fnt(50), GREEN)
        return img

    if scene_name in ("cafe_friend", "skeptical"):
        bg_cafe(draw)
        # Lyosha
        draw_char(draw, W//2-160, int(H*0.5)+180, scale=0.9,
                  emotion="neutral" if scene_name=="skeptical" else "sad",
                  look=1, hair_col=HAIR_BROWN)
        # Friend Katya
        draw_char(draw, W//2+180, int(H*0.5)+170, scale=0.85,
                  emotion="happy", look=-1, hair_col=HAIR_BLONDE,
                  shirt_col=SHIRT_GREEN, holding="phone")
        if scene_name == "cafe_friend":
            draw_speech_bubble(draw, W//2+20, 560, "Скачай Todo Budget!\nСерьёзно!", fnt(18, False), w=280, h=55, tail="down")
        return img

    if scene_name == "phone_download":
        draw.rectangle([0,0,W,H], fill=SCREEN_BG)
        # Phone downloading animation
        cx = W//2
        cy = H//2
        # Phone frame
        pw, ph = 400, 700
        draw.rounded_rectangle([cx-pw//2,cy-ph//2,cx+pw//2,cy+ph//2], radius=30, fill=(30,30,40), outline=(80,80,100), width=3)
        # Screen
        draw.rounded_rectangle([cx-pw//2+10,cy-ph//2+40,cx+pw//2-10,cy+ph//2-40], radius=15, fill=SCREEN_BG)
        # Download progress
        prog = min(1, p*1.5)
        bar_w = pw - 60
        bar_y = cy + 50
        draw.rounded_rectangle([cx-bar_w//2, bar_y, cx+bar_w//2, bar_y+20], radius=10, fill=(50,50,70))
        draw.rounded_rectangle([cx-bar_w//2, bar_y, cx-bar_w//2+int(bar_w*prog), bar_y+20], radius=10, fill=GREEN)
        draw.text((cx-60, bar_y-40), f"{int(prog*9)} МБ / 9 МБ", font=fnt(18,False), fill=DIM)
        # App icon
        ir = 50
        draw.rounded_rectangle([cx-ir,cy-ph//2+100,cx+ir,cy-ph//2+200], radius=15, fill=PURPLE)
        draw.text((cx-20, cy-ph//2+125), "✓", font=fnt(40), fill=WHITE)
        draw.text((cx-65, cy-ph//2+220), "Todo Budget", font=fnt(24), fill=WHITE)
        if prog >= 1.0:
            draw.text((cx-45, bar_y+40), "Установлено!", font=fnt(22), fill=GREEN)
        return img

    if scene_name == "app_wow":
        bg_apartment(draw, "day")
        draw_char(draw, W//2-200, int(H*0.55)+180, scale=1.0, emotion="shocked",
                  look=1, holding="phone", hair_col=HAIR_BROWN, arm_angle=15)
        # Feature cards appearing
        features = [("✅ Задачи", GREEN, 0.3), ("💰 Бюджет", ORANGE, 0.6),
                    ("⏱ Помодоро", RED, 0.9), ("📝 Заметки", CYAN, 1.2)]
        for txt, col, delay in features:
            ft = t - delay
            if ft <= 0: continue
            fp = ease_back(ft/0.3)
            fy = 300 + features.index((txt,col,delay)) * 90
            fx = int(lerp(W+50, 500, fp))
            draw.rounded_rectangle([fx, fy, fx+350, fy+70], radius=18, fill=WHITE, outline=col, width=3)
            draw.text((fx+15, fy+18), txt, font=fnt(26), fill=col)
        return img

    if scene_name in ("adding_tasks", "priorities"):
        bg_phone_screen(draw)
        # Task list
        tasks_data = [
            ("Оплатить аренду", RED, True if scene_name=="priorities" else False),
            ("Купить продукты", ORANGE, True if scene_name=="priorities" else False),
            ("Позвонить маме", GREEN, True if scene_name=="priorities" else False),
            ("Сдать отчёт", RED, False),
        ]
        for i, (task, col, has_prio) in enumerate(tasks_data):
            bt = t - i*0.3
            if bt <= 0: continue
            ap = ease_out(min(1, bt/0.3))
            y = 200 + i * 100
            x_off = int(lerp(W, 0, ap))
            draw.rounded_rectangle([30+x_off, y, W-30+x_off, y+80], radius=14, fill=(35,35,55))
            draw.rounded_rectangle([50+x_off, y+25, 75+x_off, y+50], radius=5, outline=col, width=2)
            draw.text((90+x_off, y+20), task, font=fnt(22), fill=WHITE)
            if has_prio:
                draw.ellipse([W-80+x_off, y+27, W-55+x_off, y+52], fill=col)
        return img

    if scene_name in ("budget_reveal", "budget_shock"):
        bg_phone_screen(draw)
        draw.text((30,180), "Расходы за месяц", font=fnt(28), fill=WHITE)
        cats = [("Доставка еды","₽8 200",430,RED),("Аренда","₽12 000",900,ORANGE),
                ("Транспорт","₽5 100",380,YELLOW),("Развлечения","₽6 500",480,CYAN)]
        for i,(cat,amt,max_w,col) in enumerate(cats):
            y = 280 + i * 90
            draw.text((30, y), cat, font=fnt(18,False), fill=DIM)
            bp = ease_out(min(1, (t-i*0.2)/0.5))
            w = int(max_w * bp * (W-60) / 1000)
            draw.rounded_rectangle([30, y+28, 30+w, y+52], radius=10, fill=col)
            if bp > 0.5:
                draw.text((40+w, y+28), amt, font=fnt(16,False), fill=col)
        # Shock highlight on food delivery
        if scene_name == "budget_shock" and t > 0.5:
            draw.rounded_rectangle([20, 270, W-20, 360], radius=12, outline=RED, width=3)
            draw.text((W-200, 270), "😱", font=fnt(40), fill=WHITE)
        return img

    if scene_name in ("pomodoro_start", "pomodoro_works"):
        bg_phone_screen(draw)
        cx, cy = W//2, 550
        r = 160
        draw.ellipse([cx-r,cy-r,cx+r,cy+r], outline=(50,50,70), width=4)
        progress = min(1, p * 0.6)
        draw.arc([cx-r,cy-r,cx+r,cy+r], -90, -90+360*progress, fill=RED, width=8)
        m = int(25*(1-progress))
        draw.text((cx-70, cy-30), f"{m:02d}:00", font=fnt(60), fill=WHITE)
        draw.text((cx-35, cy+40), "Фокус", font=fnt(22,False), fill=DIM)
        # Focus bar
        if scene_name == "pomodoro_works":
            draw.text((30, 800), "Фокус сессий сегодня: 3", font=fnt(20,False), fill=GREEN)
            for i in range(3):
                draw.rounded_rectangle([30+i*120, 840, 130+i*120, 870], radius=8, fill=GREEN)
        return img

    if scene_name in ("evening_progress", "feeling_good"):
        bg_apartment(draw, "night")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0,
                  emotion="happy", hair_col=HAIR_BROWN, holding="phone")
        # Progress indicator
        if scene_name == "evening_progress":
            tasks_done = min(4, int(p * 5))
            for i in range(6):
                tx = 100 + (i % 3) * 300
                ty = 300 + (i // 3) * 80
                done = i < tasks_done
                draw.rounded_rectangle([tx, ty, tx+250, ty+55], radius=10,
                                       fill=(*GREEN[:3],60) if done else (40,40,60,60))
                if done:
                    draw.text((tx+10, ty+12), "✓", font=fnt(22), fill=GREEN)
        return img

    if scene_name == "cliffhanger2":
        draw.rectangle([0,0,W,H], fill=NIGHT)
        fade_p = ease_in(p) * 0.8
        pp = ease_out(min(1, t/0.5))
        draw_centered(draw, int(lerp(H//2+50,H//2-20,pp)), "Но главная трансформация", fnt(38), WHITE)
        if t > 0.8:
            draw_centered(draw, H//2+60, "впереди.", fnt(50), PURPLE)
        return img

    # ── Episode 3 scenes ──
    if scene_name == "month_later":
        draw.rectangle([0,0,W,H], fill=NIGHT)
        pp = ease_out(min(1, t/0.5))
        draw_centered(draw, H//2-60, "1 месяц спустя", fnt(52), WHITE)
        if t > 0.8:
            sp = ease_out((t-0.8)/0.4)
            draw_centered(draw, H//2+30, "Тот же Лёша", fnt(36,False), col_lerp(NIGHT,DIM,sp))
        if t > 1.5:
            draw_centered(draw, H//2+100, "Совсем другой человек.", fnt(36,False), GREEN)
        return img

    if scene_name in ("happy_morning", "organized"):
        bg_apartment(draw, "morning")
        draw_char(draw, W//2, int(H*0.55)+180, scale=1.0, emotion="happy",
                  hair_col=HAIR_BROWN, holding="phone",
                  arm_angle=int(5*math.sin(t*1.5)))
        if scene_name == "organized":
            draw_speech_bubble(draw, 100, 450, "Все задачи в\nприложении ✅", fnt(20,False), w=280, h=60, tail="down")
        return img

    if scene_name == "dashboard":
        bg_phone_screen(draw)
        # Dashboard view
        draw.text((30,180), "Сегодня", font=fnt(34), fill=WHITE)
        # Tasks
        items = [("✅ Оплатить аренду",GREEN),("⬜ Созвон с командой",DIM),
                 ("⬜ Тренировка",DIM),("✅ Отправить отчёт",GREEN)]
        for i,(txt,col) in enumerate(items):
            y = 260+i*60
            draw.text((30,y), txt, font=fnt(20), fill=col)
        # Balance
        draw.rounded_rectangle([30,530,W-30,650], radius=16, fill=(20,50,35))
        draw.text((60,555), "₽54 200", font=fnt(50), fill=GREEN)
        draw.text((60,615), "↑ +12% к прошлому месяцу", font=fnt(16,False), fill=GREEN)
        # Meetings
        draw.text((30,680), "Встречи", font=fnt(22), fill=DIM)
        draw.rounded_rectangle([30,720,500,780], radius=10, fill=(35,35,55))
        draw.text((50,735), "10:00 — Созвон", font=fnt(18), fill=WHITE)
        draw.rounded_rectangle([30,790,500,850], radius=10, fill=(35,35,55))
        draw.text((50,805), "15:00 — Презентация", font=fnt(18), fill=WHITE)
        return img

    if scene_name in ("office_good", "boss_happy", "secret_weapon"):
        bg_office(draw)
        le = "happy" if scene_name != "secret_weapon" else "happy"
        draw_char(draw, W//2-150, int(H*0.53)+200, scale=0.95, emotion=le,
                  hair_col=HAIR_BROWN, look=1)
        be = "happy" if scene_name=="boss_happy" else "neutral"
        draw_char(draw, W//2+200, int(H*0.53)+180, scale=0.85, emotion=be,
                  hair_col=HAIR_BLONDE, shirt_col=SHIRT_RED, look=-1)
        if scene_name == "boss_happy":
            draw_speech_bubble(draw, W//2+50, 530, "Отличный отчёт!", fnt(20,False), w=250, h=45, tail="down")
        elif scene_name == "secret_weapon":
            draw_speech_bubble(draw, W//2-250, 530, "Todo Budget 😎", fnt(22), w=230, h=45, tail="down")
        return img

    if scene_name in ("budget_control", "savings"):
        bg_phone_screen(draw)
        draw.text((30,180), "Финансы", font=fnt(34), fill=WHITE)
        draw.rounded_rectangle([30,250,W-30,400], radius=16, fill=(20,50,35))
        draw.text((60,275), "₽54 200", font=fnt(55), fill=GREEN)
        draw.text((60,345), "Сэкономлено: ₽12 000", font=fnt(20,False), fill=GREEN)
        # Trend chart
        if scene_name == "savings":
            chart_y = 450
            draw.text((30,chart_y), "Динамика расходов", font=fnt(20,False), fill=DIM)
            points = [(30+i*100, chart_y+150-int(h)) for i, h in enumerate([120,105,95,80,65,55,45,40,35,30])]
            for i in range(len(points)-1):
                draw.line([points[i], points[i+1]], fill=GREEN, width=3)
            for px,py in points:
                draw.ellipse([px-4,py-4,px+4,py+4], fill=GREEN)
        return img

    if scene_name in ("pomodoro_habit", "sprint"):
        bg_phone_screen(draw)
        cx, cy = W//2, 450
        r = 140
        draw.ellipse([cx-r,cy-r,cx+r,cy+r], outline=(50,50,70), width=4)
        prog = min(1, p*0.85)
        draw.arc([cx-r,cy-r,cx+r,cy+r], -90, -90+360*prog, fill=RED, width=8)
        m = int(25*(1-prog))
        draw.text((cx-60, cy-25), f"{m:02d}:00", font=fnt(55), fill=WHITE)
        # Session counter
        draw.text((30, 700), "Сессий сегодня: 7", font=fnt(22,False), fill=DIM)
        for i in range(7):
            x = 30+i*70
            done = i < 7
            draw.rounded_rectangle([x,740,x+55,770], radius=8, fill=GREEN if done else (50,50,70))
        return img

    if scene_name == "notes_save":
        bg_phone_screen(draw)
        draw.text((30,180), "📝 Заметки", font=fnt(34), fill=WHITE)
        notes = [("Идея: Новый проект","Обсудить с командой в пн",CYAN),
                 ("Рецепт пасты","Ингредиенты и шаги",ORANGE),
                 ("Книга: Атомные привычки","Глава 3 — ключевые мысли",PURPLE)]
        for i,(title,desc,col) in enumerate(notes):
            y = 260+i*120
            draw.rounded_rectangle([30,y,W-30,y+100], radius=14, fill=(35,35,55))
            draw.rounded_rectangle([30,y,38,y+100], radius=4, fill=col)
            draw.text((55,y+15), title, font=fnt(20), fill=WHITE)
            draw.text((55,y+48), desc, font=fnt(16,False), fill=DIM)
            draw.text((55,y+72), "Сегодня, 14:32", font=fnt(12,False), fill=(*col,180))
        return img

    if scene_name == "park_pitch":
        bg_park(draw, t)
        draw_char(draw, W//2, int(H*0.53)+200, scale=1.1, emotion="happy",
                  hair_col=HAIR_BROWN, holding="phone",
                  arm_angle=int(15+10*math.sin(t*1.5)),
                  jump=int(max(0,15*math.sin(t*1.5))))
        # Feature pills
        features = [("0 ₽",GREEN,150,int(H*0.53)-100),("9 МБ",CYAN,400,int(H*0.53)-130),
                    ("Оффлайн",PURPLE,650,int(H*0.53)-90)]
        for txt,col,fx,fy in features:
            bob = int(5*math.sin(t*2+fx*0.01))
            draw.rounded_rectangle([fx,fy+bob,fx+180,fy+50+bob], radius=25, fill=WHITE, outline=col, width=2)
            draw.text((fx+15,fy+10+bob), txt, font=fnt(22), fill=col)
        return img

    if scene_name == "epic_tagline":
        draw.rectangle([0,0,W,H], fill=NIGHT)
        cx = W//2
        for r in range(500,0,-3):
            a=0.06*(r/500)
            c=tuple(int(ch*a) for ch in PURPLE)
            draw.ellipse([cx-r,H//2-r,cx+r,H//2+r], fill=c)
        words = ["Todo Budget.", "4 инструмента.", "1 приложение.", "0 хаоса."]
        for i, word in enumerate(words):
            wt = t - i * 0.5
            if wt <= 0: continue
            wp = ease_out(min(1, wt/0.3))
            y = H//2 - 120 + i * 70
            draw_centered(draw, y, word, fnt(42), col_lerp(NIGHT, WHITE if i==0 else GREEN if i<3 else PURPLE, wp))
        return img

    if scene_name == "final_cta":
        draw.rectangle([0,0,W,H], fill=NIGHT)
        cx = W//2
        # Logo
        ir = 60
        draw.rounded_rectangle([cx-ir,350,cx+ir,350+ir*2], radius=15, fill=PURPLE)
        draw.text((cx-25,380), "✓", font=fnt(50), fill=WHITE)
        draw_centered(draw, 500, "Todo Budget", fnt(52), WHITE)
        draw_centered(draw, 580, "Задачи · Бюджет · Помодоро · Заметки", fnt(22,False), DIM)
        # CTA
        bw, bh = 500, 80
        draw.rounded_rectangle([cx-bw//2,700,cx+bw//2,700+bh], radius=bh//2, fill=PURPLE)
        draw_centered(draw, 718, "Скачать в RuStore", fnt(30), WHITE)
        draw_centered(draw, 830, "apps.rustore.ru/app/ru.todobudget.todo", fnt(18,False), CYAN)
        # Lyosha waving
        draw_char(draw, cx, 1300, scale=0.7, emotion="happy",
                  arm_angle=int(30+20*math.sin(t*3)), hair_col=HAIR_BROWN)
        pulse = 0.5+0.5*math.sin(t*3)
        draw_centered(draw, 1450, "Ссылка в описании ↓", fnt(22,False), col_lerp(NIGHT,DIM,pulse))
        return img

    # Fallback
    draw.rectangle([0,0,W,H], fill=WALL)
    draw_centered(draw, H//2, scene_name, fnt(30), BLACK)
    return img


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO MIXING
# ═══════════════════════════════════════════════════════════════════════════

def generate_episode_music(ep, duration_ms):
    """Generate background music track for episode."""
    from pydub import AudioSegment
    sr = 44100

    def synth(freq, dur_ms, vol=0.3, att=0.02, dec=0.1):
        n = int(sr*dur_ms/1000)
        t = np.linspace(0, dur_ms/1000, n)
        env = np.minimum(t/att,1.0)*np.exp(-np.maximum(t-(dur_ms/1000-dec),0)/dec*5)
        return AudioSegment((env*np.sin(2*np.pi*freq*t)*vol*32767).astype(np.int16).tobytes(),
                            frame_rate=sr, sample_width=2, channels=1)

    def kick(dur_ms=100):
        n=int(sr*dur_ms/1000); t=np.linspace(0,dur_ms/1000,n)
        env=np.exp(-t*25); freq=50*(1+5*np.exp(-t*30))
        sig=np.tanh(env*np.sin(2*np.pi*np.cumsum(freq)/sr)*3)*0.5
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def snare(dur_ms=60):
        n=int(sr*dur_ms/1000); t=np.linspace(0,dur_ms/1000,n)
        sig=np.exp(-t*25)*(np.random.uniform(-1,1,n)*0.5+np.sin(2*np.pi*180*t)*0.3)*0.4
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def hh(dur_ms=25):
        n=int(sr*dur_ms/1000)
        sig=np.random.uniform(-1,1,n)*np.exp(-np.linspace(0,12,n))*0.12
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def pad(dur_ms, freq, vol=0.06):
        n=int(sr*dur_ms/1000); t=np.linspace(0,dur_ms/1000,n)
        env=(1-np.exp(-t*1.5))*np.exp(-t*0.08)
        s=(np.sin(2*np.pi*freq*t)+np.sin(2*np.pi*freq*1.003*t))/2
        return AudioSegment((env*s*vol*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def bell(freq, dur_ms=600, vol=0.1):
        n=int(sr*dur_ms/1000); t=np.linspace(0,dur_ms/1000,n)
        env=np.exp(-t*4)
        sig=env*(np.sin(2*np.pi*freq*t)+0.5*np.sin(2*np.pi*freq*2*t))/1.5*vol
        return AudioSegment((sig*32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    track = AudioSegment.silent(duration=duration_ms+2000)
    k = kick(); sn = snare(); h = hh()
    beat = BEAT_MS

    if ep == 1:
        # Ep1: starts calm, gets tense
        track = track.overlay(pad(duration_ms, 165, 0.04), position=0)
        # Calm start (first 15s)
        for b in range(30):
            pos = b*beat
            if pos > 15000: break
            track = track.overlay(h-6, position=pos+beat//2)
            if b%4 == 0: track = track.overlay(bell(440, 500, 0.06), position=pos)
        # Building tension (15-45s)
        for b in range(30, 90):
            pos = b*beat
            if pos > 45000: break
            prog = (b-30)/60
            vol_adj = int(-6+prog*6)
            track = track.overlay(k+vol_adj, position=pos)
            if b%2==1: track = track.overlay(sn+vol_adj, position=pos)
            track = track.overlay(h, position=pos+beat//2)
        # Intense (45-55s)
        for b in range(90, 110):
            pos = b*beat
            if pos > 55000: break
            track = track.overlay(k, position=pos)
            if b%2==1: track = track.overlay(sn, position=pos)
            track = track.overlay(h, position=pos)
            track = track.overlay(h-4, position=pos+beat//2)
        # Tension pad
        track = track.overlay(pad(30000, 110, 0.05), position=15000)

    elif ep == 2:
        # Ep2: uncertain start, builds to hopeful
        track = track.overlay(pad(20000, 165, 0.04), position=0)
        # Soft first 15s
        for b in range(30):
            pos = b*beat
            if pos > 15000: break
            if b%4==0: track = track.overlay(k-6, position=pos)
            track = track.overlay(h-6, position=pos+beat//2)
        # Discovery moment (~18s) — bells
        for i, note in enumerate([330,392,440,523,587,659]):
            track = track.overlay(bell(note, 700, 0.1), position=18000+i*500)
        # Upbeat second half
        for b in range(40, 120):
            pos = b*beat
            if pos > 60000: break
            track = track.overlay(k, position=pos)
            if b%4 in [1,3]: track = track.overlay(sn, position=pos)
            track = track.overlay(h, position=pos+beat//2)
        track = track.overlay(pad(40000, 220, 0.06), position=20000)
        track = track.overlay(pad(40000, 277, 0.04), position=20200)

    else:
        # Ep3: confident, upbeat, triumphant
        track = track.overlay(pad(duration_ms, 220, 0.06), position=0)
        track = track.overlay(pad(duration_ms, 277, 0.04), position=200)
        track = track.overlay(pad(duration_ms, 330, 0.03), position=400)
        for b in range(duration_ms//beat+1):
            pos = b*beat
            if pos > duration_ms: break
            track = track.overlay(k, position=pos)
            if b%4 in [1,3]: track = track.overlay(sn, position=pos)
            track = track.overlay(h, position=pos+beat//2)
            if b%2==1: track = track.overlay(h-6, position=pos+beat//4)
        # Melody
        melody = [440,523,587,659,587,523,440,392,440,523,587,659,784,659,587,523]
        for i, note in enumerate(melody):
            pos = i*beat+3000
            if pos < duration_ms:
                track = track.overlay(bell(note, 400, 0.08), position=pos)
        # Repeat melody at 30s
        for i, note in enumerate(melody):
            pos = i*beat+30000
            if pos < duration_ms:
                track = track.overlay(bell(note, 400, 0.08), position=pos)

    track = track[:duration_ms+1000].fade_in(500).fade_out(2000)
    return track.normalize()


def mix_episode_audio(ep, timeline, voice_dir, duration_ms):
    """Mix voices + music into final audio."""
    from pydub import AudioSegment

    print(f"    Generating background music...")
    music = generate_episode_music(ep, duration_ms)

    # Lower music volume for voice clarity
    music = music - 12  # -12dB under voice

    print(f"    Mixing voice lines...")
    mixed = music

    for start_sec, end_sec, scene, voice_file, sub in timeline:
        if voice_file is None:
            continue
        vpath = voice_dir / voice_file
        if not vpath.exists():
            continue
        voice = AudioSegment.from_mp3(str(vpath))
        pos = int(start_sec * 1000) + 200  # small delay after scene start
        mixed = mixed.overlay(voice, position=pos)

    mixed = mixed[:duration_ms].normalize()
    return mixed


# ═══════════════════════════════════════════════════════════════════════════
# MAIN RENDER PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def render_episode(ep, timeline, duration_sec):
    """Render all frames for an episode."""
    total_frames = int(duration_sec * FPS)
    frames_dir = SERIES_DIR / f"ep{ep}_frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()

    print(f"    Rendering {total_frames} frames ({duration_sec:.1f}s)...")

    prev_img = None
    for fi in range(total_frames):
        global_t = fi / FPS
        random.seed(42 + fi + ep * 10000)

        # Find current scene
        current = None
        for start, end, scene, voice, sub in timeline:
            if start <= global_t < end:
                current = (start, end, scene, voice, sub)
                break
        if current is None:
            current = timeline[-1]

        start, end, scene, voice, sub = current
        local_t = global_t - start
        local_dur = end - start

        # Render scene
        img = render_scene(scene, local_t, local_dur, ep)

        # Subtitle overlay
        if sub and local_t > 0.1:
            sub_p = min(1, (local_t - 0.1) / 0.3)
            fade_out_p = max(0, min(1, (local_dur - local_t) / 0.3))
            alpha = int(min(sub_p, fade_out_p) * 160)
            if alpha > 10:
                # Convert to RGBA if needed
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                sub_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                sd = ImageDraw.Draw(sub_overlay)
                f = fnt(26, False)
                lines = sub.split("\n")
                lh = 34
                total_h = len(lines) * lh + 24
                sub_y = H - 250
                sd.rounded_rectangle([20, sub_y, W-20, sub_y+total_h], radius=14, fill=(0,0,0,alpha))
                for i, line in enumerate(lines):
                    lw = tw(sd, line, f)
                    sd.text(((W-lw)//2, sub_y+12+i*lh), line, font=f, fill=(*WHITE, min(255, alpha+80)))
                img = Image.alpha_composite(img, sub_overlay)

        # Scene transitions (crossfade)
        if local_t < 0.12 and prev_img is not None:
            tp = local_t / 0.12
            if img.mode != "RGBA": img = img.convert("RGBA")
            if prev_img.mode != "RGBA": prev_img = prev_img.convert("RGBA")
            img = Image.blend(prev_img, img, tp)

        # Global fades
        if img.mode == "RGBA":
            img = img.convert("RGB")

        if global_t < 0.5:
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, global_t / 0.5)
        if global_t > duration_sec - 1.0:
            p = (duration_sec - global_t) / 1.0
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, max(0, min(1, p)))

        if local_t >= local_dur - 1.0/FPS:
            prev_img = img.copy()

        img.save(str(frames_dir / f"f_{fi:05d}.png"), optimize=False)

        if fi % (FPS * 5) == 0:
            print(f"      {fi}/{total_frames} ({100*fi//total_frames}%)")

    print(f"    ✅ {total_frames} frames")
    return frames_dir


def assemble_episode(ep, frames_dir, audio, duration_sec):
    """Assemble frames + audio into final video."""
    from pydub import AudioSegment

    audio_path = SERIES_DIR / f"ep{ep}_audio.wav"
    audio.export(str(audio_path), format="wav")

    output = SERIES_DIR / f"episode_{ep}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_dir}/f_%05d.png",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(output)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        sz = os.path.getsize(output) / (1024*1024)
        print(f"    ✅ {output.name} ({sz:.1f} MB)")
    else:
        print(f"    ❌ {result.stderr[-500:]}")

    # Cleanup
    shutil.rmtree(frames_dir, ignore_errors=True)
    try: os.remove(str(audio_path))
    except: pass

    return output


def build_episode(ep):
    """Full pipeline for one episode."""
    print(f"\n{'='*60}")
    print(f"  🎬 СЕРИЯ {ep}")
    print(f"{'='*60}")

    voice_dir = SERIES_DIR / f"ep{ep}_voices"

    # 1. Generate voices
    print(f"\n  1️⃣ Генерация озвучки...")
    lines = get_episode_voices(ep)
    durations = generate_episode_voices(ep, lines, voice_dir)
    print(f"    ✅ {len(lines)} голосовых линий")

    # 2. Build timeline
    print(f"\n  2️⃣ Построение таймлайна...")
    timeline = build_episode_timeline(ep, durations)
    actual_dur = timeline[-1][1]
    # Clamp to ~60s
    target_dur = 60.0
    if actual_dur > target_dur + 2:
        # Trim last scene
        timeline[-1] = (timeline[-1][0], target_dur, timeline[-1][2], timeline[-1][3], timeline[-1][4])
        actual_dur = target_dur
    elif actual_dur < target_dur - 5:
        # Extend last scene
        timeline[-1] = (timeline[-1][0], target_dur, timeline[-1][2], timeline[-1][3], timeline[-1][4])
        actual_dur = target_dur

    print(f"    {len(timeline)} сцен, {actual_dur:.1f}с")
    for s, e, name, v, sub in timeline:
        print(f"    {s:5.1f}s-{e:5.1f}s  {name:25s} {'🎤' if v else '  '}")

    # 3. Mix audio
    print(f"\n  3️⃣ Микширование аудио...")
    audio = mix_episode_audio(ep, timeline, voice_dir, int(actual_dur * 1000))

    # 4. Render frames
    print(f"\n  4️⃣ Рендер кадров...")
    frames_dir = render_episode(ep, timeline, actual_dur)

    # 5. Assemble
    print(f"\n  5️⃣ Сборка видео...")
    output = assemble_episode(ep, frames_dir, audio, actual_dur)

    return output


def main():
    episodes_to_build = [1, 2, 3]
    if len(sys.argv) > 1:
        episodes_to_build = [int(x) for x in sys.argv[1:]]

    print("=" * 60)
    print("🎬 TODO BUDGET — МУЛЬТСЕРИАЛ (3 серии × 60с)")
    print("=" * 60)
    print(f"📐 {W}×{H} @ {FPS}fps")
    print(f"🎤 Озвучка: Edge TTS (Дмитрий + Светлана)")
    print(f"🎵 Генеративная музыка + SFX")
    print(f"📺 Серии: {episodes_to_build}")

    outputs = []
    for ep in episodes_to_build:
        out = build_episode(ep)
        outputs.append(out)

    print(f"\n{'='*60}")
    print(f"✅ ГОТОВО!")
    for o in outputs:
        if o.exists():
            sz = os.path.getsize(o) / (1024*1024)
            print(f"  📁 {o.name} ({sz:.1f} MB)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
