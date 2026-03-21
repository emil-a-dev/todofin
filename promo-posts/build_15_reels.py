#!/usr/bin/env python3
"""
🎬 Todo Budget — 15 Instagram Reels Generator
Each scenario → separate video file (1080×1920, 30fps, 25s)
Same engine as killer reels: PIL frame-by-frame + effects + electronic beat

Usage: python3 build_15_reels.py
"""

import os, sys, math, random, shutil, subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# ─── Config ──────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS = 30
BPM = 140
BEAT = 60.0 / BPM

BASE = Path(__file__).parent
OUT_DIR = BASE / "reels_15"
OUT_DIR.mkdir(exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colors
BG       = (6, 6, 18)
WHITE    = (255, 255, 255)
PURPLE   = (108, 58, 224)
GREEN    = (0, 229, 160)
RED      = (255, 107, 107)
CYAN     = (0, 201, 255)
ORANGE   = (255, 179, 71)
YELLOW   = (255, 220, 80)
DIM      = (80, 80, 120)
CARD_BG  = (30, 30, 56)
DARK_GREEN = (10, 42, 26)
LILAC    = (184, 160, 255)

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES (same engine as killer reels)
# ═══════════════════════════════════════════════════════════════════════════════

_font_cache = {}
def fnt(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    return _font_cache[key]


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def ease_out_elastic(t):
    t = max(0.0, min(1.0, t))
    if t == 0 or t == 1: return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2

def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

def color_lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def text_w(draw, text, f):
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0]

def text_h(draw, text, f):
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[3] - bbox[1]

def draw_centered(draw, y, text, f, fill=WHITE, shadow=True):
    tw = text_w(draw, text, f)
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0))
    draw.text((x, y), text, font=f, fill=fill)

def draw_rr(draw, rect, radius, fill, outline=None, width=0):
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)

def apply_shake(img, intensity):
    if intensity <= 0: return img
    dx = int(random.gauss(0, intensity))
    dy = int(random.gauss(0, intensity))
    return ImageChops.offset(img, dx, dy)

def apply_glitch(img, intensity):
    if intensity <= 0: return img
    arr = np.array(img)
    s = int(intensity)
    if s < 1: return img
    result = arr.copy()
    result[:, s:, 0] = arr[:, :-s, 0]
    result[:, :-s, 2] = arr[:, s:, 2]
    for _ in range(max(1, s // 2)):
        y = random.randint(0, H - 20)
        h = random.randint(3, 15)
        sx = random.randint(-s * 3, s * 3)
        if sx > 0:
            result[y:y+h, sx:, :] = result[y:y+h, :-sx, :]
        elif sx < 0:
            result[y:y+h, :sx, :] = result[y:y+h, -sx:, :]
    return Image.fromarray(result)

def apply_flash(img, intensity):
    if intensity <= 0: return img
    flash = Image.new("RGB", (W, H), WHITE)
    return Image.blend(img, flash, min(1.0, intensity))

def draw_particles(draw, t, count=30, color=PURPLE, seed=0):
    rng = random.Random(seed)
    for _ in range(count):
        speed = rng.uniform(0.3, 1.5)
        x = rng.randint(0, W)
        base_y = rng.randint(0, H)
        y = (base_y - t * speed * 200) % H
        sz = rng.uniform(1.5, 4)
        draw.ellipse([x - sz, y - sz, x + sz, y + sz], fill=color[:3])

def draw_glow(img, cx, cy, radius, color, intensity=0.15):
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(int(radius), 0, -4):
        a = intensity * (r / radius)
        c = tuple(int(ch * a) for ch in color)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    return ImageChops.add(img, glow)

def slam_text(draw, img, t, y_target, text, f, color=WHITE, delay=0):
    """Text that slams in with scale + shake + flash."""
    bt = t - delay
    if bt <= 0: return img
    p = ease_out_back(bt / 0.2)
    scale = max(1.0, lerp(2.5, 1.0, p))
    actual_f = fnt(int(f.size * scale), True)
    y = int(lerp(y_target - 100, y_target, ease_out_cubic(bt / 0.25)))
    c = color_lerp(BG, color, min(1.0, bt / 0.1))
    draw_centered(draw, y, text, actual_f, c)
    if bt < 0.07:
        img = apply_shake(img, 18 * (1 - bt / 0.07))
        img = apply_flash(img, 0.35 * (1 - bt / 0.07))
    return img

def slide_card(draw, img, t, y, texts, accent=PURPLE, delay=0, from_right=True):
    """Card that slides in from a side."""
    bt = t - delay
    if bt <= 0: return img
    p = ease_out_back(bt / 0.22)
    x_off = int(lerp(W + 100 if from_right else -W - 100, 0, p))
    rect = (70 + x_off, y, 1010 + x_off, y + 50 + 35 * len(texts))
    draw_rr(draw, rect, 22, CARD_BG, outline=(*accent, 60), width=2)
    for i, (txt, col, sz, bold) in enumerate(texts):
        draw.text((130 + x_off, y + 20 + i * 35), txt, font=fnt(sz, bold), fill=col)
    if bt < 0.06:
        img = apply_shake(img, 10)
    return img

def typewriter(draw, t, y, full_text, f, color=DIM, delay=0, speed=0.8):
    """Character-by-character text reveal."""
    bt = t - delay
    if bt <= 0: return
    chars = int(len(full_text) * min(1, bt / speed))
    text = full_text[:chars]
    if text:
        draw_centered(draw, y, text, f, color, shadow=False)

def draw_arc_progress(draw, cx, cy, radius, progress, color=RED, width=8):
    """Draw a circular progress arc."""
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 outline=(*color[:3], 30), width=4)
    start = -90
    end = start + 360 * progress
    draw.arc([cx - radius, cy - radius, cx + radius, cy + radius],
             start, end, fill=color, width=width)

def draw_bar_chart(draw, t, y_base, bars, delay=0):
    """Animated horizontal bar chart."""
    bt = t - delay
    if bt <= 0: return
    for i, (label, value, max_w, color, amount_text) in enumerate(bars):
        entry_t = bt - i * BEAT * 0.35
        if entry_t <= 0: continue
        p = ease_out_cubic(entry_t / 0.4)
        y = y_base + i * 55
        w = int(max_w * p)
        draw.rounded_rectangle([110, y, 110 + w, y + 30], radius=8, fill=color)
        if p > 0.5:
            draw.text((120 + max_w + 15, y + 3), f"{label} — {amount_text}",
                      font=fnt(15, False), fill=DIM)

def cta_block(draw, img, t, delay=0):
    """Reusable CTA at the end of each video."""
    bt = t - delay
    if bt <= 0: return img
    # Button
    p = ease_out_back(bt / 0.25)
    y = int(lerp(1500, 1350, p))
    bw, bh = 520, 86
    draw_rr(draw, (W // 2 - bw // 2, y, W // 2 + bw // 2, y + bh), bh // 2, PURPLE)
    draw_centered(draw, y + 20, "📲 Скачать в RuStore", fnt(30), WHITE, shadow=False)
    if bt < 0.06:
        img = apply_shake(img, 12)
    # URL
    url_t = bt - BEAT
    if url_t > 0:
        p2 = ease_out_cubic(url_t / 0.3)
        draw_centered(draw, y + bh + 20, "emil-a-dev.github.io/todofin",
                      fnt(22, False), color_lerp(BG, CYAN, p2), shadow=False)
    return img


def bottom_text(draw, t, text, delay=0):
    """Bottom screen text that fades in."""
    bt = t - delay
    if bt <= 0: return
    p = ease_out_cubic(bt / 0.3)
    draw_centered(draw, 1700, text, fnt(28, False),
                  color_lerp(BG, DIM, p), shadow=False)
    pulse_t = bt - 0.3
    if pulse_t > 0:
        a = 0.5 + 0.5 * math.sin(pulse_t * 3)
        draw_centered(draw, 1760, "Ссылка в описании ↓", fnt(20, False),
                      color_lerp(BG, DIM, a), shadow=False)


# ═══════════════════════════════════════════════════════════════════════════════
# 15 SCENARIO BUILDERS
# Each returns: (scene_list, total_duration, accent_color, bpm)
#   scene_list = [(renderer_func, duration, transition_type), ...]
# ═══════════════════════════════════════════════════════════════════════════════

def scenario_01():
    """Morning Control"""
    DUR = 28

    def sc_wake(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Screen lights up — glow expanding
        glow_r = int(lerp(0, 600, ease_out_cubic(t / 1.5)))
        if glow_r > 0:
            img = draw_glow(img, W//2, H//2, glow_r, PURPLE, 0.05)
            draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, PURPLE, seed=101)
        # "Утро" typewriter
        typewriter(draw, t, 850, "Утро. Телефон. Контроль.", fnt(42, False), DIM, delay=0.5)
        return img

    def sc_dashboard(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        img = draw_glow(img, W//2, 400, 400, PURPLE, 0.04)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=102)
        # Dashboard title
        p0 = ease_out_back(t / 0.2)
        draw_centered(draw, int(lerp(-80, 180, p0)), "📊 Дашборд", fnt(52), WHITE)
        if t < 0.06: img = apply_shake(img, 12); draw = ImageDraw.Draw(img)
        # Balance card
        bt1 = t - BEAT
        if bt1 > 0:
            p = ease_out_back(bt1 / 0.2)
            y_off = int(lerp(150, 0, p))
            draw_rr(draw, (70, 320+y_off, 1010, 480+y_off), 24, CARD_BG, outline=(*GREEN,50), width=2)
            draw.text((110, 345+y_off), "Баланс", font=fnt(20, False), fill=DIM)
            val = int(42350 * min(1, max(0, bt1-0.2)/0.5))
            if val > 0:
                draw.text((110, 390+y_off), f"₽{val:,}".replace(",", " "), font=fnt(52), fill=GREEN)
        # Task add
        bt2 = t - BEAT * 3
        if bt2 > 0:
            texts = [("+ Оплатить аренду", WHITE, 26, True), ("Приоритет: Высокий", RED, 18, False)]
            img = slide_card(draw, img, t, 540, texts, RED, delay=BEAT*3, from_right=True)
            draw = ImageDraw.Draw(img)
        # Expense add
        bt3 = t - BEAT * 5
        if bt3 > 0:
            texts = [("– ₽25 000 · Жильё", ORANGE, 26, True), ("Категория: Аренда", DIM, 18, False)]
            img = slide_card(draw, img, t, 710, texts, ORANGE, delay=BEAT*5, from_right=False)
            draw = ImageDraw.Draw(img)
        return img

    def sc_stats(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=103)
        img = draw_glow(img, W//2, 500, 350, GREEN, 0.04)
        draw = ImageDraw.Draw(img)
        # Updated balance
        img = slam_text(draw, img, t, 350, "₽17 350", fnt(90), GREEN)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 480, "Обновлённый баланс", fnt(28, False),
                      color_lerp(BG, DIM, min(1, t/0.5)), shadow=False)
        # Chart
        bars = [("Жильё", 0, 500, ORANGE, "₽25 000"),
                ("Еда", 0, 350, RED, "₽8 500"),
                ("Транспорт", 0, 200, CYAN, "₽3 200")]
        draw_bar_chart(draw, t, 600, bars, delay=BEAT*2)
        # CTA text
        bt_cta = t - BEAT * 5
        if bt_cta > 0:
            draw_centered(draw, 860, "Начни утро с порядка.", fnt(38),
                          color_lerp(BG, WHITE, min(1, bt_cta/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget — бесплатно", delay=BEAT*7)
        return img

    scenes = [
        (sc_wake,      3.5, "flash"),
        (sc_dashboard,  4.5, "glitch"),
        (sc_stats,      5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), PURPLE, BPM


def scenario_02():
    """One App Instead of Three"""
    def sc_apps(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, RED, seed=201)
        # Three app names slam in one by one
        apps = [("📝 Заметки", RED), ("✅ To-Do", ORANGE), ("💰 Бюджет", CYAN)]
        for i, (name, col) in enumerate(apps):
            bt = t - BEAT * (i * 1.2)
            if bt > 0:
                p = ease_out_back(bt / 0.2)
                y = 500 + i * 180
                x_off = int(lerp(-W, 0, p))
                draw_rr(draw, (120+x_off, y, 960+x_off, y+140), 28, CARD_BG, outline=(*col,60), width=3)
                draw.text((180+x_off, y+40), name, font=fnt(46), fill=col)
                if bt < 0.06: img = apply_shake(img, 14); draw = ImageDraw.Draw(img)
        # "3 приложения"
        typewriter(draw, t, 350, "3 приложения", fnt(56), WHITE, delay=0.2)
        typewriter(draw, t, 1120, "3 подписки...", fnt(36, False), DIM, delay=BEAT*3)
        return img

    def sc_switch(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Glitch transition text
        typewriter(draw, t, 800, "А что если...", fnt(52, False), DIM, delay=0)
        bt = t - BEAT * 2
        if bt > 0:
            img = slam_text(draw, img, t, 920, "ОДНО?", fnt(90), PURPLE, delay=BEAT*2)
            draw = ImageDraw.Draw(img)
        if 0 < t < 0.1: img = apply_glitch(img, 25)
        return img

    def sc_todo_budget(t, dur):
        img = Image.new("RGB", (W, H), BG)
        pulse = 0.06 + 0.03 * math.sin(t * 4)
        img = draw_glow(img, W//2, 600, 500, PURPLE, pulse)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 40, PURPLE, seed=203)
        # Icon
        p0 = ease_out_back(t / 0.3)
        sz = int(120 * p0)
        if sz > 5:
            cx, cy = W//2, 480
            r = sz // 2
            draw_rr(draw, (cx-r, cy-r, cx+r, cy+r), max(5, int(sz*0.28)), PURPLE)
            cf = fnt(int(sz * 0.6))
            draw.text((cx - text_w(draw, "✓", cf)//2, cy - 35), "✓", font=cf, fill=WHITE)
        # Name
        img = slam_text(draw, img, t, 600, "Todo Budget", fnt(80), WHITE, delay=BEAT)
        draw = ImageDraw.Draw(img)
        # Features scroll
        features = ["✅ Задачи", "💰 Финансы", "⏱ Помодоро", "📝 Заметки"]
        for i, feat in enumerate(features):
            ft = t - BEAT * (2.5 + i * 0.7)
            if ft > 0:
                p = ease_out_cubic(ft / 0.3)
                draw_centered(draw, int(lerp(780, 740, p)) + i * 55, feat, fnt(32, False),
                              color_lerp(BG, WHITE, p), shadow=False)
        # Bottom
        draw_centered(draw, 1020, "Всё в одном месте.", fnt(36),
                      color_lerp(BG, GREEN, min(1, max(0, t-BEAT*5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "0 ₽ · Навсегда", delay=BEAT*7)
        return img

    scenes = [
        (sc_apps,        4.0, "glitch"),
        (sc_switch,      2.5, "flash"),
        (sc_todo_budget, 5.5, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), PURPLE, BPM


def scenario_03():
    """Fast Add Challenge"""
    def sc_timer(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, RED, seed=301)
        img = draw_glow(img, W//2, H//2, 400, RED, 0.04)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 400, "Челлендж:", fnt(44, False), DIM, delay=0)
        img = slam_text(draw, img, t, 500, "Добавь за 3 сек", fnt(62), WHITE, delay=BEAT)
        draw = ImageDraw.Draw(img)
        # Countdown 3, 2, 1
        countdown_t = t - BEAT * 2.5
        if countdown_t > 0:
            num = 3 - int(countdown_t / BEAT)
            if 1 <= num <= 3:
                p = ease_out_elastic((countdown_t % BEAT) / BEAT)
                scale = max(1, lerp(4, 1, p))
                draw_centered(draw, 750, str(num), fnt(min(200, int(150*scale))), RED)
        return img

    def sc_fast_add(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=302)
        # Task added
        img = slam_text(draw, img, t, 350, "✅ Задача", fnt(56), GREEN)
        draw = ImageDraw.Draw(img)
        texts = [("Купить молоко", WHITE, 26, True), ("Приоритет: Средний · Сегодня", DIM, 16, False)]
        img = slide_card(draw, img, t, 480, texts, GREEN, delay=BEAT, from_right=True)
        draw = ImageDraw.Draw(img)
        # Expense added
        bt2 = t - BEAT * 2.5
        if bt2 > 0:
            draw_centered(draw, 680, "💰 Расход", fnt(56),
                          color_lerp(BG, ORANGE, min(1, bt2/0.15)))
            if bt2 < 0.06: img = apply_shake(img, 14); draw = ImageDraw.Draw(img)
        texts2 = [("– ₽350 · Продукты", ORANGE, 26, True)]
        img = slide_card(draw, img, t, 790, texts2, ORANGE, delay=BEAT*3, from_right=False)
        draw = ImageDraw.Draw(img)
        # Stats update
        bt3 = t - BEAT * 4.5
        if bt3 > 0:
            p = ease_out_cubic(bt3 / 0.4)
            draw_rr(draw, (70, 940, 1010, 1060), 24, CARD_BG, outline=(*CYAN,40), width=1)
            bar_w = int(700 * p)
            draw.rounded_rectangle([90, 970, 90+bar_w, 990], radius=8, fill=CYAN)
            draw.text((110, 1010), "Статистика обновлена ✓", font=fnt(18, False), fill=CYAN)
        return img

    def sc_done(t, dur):
        img = Image.new("RGB", (W, H), BG)
        img = draw_glow(img, W//2, 600, 500, GREEN, 0.06)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 30, GREEN, seed=303)
        img = slam_text(draw, img, t, 500, "Готово", fnt(100), GREEN)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 650, "за секунды.", fnt(44, False),
                      color_lerp(BG, DIM, min(1, max(0, t-0.3)/0.3)), shadow=False)
        img = cta_block(draw, img, t, delay=BEAT*3)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget — мгновенно", delay=BEAT*4)
        return img

    scenes = [
        (sc_timer,    3.5, "flash"),
        (sc_fast_add, 4.0, "glitch"),
        (sc_done,     4.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), RED, BPM


def scenario_04():
    """Visual Money Flow"""
    def sc_empty(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, DIM, seed=401)
        typewriter(draw, t, 750, "Баланс: ₽0", fnt(60), DIM, delay=0.3)
        typewriter(draw, t, 850, "Пустой экран...", fnt(32, False), DIM, delay=1.0)
        return img

    def sc_income(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=402)
        img = draw_glow(img, W//2, 450, 400, GREEN, 0.05)
        draw = ImageDraw.Draw(img)
        # Income added
        img = slam_text(draw, img, t, 280, "+ ₽85 000", fnt(80), GREEN)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 400, "Зарплата", fnt(30, False),
                      color_lerp(BG, DIM, min(1, max(0, t-0.3)/0.3)), shadow=False)
        # Balance rises
        bt = t - BEAT * 2
        if bt > 0:
            val = int(85000 * min(1, bt / 0.6))
            draw_centered(draw, 550, f"₽{val:,}".replace(",", " "), fnt(56), GREEN)
        # Expenses subtract
        expenses = [
            ("– ₽25 000 Аренда", RED, BEAT*3.5),
            ("– ₽8 500 Еда", ORANGE, BEAT*4.5),
            ("– ₽3 200 Транспорт", CYAN, BEAT*5.5),
        ]
        for i, (txt, col, delay) in enumerate(expenses):
            bt2 = t - delay
            if bt2 > 0:
                p = ease_out_back(bt2 / 0.2)
                x_off = int(lerp(-W, 0, p))
                y = 700 + i * 80
                draw.text((120 + x_off, y), txt, font=fnt(28), fill=col)
                if bt2 < 0.06: img = apply_shake(img, 10); draw = ImageDraw.Draw(img)
        return img

    def sc_chart(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=403)
        img = draw_glow(img, W//2, 500, 350, CYAN, 0.04)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 200, "💹 Тренды", fnt(52), WHITE)
        # Animated line chart (simple representation)
        chart_t = t - BEAT
        if chart_t > 0:
            p = ease_out_cubic(chart_t / 1.5)
            points = [(120, 700), (250, 500), (400, 600), (540, 450),
                      (680, 550), (820, 380), (960, 420)]
            visible = int(len(points) * p)
            for i in range(1, visible):
                x1, y1 = points[i-1]
                x2, y2 = points[i]
                draw.line([(x1, y1), (x2, y2)], fill=GREEN, width=4)
                draw.ellipse([x2-6, y2-6, x2+6, y2+6], fill=GREEN)
        # Final balance
        bt2 = t - BEAT * 4
        if bt2 > 0:
            draw_centered(draw, 850, "Остаток: ₽48 300", fnt(44), GREEN)
        draw_centered(draw, 950, "Видно куда уходят деньги.", fnt(30, False),
                      color_lerp(BG, DIM, min(1, max(0, t-BEAT*5)/0.3)), shadow=False)
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget — бесплатно", delay=BEAT*7)
        return img

    scenes = [
        (sc_empty,  3.0, "flash"),
        (sc_income, 5.0, "glitch"),
        (sc_chart,  5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), GREEN, BPM


def scenario_05():
    """Pomodoro Focus"""
    def sc_open(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, RED, seed=501)
        img = draw_glow(img, W//2, H//2, 400, RED, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 600, "⏱ Помодоро", fnt(70), WHITE)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 730, "25 минут фокуса", fnt(36, False), DIM, delay=BEAT*2)
        return img

    def sc_timer(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, RED, seed=502)
        img = draw_glow(img, W//2, 600, 350, RED, 0.03)
        draw = ImageDraw.Draw(img)
        # Animated timer circle
        progress = ease_in_out_cubic(t / dur) * 0.85
        cx, cy = W//2, 580
        draw_arc_progress(draw, cx, cy, 200, progress, RED, 10)
        total_secs = int(25 * 60 * (1 - progress))
        m, s = divmod(total_secs, 60)
        draw.text((cx - 110, cy - 50), f"{m:02d}:{s:02d}", font=fnt(80), fill=WHITE)
        draw_centered(draw, cy + 60, "Фокусировка...", fnt(24, False), (255, 150, 150))
        # Pulsing ring
        ring_p = 0.5 + 0.5 * math.sin(t * 3)
        draw.ellipse([cx - 220, cy - 220, cx + 220, cy + 220],
                     outline=color_lerp(BG, RED, ring_p * 0.3), width=2)
        return img

    def sc_done(t, dur):
        img = Image.new("RGB", (W, H), BG)
        img = draw_glow(img, W//2, 500, 500, GREEN, 0.06)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 35, GREEN, seed=503)
        img = slam_text(draw, img, t, 400, "✅ Готово!", fnt(90), GREEN)
        draw = ImageDraw.Draw(img)
        bt = t - BEAT * 2
        if bt > 0:
            texts = [("Подготовить отчёт", GREEN, 28, True), ("Выполнено ✓", GREEN, 18, False)]
            img = slide_card(draw, img, t, 600, texts, GREEN, delay=BEAT*2)
            draw = ImageDraw.Draw(img)
        draw_centered(draw, 820, "Фокус. Финиш. Трекинг.", fnt(38),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*4)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*5)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*6)
        return img

    scenes = [
        (sc_open,  3.0, "flash"),
        (sc_timer, 5.0, "glitch"),
        (sc_done,  4.5, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), RED, BPM


def scenario_06():
    """Weekly Overview"""
    def sc_open(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=601)
        img = draw_glow(img, W//2, H//2, 400, CYAN, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 600, "📊 Неделя", fnt(70), WHITE)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 730, "Итоги за 7 дней", fnt(36, False), DIM, delay=BEAT*2)
        return img

    def sc_categories(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=602)
        img = draw_glow(img, 300, 400, 300, CYAN, 0.03)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 200, "Расходы по категориям", fnt(38), WHITE)
        bars = [
            ("Еда", 0, 500, RED, "₽8 500"),
            ("Транспорт", 0, 350, ORANGE, "₽5 200"),
            ("Развлечения", 0, 250, CYAN, "₽4 100"),
            ("Жильё", 0, 600, LILAC, "₽25 000"),
            ("Прочее", 0, 180, YELLOW, "₽2 850"),
        ]
        draw_bar_chart(draw, t, 350, bars, delay=BEAT)
        # Highlight biggest
        bt = t - BEAT * 4
        if bt > 0:
            p = ease_out_elastic(bt / 0.3)
            draw_rr(draw, (70, 660, 1010, 740), 20, (*LILAC, 15), outline=(*LILAC,60), width=2)
            draw_centered(draw, 675, "⚠ Жильё — 54% расходов", fnt(26), LILAC)
        return img

    def sc_savings(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=603)
        img = draw_glow(img, W//2, 500, 400, GREEN, 0.05)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 400, "Сэкономлено", fnt(50), DIM)
        draw = ImageDraw.Draw(img)
        bt = t - BEAT * 1.5
        if bt > 0:
            val = int(12400 * min(1, bt / 0.5))
            draw_centered(draw, 500, f"₽{val:,}".replace(",", " "), fnt(90), GREEN)
            if bt < 0.06: img = apply_shake(img, 20); img = apply_flash(img, 0.4); draw = ImageDraw.Draw(img)
        # Savings %
        bt2 = t - BEAT * 3.5
        if bt2 > 0:
            p = ease_out_cubic(bt2 / 0.4)
            pct = int(14.6 * p)
            draw_centered(draw, 640, f"↑ {pct}% от дохода", fnt(32, False), GREEN)
        draw_centered(draw, 780, "Знай свою неделю.", fnt(38),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*7)
        return img

    scenes = [
        (sc_open,       2.5, "flash"),
        (sc_categories, 4.0, "glitch"),
        (sc_savings,    5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), CYAN, BPM


def scenario_07():
    """Minimalist Lifestyle"""
    def sc_clean(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Minimal particles
        draw_particles(draw, t, 8, LILAC, seed=701)
        img = draw_glow(img, W//2, H//2, 300, LILAC, 0.03)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 800, "Минимализм.", fnt(56), WHITE, delay=0.3)
        typewriter(draw, t, 880, "Ничего лишнего.", fnt(36, False), DIM, delay=1.2)
        return img

    def sc_ui(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 10, LILAC, seed=702)
        img = draw_glow(img, W//2, 500, 300, LILAC, 0.03)
        draw = ImageDraw.Draw(img)
        # Clean UI cards sliding
        items = [
            ("📝 Новая заметка", "Идеи на выходные", LILAC),
            ("✅ Купить кофе", "Сегодня, 10:00", GREEN),
            ("💰 Баланс: ₽42 350", "↑ +12%", GREEN),
        ]
        for i, (title, sub, col) in enumerate(items):
            bt = t - BEAT * (1 + i * 1.2)
            if bt > 0:
                p = ease_out_cubic(bt / 0.35)
                y = 350 + i * 180
                alpha_f = min(1.0, bt / 0.3)
                draw_rr(draw, (90, y, 990, y + 140), 22, CARD_BG, outline=(*col, int(40*alpha_f)), width=1)
                draw.text((150, y + 30), title, font=fnt(26), fill=color_lerp(BG, WHITE, alpha_f))
                draw.text((150, y + 75), sub, font=fnt(18, False), fill=color_lerp(BG, DIM, alpha_f))
        return img

    def sc_calm(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 12, LILAC, seed=703)
        img = draw_glow(img, W//2, 600, 400, LILAC, 0.04)
        draw = ImageDraw.Draw(img)
        # Summary card
        bt = t - BEAT
        if bt > 0:
            p = ease_out_back(bt / 0.3)
            y_off = int(lerp(100, 0, p))
            draw_rr(draw, (70, 400+y_off, 1010, 700+y_off), 24, CARD_BG)
            draw.text((110, 430+y_off), "Финансовый обзор", font=fnt(22, False), fill=DIM)
            draw.text((110, 480+y_off), "₽42 350", font=fnt(56), fill=GREEN)
            draw.text((110, 560+y_off), "3 задачи · 2 заметки · ₽48.3к расходов", font=fnt(18, False), fill=DIM)
            draw.text((110, 600+y_off), "Всё под контролем ✓", font=fnt(22), fill=GREEN)

        draw_centered(draw, 800, "Просто. Чисто. Эффективно.", fnt(36),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*3)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*4)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*5)
        return img

    scenes = [
        (sc_clean, 3.0, "flash"),
        (sc_ui,    4.5, "flash"),
        (sc_calm,  4.5, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), LILAC, BPM


def scenario_08():
    """Productivity Loop"""
    def sc_plan(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, PURPLE, seed=801)
        img = draw_glow(img, W//2, H//2, 400, PURPLE, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 450, "1. ПЛАН", fnt(80), PURPLE)
        draw = ImageDraw.Draw(img)
        texts = [("+ Написать статью", WHITE, 28, True), ("Срок: Сегодня, 18:00", DIM, 18, False)]
        img = slide_card(draw, img, t, 620, texts, PURPLE, delay=BEAT*2)
        draw = ImageDraw.Draw(img)
        return img

    def sc_work(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, RED, seed=802)
        img = draw_glow(img, W//2, 550, 350, RED, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 350, "2. РАБОТА", fnt(80), RED)
        draw = ImageDraw.Draw(img)
        # Pomodoro mini
        bt = t - BEAT * 1.5
        if bt > 0:
            cx, cy = W//2, 620
            progress = ease_out_cubic(bt / 2.0) * 0.6
            draw_arc_progress(draw, cx, cy, 130, progress, RED, 8)
            m = int(25 * (1 - progress))
            draw.text((cx - 60, cy - 30), f"{m:02d}:00", font=fnt(52), fill=WHITE)
        return img

    def sc_track(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=803)
        img = draw_glow(img, W//2, 550, 350, GREEN, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 350, "3. ТРЕКИНГ", fnt(80), GREEN)
        draw = ImageDraw.Draw(img)
        # Task completed
        bt1 = t - BEAT * 2
        if bt1 > 0:
            texts = [("✅ Статья написана", GREEN, 26, True)]
            img = slide_card(draw, img, t, 520, texts, GREEN, delay=BEAT*2)
            draw = ImageDraw.Draw(img)
        # Expense logged
        bt2 = t - BEAT * 3.5
        if bt2 > 0:
            texts = [("+ ₽5 000 · Гонорар", GREEN, 26, True)]
            img = slide_card(draw, img, t, 660, texts, GREEN, delay=BEAT*3.5, from_right=False)
            draw = ImageDraw.Draw(img)
        return img

    def sc_loop(t, dur):
        img = Image.new("RGB", (W, H), BG)
        pulse = 0.05 + 0.03 * math.sin(t * 4)
        img = draw_glow(img, W//2, 600, 500, PURPLE, pulse)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 30, PURPLE, seed=804)
        # Loop text
        draw_centered(draw, 500, "План → Работа → Трекинг", fnt(38),
                      color_lerp(BG, WHITE, min(1, t/0.5)))
        draw_centered(draw, 570, "↻ Повтори", fnt(50), PURPLE)
        img = cta_block(draw, img, t, delay=BEAT*3)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*4)
        return img

    scenes = [
        (sc_plan,  2.5, "flash"),
        (sc_work,  3.0, "glitch"),
        (sc_track, 3.0, "glitch"),
        (sc_loop,  4.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), PURPLE, BPM


def scenario_09():
    """Monthly Reset"""
    def sc_new_month(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=901)
        img = draw_glow(img, W//2, H//2, 400, CYAN, 0.04)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 700, "Март 2026", fnt(70), WHITE, delay=0.2)
        typewriter(draw, t, 800, "Новый месяц.", fnt(40, False), DIM, delay=0.8)
        return img

    def sc_budget_set(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=902)
        img = draw_glow(img, 300, 400, 300, GREEN, 0.03)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 200, "Установи лимиты", fnt(44), WHITE)
        budgets = [
            ("Еда", "₽12 000", RED, 450),
            ("Транспорт", "₽5 000", ORANGE, 190),
            ("Развлечения", "₽8 000", CYAN, 300),
        ]
        for i, (cat, amount, col, bar_max) in enumerate(budgets):
            bt = t - BEAT * (1 + i * 0.8)
            if bt <= 0: continue
            p = ease_out_back(bt / 0.2)
            y = 340 + i * 160
            x_off = int(lerp(W, 0, p))
            draw_rr(draw, (70+x_off, y, 1010+x_off, y+120), 22, CARD_BG, outline=(*col,40), width=1)
            draw.text((110+x_off, y+20), cat, font=fnt(24), fill=WHITE)
            draw.text((110+x_off, y+60), f"Лимит: {amount}", font=fnt(20, False), fill=col)
            # Progress bar (empty)
            draw.rounded_rectangle([500+x_off, y+70, 500+x_off+bar_max, y+82], radius=6, outline=(*col,40), width=1)
            if bt < 0.06: img = apply_shake(img, 8); draw = ImageDraw.Draw(img)
        return img

    def sc_progress(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=903)
        img = draw_glow(img, W//2, 500, 400, GREEN, 0.05)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 250, "Первые расходы", fnt(44), WHITE)
        # Progress bars filling
        budgets = [
            ("Еда", 0.35, 450, RED),
            ("Транспорт", 0.20, 450, ORANGE),
            ("Развлечения", 0.15, 450, CYAN),
        ]
        for i, (cat, fill_pct, bar_max, col) in enumerate(budgets):
            bt = t - BEAT * (1 + i * 0.6)
            if bt <= 0: continue
            p = ease_out_cubic(bt / 0.6)
            y = 400 + i * 120
            draw.text((110, y), cat, font=fnt(22), fill=WHITE)
            w = int(bar_max * fill_pct * p)
            draw.rounded_rectangle([110, y+35, 110+bar_max, y+50], radius=8, outline=(*col,30), width=1)
            draw.rounded_rectangle([110, y+35, 110+w, y+50], radius=8, fill=col)
            pct = int(fill_pct * 100 * p)
            draw.text((570, y+30), f"{pct}%", font=fnt(18), fill=col)

        draw_centered(draw, 820, "Новый месяц. Свежий контроль.", fnt(34),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*4)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*5)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*6)
        return img

    scenes = [
        (sc_new_month,  2.5, "flash"),
        (sc_budget_set, 4.0, "glitch"),
        (sc_progress,   5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), CYAN, BPM


def scenario_10():
    """Statistics Power"""
    def sc_open(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=1001)
        img = draw_glow(img, W//2, H//2, 400, CYAN, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 550, "📈 Аналитика", fnt(70), WHITE)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 700, "Данные которые помогают", fnt(30, False), DIM, delay=BEAT*2)
        return img

    def sc_pie(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, CYAN, seed=1002)
        img = draw_glow(img, W//2, 550, 300, CYAN, 0.03)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 220, "Расходы", fnt(38), WHITE)
        # Animated pie chart
        cx, cy, r = W//2, 560, 180
        slices = [(0.35, RED), (0.25, ORANGE), (0.22, CYAN), (0.18, LILAC)]
        progress = ease_out_cubic(t / 1.5)
        start = -90
        for pct, col in slices:
            sweep = 360 * pct * progress
            if sweep > 0.5:
                draw.pieslice([cx-r, cy-r, cx+r, cy+r], start, start + sweep, fill=col, outline=BG, width=2)
            start += sweep
        # Labels
        labels = [("Еда 35%", RED), ("Транспорт 25%", ORANGE), ("Развлечения 22%", CYAN), ("Прочее 18%", LILAC)]
        for i, (lbl, col) in enumerate(labels):
            lt = t - BEAT * 2 - i * 0.15
            if lt > 0:
                p = ease_out_cubic(lt / 0.2)
                draw.text((150, 800 + i * 40), "●", font=fnt(16), fill=col)
                draw.text((180, 800 + i * 40), lbl, font=fnt(18, False), fill=color_lerp(BG, WHITE, p))
        return img

    def sc_line(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=1003)
        img = draw_glow(img, W//2, 450, 350, GREEN, 0.04)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 200, "📊 Баланс за месяц", fnt(38), WHITE)
        # Line graph
        points = [(100, 600), (220, 550), (350, 580), (480, 500),
                  (600, 520), (720, 440), (850, 430), (970, 400)]
        p = ease_out_cubic(t / 1.5)
        vis = max(2, int(len(points) * p))
        for i in range(1, vis):
            x1, y1 = points[i-1]; x2, y2 = points[i]
            draw.line([(x1, y1), (x2, y2)], fill=GREEN, width=4)
            draw.ellipse([x2-5, y2-5, x2+5, y2+5], fill=GREEN)
        # Balance comparison
        bt = t - BEAT * 3
        if bt > 0:
            draw_centered(draw, 700, "Начало: ₽35 000", fnt(28, False), DIM)
            draw_centered(draw, 750, "Конец:  ₽48 300", fnt(28), GREEN)
            draw_centered(draw, 810, "↑ +38%", fnt(52), GREEN)
        draw_centered(draw, 950, "Данные помогают решать.", fnt(34),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*7)
        return img

    scenes = [
        (sc_open, 2.5, "flash"),
        (sc_pie,  4.0, "glitch"),
        (sc_line, 5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), CYAN, BPM


def scenario_11():
    """Dark Mode Aesthetic"""
    DARK_BG = (3, 3, 10)
    def sc_switch(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 10, LILAC, seed=1101)
        # Theme toggle
        typewriter(draw, t, 750, "Тёмная тема", fnt(60), WHITE, delay=0.2)
        bt = t - BEAT * 2
        if bt > 0:
            p = ease_out_cubic(bt / 0.5)
            # Expanding dark circle
            r = int(lerp(0, 1500, p))
            draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], fill=DARK_BG)
            if bt > 0.3:
                draw_centered(draw, 850, "🌙", fnt(80), WHITE)
        return img

    def sc_scroll(t, dur):
        img = Image.new("RGB", (W, H), DARK_BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 12, LILAC, seed=1102)
        img = draw_glow(img, W//2, 500, 350, LILAC, 0.03)
        draw = ImageDraw.Draw(img)
        # Dark mode cards
        items = [
            ("✅ Дашборд", "3 задачи · ₽42 350", LILAC),
            ("📝 Заметки", "2 записи", CYAN),
            ("⏱ Помодоро", "25:00", RED),
        ]
        for i, (title, sub, col) in enumerate(items):
            bt = t - BEAT * (0.5 + i * 1.0)
            if bt <= 0: continue
            p = ease_out_cubic(bt / 0.35)
            y = 350 + i * 180
            draw_rr(draw, (80, y, 1000, y + 140), 22, (15, 15, 30), outline=(*col, int(30*p)), width=1)
            draw.text((140, y + 35), title, font=fnt(28), fill=color_lerp(DARK_BG, WHITE, p))
            draw.text((140, y + 80), sub, font=fnt(18, False), fill=color_lerp(DARK_BG, DIM, p))
        return img

    def sc_chart(t, dur):
        img = Image.new("RGB", (W, H), DARK_BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, LILAC, seed=1103)
        img = draw_glow(img, W//2, 500, 400, LILAC, 0.04)
        draw = ImageDraw.Draw(img)
        # Transaction
        bt = t - 0.3
        if bt > 0:
            p = ease_out_back(bt / 0.2)
            y_off = int(lerp(100, 0, p))
            draw_rr(draw, (70, 300+y_off, 1010, 450+y_off), 24, (15, 15, 30), outline=(*ORANGE, 40), width=1)
            draw.text((110, 330+y_off), "– ₽1 500 · Кафе", font=fnt(28), fill=ORANGE)
            draw.text((110, 380+y_off), "Развлечения · Сегодня", font=fnt(18, False), fill=DIM)
        # Elegant chart
        bt2 = t - BEAT * 2
        if bt2 > 0:
            draw_rr(draw, (70, 500, 1010, 850), 24, (15, 15, 30))
            bars_data = [
                ("", 0, 400, LILAC, ""), ("", 0, 300, LILAC, ""),
                ("", 0, 350, LILAC, ""), ("", 0, 250, RED, ""),
                ("", 0, 450, GREEN, ""), ("", 0, 280, LILAC, ""),
            ]
            p = ease_out_cubic(bt2 / 1.0)
            for i, (_, _, max_h_val, col, _) in enumerate(bars_data):
                h = int(max_h_val / 3 * p)
                x = 130 + i * 140
                y_bottom = 820
                draw.rounded_rectangle([x, y_bottom - h, x + 80, y_bottom], radius=8, fill=col)
        draw_centered(draw, 900, "Комфорт в любое время.", fnt(34),
                      color_lerp(DARK_BG, WHITE, min(1, max(0, t-BEAT*4)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*5)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*6)
        return img

    scenes = [
        (sc_switch, 3.0, "flash"),
        (sc_scroll, 3.5, "flash"),
        (sc_chart,  5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), LILAC, BPM


def scenario_12():
    """Daily Micro Habits"""
    def sc_micro(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 15, GREEN, seed=1201)
        img = draw_glow(img, W//2, H//2, 400, GREEN, 0.03)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 550, "Микро-привычки", fnt(60), WHITE)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 680, "Маленькие шаги каждый день", fnt(28, False), DIM, delay=BEAT*2)
        return img

    def sc_actions(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=1202)
        # Fast cuts of adding things
        actions = [
            ("✅ + Выпить воду", GREEN, "Задача"),
            ("💰 – ₽150 кофе", ORANGE, "Расход"),
            ("✅ + Прогулка 15 мин", GREEN, "Задача"),
            ("💰 – ₽350 обед", ORANGE, "Расход"),
            ("✅ + Прочитать 10 стр", GREEN, "Задача"),
            ("💰 + ₽500 кешбэк", CYAN, "Доход"),
        ]
        for i, (txt, col, cat) in enumerate(actions):
            bt = t - BEAT * (i * 0.6)
            if bt <= 0: continue
            p = ease_out_back(bt / 0.15)
            y = 300 + (i % 4) * 130
            side = i % 2 == 0
            x_off = int(lerp(W if side else -W, 0, p))
            draw_rr(draw, (80+x_off, y, 1000+x_off, y+100), 20, CARD_BG, outline=(*col, 50), width=2)
            draw.text((140+x_off, y+15), txt, font=fnt(24), fill=col)
            draw.text((140+x_off, y+55), cat, font=fnt(16, False), fill=DIM)
            if bt < 0.05: img = apply_shake(img, 10); draw = ImageDraw.Draw(img)
        return img

    def sc_summary(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=1203)
        img = draw_glow(img, W//2, 500, 400, GREEN, 0.05)
        draw = ImageDraw.Draw(img)
        # Daily summary
        img = slam_text(draw, img, t, 350, "Итог дня", fnt(56), WHITE)
        draw = ImageDraw.Draw(img)
        stats = [("5 задач ✓", GREEN), ("₽1 000 расходов", ORANGE), ("₽500 доход", CYAN)]
        for i, (txt, col) in enumerate(stats):
            bt = t - BEAT * (1.5 + i * 0.8)
            if bt > 0:
                p = ease_out_cubic(bt / 0.3)
                draw_centered(draw, 500 + i * 60, txt, fnt(28, False), color_lerp(BG, col, p))
        draw_centered(draw, 780, "Маленькие шаги.", fnt(44),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*4.5)/0.3)))
        draw_centered(draw, 850, "Большие результаты.", fnt(44),
                      color_lerp(BG, GREEN, min(1, max(0, t-BEAT*5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*6)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*7)
        return img

    scenes = [
        (sc_micro,   2.5, "flash"),
        (sc_actions, 4.0, "glitch"),
        (sc_summary, 5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), GREEN, BPM


def scenario_13():
    """Control Without Internet"""
    def sc_airplane(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 10, ORANGE, seed=1301)
        img = draw_glow(img, W//2, H//2, 400, ORANGE, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 550, "✈ Авиарежим", fnt(70), ORANGE)
        draw = ImageDraw.Draw(img)
        typewriter(draw, t, 700, "Нет интернета.", fnt(36, False), DIM, delay=BEAT*2)
        return img

    def sc_working(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=1302)
        img = draw_glow(img, W//2, 500, 350, GREEN, 0.04)
        draw = ImageDraw.Draw(img)
        # Status bar with airplane icon
        draw_rr(draw, (0, 0, W, 60), 0, (15, 15, 30))
        draw.text((W-120, 15), "✈ WiFi ✗", font=fnt(18, False), fill=ORANGE)
        # App still works
        draw_centered(draw, 200, "Приложение работает", fnt(40), GREEN)
        # Adding things
        items = [
            ("✅ Прочитать книгу", GREEN, BEAT*1.5),
            ("💰 – ₽500 такси", ORANGE, BEAT*2.5),
            ("📝 Идея: новый проект", CYAN, BEAT*3.5),
        ]
        for i, (txt, col, delay) in enumerate(items):
            bt = t - delay
            if bt <= 0: continue
            p = ease_out_back(bt / 0.2)
            y = 350 + i * 150
            x_off = int(lerp(-W, 0, p))
            draw_rr(draw, (80+x_off, y, 1000+x_off, y+110), 22, CARD_BG, outline=(*col,40), width=1)
            draw.text((140+x_off, y+30), txt, font=fnt(24), fill=col)
            draw.text((140+x_off, y+70), "Сохранено локально ✓", font=fnt(16, False), fill=GREEN)
            if bt < 0.06: img = apply_shake(img, 8); draw = ImageDraw.Draw(img)
        return img

    def sc_saved(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 25, GREEN, seed=1303)
        img = draw_glow(img, W//2, 500, 400, GREEN, 0.05)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 400, "📱 Всё на устройстве", fnt(48), WHITE)
        draw = ImageDraw.Draw(img)
        facts = [("🔒 Приватно", LILAC), ("📴 Оффлайн", ORANGE), ("⚡ Мгновенно", GREEN)]
        for i, (txt, col) in enumerate(facts):
            bt = t - BEAT * (1.5 + i * 0.8)
            if bt > 0:
                p = ease_out_elastic(bt / 0.3)
                draw_centered(draw, 550 + i * 70, txt, fnt(32), color_lerp(BG, col, p))
        draw_centered(draw, 830, "Твои данные. На твоём устройстве.", fnt(30),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*4.5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*5.5)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*6.5)
        return img

    scenes = [
        (sc_airplane, 2.5, "flash"),
        (sc_working,  4.5, "glitch"),
        (sc_saved,    5.0, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), ORANGE, BPM


def scenario_14():
    """From Chaos to Order"""
    def sc_chaos(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        rng = random.Random(int(t * 10))
        # Random chaotic text flying
        chaos_words = ["₽???", "ДЕЛА", "СЧЕТА", "ЗАМЕТКИ", "СРОКИ!", "БЮДЖЕТ?", "ГДЕ?!", "СКОЛЬКО?"]
        for i in range(15):
            word = chaos_words[rng.randint(0, len(chaos_words) - 1)]
            x = rng.randint(0, W - 200)
            y = rng.randint(0, H - 100)
            sz = rng.randint(20, 60)
            col = [RED, ORANGE, YELLOW, WHITE][rng.randint(0, 3)]
            draw.text((x, y), word, font=fnt(sz), fill=col)
        # Glitch
        if t > 0.3:
            img = apply_glitch(img, int(15 + t * 10))
        draw = ImageDraw.Draw(img)
        draw_centered(draw, H // 2 - 30, "ХАОС", fnt(100), RED)
        return img

    def sc_blur(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Transition: blur circle expanding to reveal clean
        p = ease_out_cubic(t / dur)
        r = int(p * 1500)
        draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], fill=BG)
        if t > dur * 0.5:
            draw_centered(draw, H//2 - 30, "→", fnt(120), PURPLE)
        return img

    def sc_order(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, PURPLE, seed=1403)
        img = draw_glow(img, W//2, 500, 400, PURPLE, 0.05)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 250, "Порядок", fnt(80), WHITE)
        draw = ImageDraw.Draw(img)
        # Structured list
        items = [
            ("✅ Задачи по приоритету", GREEN),
            ("💰 Финансы по категориям", ORANGE),
            ("⏱ Время под контролем", RED),
            ("📝 Заметки организованы", CYAN),
        ]
        for i, (txt, col) in enumerate(items):
            bt = t - BEAT * (1.5 + i * 0.7)
            if bt <= 0: continue
            p = ease_out_cubic(bt / 0.3)
            y = 420 + i * 70
            draw.text((150, y), "●", font=fnt(14), fill=col)
            draw.text((190, y), txt, font=fnt(26, False), fill=color_lerp(BG, WHITE, p))
        # Dashboard card
        bt2 = t - BEAT * 5
        if bt2 > 0:
            p = ease_out_back(bt2 / 0.25)
            y_off = int(lerp(100, 0, p))
            draw_rr(draw, (70, 750+y_off, 1010, 960+y_off), 24, CARD_BG)
            draw.text((110, 780+y_off), "₽42 350", font=fnt(52), fill=GREEN)
            draw.text((110, 860+y_off), "5 задач · 3 заметки · Баланс +12%", font=fnt(18, False), fill=DIM)
        draw_centered(draw, 1020, "Из хаоса — в ясность.", fnt(38),
                      color_lerp(BG, WHITE, min(1, max(0, t-BEAT*6.5)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*7)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "Todo Budget", delay=BEAT*8)
        return img

    scenes = [
        (sc_chaos, 3.0, "glitch"),
        (sc_blur,  1.5, "flash"),
        (sc_order, 6.5, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), PURPLE, BPM


def scenario_15():
    """30-Second Demo"""
    def sc_logo(t, dur):
        img = Image.new("RGB", (W, H), BG)
        pulse = 0.05 + 0.04 * math.sin(t * 5)
        img = draw_glow(img, W//2, H//2, 500, PURPLE, pulse)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 30, PURPLE, seed=1501)
        # Icon
        p0 = ease_out_back(t / 0.3)
        sz = int(160 * p0)
        if sz > 5:
            cx, cy = W//2, 700
            r = sz // 2
            draw_rr(draw, (cx-r, cy-r, cx+r, cy+r), max(5, int(sz*0.28)), PURPLE)
            draw.text((cx - text_w(draw, "✓", fnt(int(sz*0.55)))//2, cy - 40), "✓", font=fnt(int(sz*0.55)), fill=WHITE)
        img = slam_text(draw, img, t, 850, "Todo Budget", fnt(80), WHITE, delay=BEAT)
        draw = ImageDraw.Draw(img)
        return img

    def sc_task(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=1502)
        img = slam_text(draw, img, t, 300, "✅ Задачи", fnt(60), GREEN)
        draw = ImageDraw.Draw(img)
        texts = [("Купить продукты", WHITE, 26, True), ("Высокий · Сегодня 18:00", RED, 16, False)]
        img = slide_card(draw, img, t, 450, texts, GREEN, delay=BEAT)
        draw = ImageDraw.Draw(img)
        return img

    def sc_income(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, GREEN, seed=1503)
        img = slam_text(draw, img, t, 300, "💰 Доход", fnt(60), GREEN)
        draw = ImageDraw.Draw(img)
        texts = [("+ ₽85 000 · Зарплата", GREEN, 28, True)]
        img = slide_card(draw, img, t, 450, texts, GREEN, delay=BEAT, from_right=False)
        draw = ImageDraw.Draw(img)
        return img

    def sc_expense(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, RED, seed=1504)
        img = slam_text(draw, img, t, 300, "💸 Расход", fnt(60), ORANGE)
        draw = ImageDraw.Draw(img)
        texts = [("– ₽8 500 · Еда", RED, 28, True)]
        img = slide_card(draw, img, t, 450, texts, RED, delay=BEAT)
        draw = ImageDraw.Draw(img)
        return img

    def sc_stats_demo(t, dur):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 20, CYAN, seed=1505)
        img = draw_glow(img, W//2, 500, 350, CYAN, 0.04)
        draw = ImageDraw.Draw(img)
        img = slam_text(draw, img, t, 300, "📊 Статистика", fnt(56), WHITE)
        draw = ImageDraw.Draw(img)
        bars = [("Еда", 0, 500, RED, "₽8 500"), ("Транспорт", 0, 300, ORANGE, "₽5 200"),
                ("Развлечения", 0, 200, CYAN, "₽3 100")]
        draw_bar_chart(draw, t, 460, bars, delay=BEAT)
        return img

    def sc_final(t, dur):
        img = Image.new("RGB", (W, H), BG)
        pulse = 0.05 + 0.03 * math.sin(t * 4)
        img = draw_glow(img, W//2, 700, 500, PURPLE, pulse)
        draw = ImageDraw.Draw(img)
        draw_particles(draw, t, 40, PURPLE, seed=1506)
        img = slam_text(draw, img, t, 450, "₽42 350", fnt(100), GREEN)
        draw = ImageDraw.Draw(img)
        draw_centered(draw, 600, "Задачи + Бюджет", fnt(44),
                      color_lerp(BG, WHITE, min(1, max(0, t-0.3)/0.3)))
        draw_centered(draw, 670, "Одно решение.", fnt(44),
                      color_lerp(BG, PURPLE, min(1, max(0, t-BEAT)/0.3)))
        img = cta_block(draw, img, t, delay=BEAT*2.5)
        draw = ImageDraw.Draw(img)
        bottom_text(draw, t, "0 ₽ · Навсегда", delay=BEAT*3.5)
        return img

    scenes = [
        (sc_logo,       3.0, "flash"),
        (sc_task,       2.5, "glitch"),
        (sc_income,     2.5, "flash"),
        (sc_expense,    2.5, "glitch"),
        (sc_stats_demo, 3.0, "flash"),
        (sc_final,      4.5, "flash"),
    ]
    return scenes, sum(d for _,d,_ in scenes), PURPLE, BPM


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_beat(total_dur, bpm=140, accent=PURPLE, out_path=None):
    """Generate a dark electronic beat for the given duration."""
    from pydub import AudioSegment
    sr = 44100
    beat_ms = int(60.0 / bpm * 1000)
    half = beat_ms // 2
    total_ms = int(total_dur * 1000) + 2000

    def make_kick(dur_ms=150, freq=45):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = np.exp(-t * 25)
        freq_sweep = freq * (1 + 6 * np.exp(-t * 35))
        sig = env * np.sin(2 * np.pi * np.cumsum(freq_sweep) / sr)
        sig = np.tanh(sig * 3) * 0.8
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_snare(dur_ms=100):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = np.exp(-t * 30)
        sig = env * (np.random.uniform(-1, 1, len(t)) * 0.7 + np.sin(2 * np.pi * 200 * t) * 0.3)
        sig = np.tanh(sig * 2) * 0.5
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_hh(dur_ms=40):
        n = int(sr * dur_ms / 1000)
        sig = np.random.uniform(-1, 1, n) * np.exp(-np.linspace(0, 15, n)) * 0.2
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_sub(dur_ms=300, freq=35):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        sig = np.exp(-t * 4) * np.sin(2 * np.pi * freq * t) * 0.5
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_impact():
        dur_ms = 500
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        sig = np.exp(-t * 8) * np.sin(2 * np.pi * 30 * t) * 0.8
        sig += np.exp(-t * 20) * np.random.uniform(-1, 1, len(t)) * 0.4
        sig = np.tanh(sig * 2) * 0.9
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_pad(dur_ms=4000, freq=55):
        t = np.linspace(0, dur_ms/1000, int(sr*dur_ms/1000))
        env = (1 - np.exp(-t * 1.5)) * np.exp(-t * 0.15)
        sig = (np.sin(2*np.pi*freq*t) + np.sin(2*np.pi*freq*1.003*t) + np.sin(2*np.pi*freq*0.997*t)) / 3
        sig = env * sig * 0.15
        return AudioSegment((sig * 32767).astype(np.int16).tobytes(), frame_rate=sr, sample_width=2, channels=1)

    kick = make_kick(); snare = make_snare(); hh = make_hh(); sub = make_sub()
    track = AudioSegment.silent(duration=total_ms)
    num_beats = total_ms // beat_ms + 1

    for b in range(num_beats):
        pos = b * beat_ms
        track = track.overlay(kick, position=pos)
        if b % 4 in [1, 3]: track = track.overlay(snare, position=pos)
        track = track.overlay(hh, position=pos)
        track = track.overlay(hh, position=pos + half)
        if b % 2 == 1: track = track.overlay(hh - 6, position=pos + half // 2)
        if b % 4 in [0, 2]: track = track.overlay(sub, position=pos)

    # Pad layer
    pad_layer = AudioSegment.silent(duration=total_ms)
    bar_ms = beat_ms * 4
    pad_notes = [55, 41.2, 55, 73.4]
    for i in range(total_ms // bar_ms + 1):
        pad = make_pad(dur_ms=bar_ms, freq=pad_notes[i % len(pad_notes)])
        pad_layer = pad_layer.overlay(pad, position=i * bar_ms)

    final = track.overlay(pad_layer)
    final = final.fade_in(400).fade_out(1500)[:total_ms]
    final = final.normalize()
    final.export(out_path, format="wav")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME RENDERER + ASSEMBLER
# ═══════════════════════════════════════════════════════════════════════════════

TRANS_DUR = 0.12  # scene transition in seconds

def render_video(index, scenes, total_dur, accent, bpm):
    """Render one video: frames + audio → MP4."""
    vid_name = f"reels_{index:02d}"
    vid_dir = OUT_DIR / vid_name
    frames_dir = vid_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    total_frames = int(total_dur * FPS)
    print(f"  Rendering {total_frames} frames...")

    prev_img = None
    for fi in range(total_frames):
        global_t = fi / FPS
        # Find current scene
        t_acc = 0
        scene_idx = 0
        local_t = 0
        for idx, (renderer, dur, trans) in enumerate(scenes):
            if global_t < t_acc + dur:
                scene_idx = idx
                local_t = global_t - t_acc
                break
            t_acc += dur
        else:
            scene_idx = len(scenes) - 1
            local_t = global_t - t_acc

        renderer, dur, trans = scenes[scene_idx]
        random.seed(42 + fi)  # deterministic per frame
        img = renderer(local_t, dur)

        # Transition
        if local_t < TRANS_DUR and scene_idx > 0 and prev_img is not None:
            p = local_t / TRANS_DUR
            if trans == "glitch":
                img = apply_glitch(img, int(20 * (1 - p)))
                img = Image.blend(prev_img, img, p)
            elif trans == "flash":
                img = Image.blend(prev_img, img, p)
                img = apply_flash(img, 0.5 * (1 - p))
            else:
                img = Image.blend(prev_img, img, p)

        # Global fade in/out
        if global_t < 0.4:
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, global_t / 0.4)
        if global_t > total_dur - 1.2:
            p = (total_dur - global_t) / 1.2
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, max(0, min(1, p)))

        img.save(str(frames_dir / f"f_{fi:05d}.png"), optimize=False)

        if local_t >= dur - 1.0 / FPS:
            prev_img = img.copy()

        if fi % (FPS * 3) == 0:
            print(f"    {fi}/{total_frames} ({100*fi//total_frames}%)")

    print(f"  ✅ {total_frames} frames done")

    # Generate audio
    audio_path = str(vid_dir / "beat.wav")
    print(f"  Generating beat...")
    generate_beat(total_dur, bpm, accent, audio_path)

    # Assemble
    output_path = str(OUT_DIR / f"{vid_name}.mp4")
    print(f"  Assembling with ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_dir}/f_%05d.png",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        sz = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✅ {output_path} ({sz:.1f} MB)")
    else:
        print(f"  ❌ ffmpeg error: {result.stderr[-300:]}")

    # Cleanup frames to save disk space
    shutil.rmtree(frames_dir)
    try: os.remove(audio_path)
    except: pass

    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIOS = [
    ("Morning Control",         scenario_01),
    ("One App Instead of Three", scenario_02),
    ("Fast Add Challenge",       scenario_03),
    ("Visual Money Flow",        scenario_04),
    ("Pomodoro Focus",           scenario_05),
    ("Weekly Overview",          scenario_06),
    ("Minimalist Lifestyle",     scenario_07),
    ("Productivity Loop",        scenario_08),
    ("Monthly Reset",            scenario_09),
    ("Statistics Power",         scenario_10),
    ("Dark Mode Aesthetic",      scenario_11),
    ("Daily Micro Habits",       scenario_12),
    ("Control Without Internet", scenario_13),
    ("From Chaos to Order",      scenario_14),
    ("30-Second Demo",           scenario_15),
]

def main():
    # Allow building a single video: python3 build_15_reels.py 5
    if len(sys.argv) > 1:
        indices = [int(x) for x in sys.argv[1:]]
    else:
        indices = list(range(1, 16))

    print("=" * 60)
    print("🎬 TODO BUDGET — 15 INSTAGRAM REELS")
    print("=" * 60)
    print(f"📐 {W}×{H} @ {FPS}fps · {BPM} BPM")
    print(f"Building videos: {indices}")
    print()

    results = []
    for i in indices:
        name, builder = SCENARIOS[i - 1]
        print(f"{'━' * 55}")
        print(f"📹 [{i:02d}/15] {name}")
        print(f"{'━' * 55}")
        scenes, dur, accent, bpm = builder()
        print(f"  Duration: {dur:.1f}s · {len(scenes)} scenes")
        path = render_video(i, scenes, dur, accent, bpm)
        results.append((i, name, path))
        print()

    print("=" * 60)
    print("✅ ALL DONE!")
    print("=" * 60)
    for i, name, path in results:
        sz = os.path.getsize(path) / (1024 * 1024)
        print(f"  [{i:02d}] {name:30s} → {sz:.1f} MB")
    print()
    print(f"📁 Output: {OUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
