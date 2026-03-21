#!/usr/bin/env python3
"""
🎬 Todo Budget — KILLER Animated Reels
Frame-by-frame animated video with:
  - Typewriter text reveals
  - Elements sliding/scaling in
  - Glitch distortion effects
  - Camera shake on beat drops
  - Flash/bloom transitions
  - Floating particles
  - Heavy electronic beat synced to visuals
  - NO robotic TTS — text-on-screen style like TikTok

python3 build_killer_reels.py
"""

import os, math, random
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# ─── Config ──────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS = 30
BPM = 140  # fast, punchy
BEAT = 60.0 / BPM  # ~0.43s per beat

BASE = Path(__file__).parent
OUT_DIR = BASE / "killer"
OUT_DIR.mkdir(exist_ok=True)
OUTPUT = BASE / "instagram-reels-killer.mp4"

# Fonts
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colors
BG = (6, 6, 18)
WHITE = (255, 255, 255)
PURPLE = (108, 58, 224)
GREEN = (0, 229, 160)
RED = (255, 107, 107)
CYAN = (0, 201, 255)
ORANGE = (255, 179, 71)
DIM = (80, 80, 120)
CARD_BG = (30, 30, 56)

random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def ease_out_cubic(t):
    """Smooth deceleration curve."""
    t = max(0, min(1, t))
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    """Overshoot ease for punchy entrances."""
    t = max(0, min(1, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_elastic(t):
    t = max(0, min(1, t))
    if t == 0 or t == 1:
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def lerp(a, b, t):
    return a + (b - a) * max(0, min(1, t))


def color_lerp(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_text_centered(draw, y, text, fnt, fill=WHITE, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=fnt, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=fnt, fill=fill)


def draw_rounded_rect(draw, rect, radius, fill, outline=None, width=0):
    x1, y1, x2, y2 = rect
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)


def apply_shake(img, intensity):
    """Random camera shake."""
    if intensity <= 0:
        return img
    dx = int(random.gauss(0, intensity))
    dy = int(random.gauss(0, intensity))
    return ImageChops.offset(img, dx, dy)


def apply_glitch(img, intensity):
    """RGB split glitch effect."""
    if intensity <= 0:
        return img
    arr = np.array(img)
    shift = int(intensity)
    if shift < 1:
        return img
    # Shift red channel right, blue channel left
    result = arr.copy()
    result[:, shift:, 0] = arr[:, :-shift, 0]  # Red right
    result[:, :-shift, 2] = arr[:, shift:, 2]  # Blue left
    # Random horizontal slice displacement
    for _ in range(max(1, shift // 2)):
        y = random.randint(0, H - 20)
        h = random.randint(3, 15)
        sx = random.randint(-shift * 3, shift * 3)
        if sx > 0:
            result[y:y+h, sx:, :] = result[y:y+h, :-sx, :]
        elif sx < 0:
            result[y:y+h, :sx, :] = result[y:y+h, -sx:, :]
    return Image.fromarray(result)


def apply_flash(img, intensity):
    """White flash overlay."""
    if intensity <= 0:
        return img
    flash = Image.new("RGB", (W, H), (255, 255, 255))
    return Image.blend(img, flash, min(1.0, intensity))


def draw_particles(draw, t, count=30, color=PURPLE, seed=0):
    """Floating particles."""
    rng = random.Random(seed)
    for i in range(count):
        speed = rng.uniform(0.3, 1.5)
        x = rng.randint(0, W)
        base_y = rng.randint(0, H)
        y = (base_y - t * speed * 200) % H
        size = rng.uniform(1.5, 4)
        alpha = int(rng.uniform(30, 80))
        c = (*color[:3], alpha) if len(color) == 3 else color
        draw.ellipse([x - size, y - size, x + size, y + size], fill=c[:3])


def draw_radial_glow(img, cx, cy, radius, color, intensity=0.15):
    """Soft radial glow."""
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(int(radius), 0, -4):
        alpha = intensity * (r / radius)
        c = tuple(int(ch * alpha) for ch in color)
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    return ImageChops.add(img, glow)


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE RENDERERS — each returns a PIL Image for given time t
# ═══════════════════════════════════════════════════════════════════════════════

def scene_intro(t, dur):
    """Dark intro — text slams in with shake."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 20, PURPLE, seed=1)
    img = draw_radial_glow(img, W//2, H//2, 500, PURPLE, 0.04)
    draw = ImageDraw.Draw(img)

    # "У тебя" fades in
    p1 = ease_out_cubic(t / 0.4)
    if p1 > 0:
        f = font(48, bold=False)
        c = color_lerp(BG, DIM, p1)
        draw_text_centered(draw, 820, "У тебя", f, c, shadow=False)

    # "3 приложения" SLAMS in at beat 1
    beat1 = t - BEAT
    if beat1 > 0:
        p2 = ease_out_back(beat1 / 0.25)
        scale = lerp(2.0, 1.0, p2)
        f = font(int(80 * scale))
        c = color_lerp(BG, WHITE, min(1, beat1 / 0.15))
        draw_text_centered(draw, int(lerp(750, 890, p2)), "3 приложения", f, c)
        if beat1 < 0.1:
            img = apply_shake(img, 15 * (1 - beat1 / 0.1))
            img = apply_flash(img, 0.3 * (1 - beat1 / 0.1))

    # "для продуктивности" slides up
    beat2 = t - BEAT * 2
    if beat2 > 0:
        p3 = ease_out_cubic(beat2 / 0.3)
        y = int(lerp(1050, 990, p3))
        c = color_lerp(BG, DIM, p3)
        draw_text_centered(draw, y, "для продуктивности", font(44, False), c, shadow=False)

    return img


def scene_problem(t, dur):
    """Competitor cards slam in one by one on beats."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 15, RED, seed=2)
    img = draw_radial_glow(img, 300, 500, 300, RED, 0.03)
    draw = ImageDraw.Draw(img)

    competitors = [
        ("Todoist", "₽359/мес", "за приоритеты"),
        ("Money Manager", "₽199 единоразово", "реклама каждые 30 сек"),
        ("Forest", "₽299", "только таймер"),
    ]

    for i, (name, price, desc) in enumerate(competitors):
        entry_t = t - BEAT * i
        if entry_t <= 0:
            continue

        p = ease_out_back(entry_t / 0.2)
        y_base = 380 + i * 230
        x_off = int(lerp(-W, 0, p))  # slide from left

        rect = (80 + x_off, y_base, 1000 + x_off, y_base + 190)
        draw_rounded_rect(draw, rect, 22, CARD_BG, outline=RED, width=2)

        draw.text((160 + x_off, y_base + 30), name, font=font(34), fill=WHITE)
        draw.text((160 + x_off, y_base + 80), price, font=font(28), fill=RED)
        draw.text((160 + x_off, y_base + 120), desc, font=font(18, False), fill=DIM)

        # Shake on entry
        if entry_t < 0.08:
            img = apply_shake(img, 12)

    # Total price appears
    total_t = t - BEAT * 3.5
    if total_t > 0:
        p = ease_out_elastic(total_t / 0.4)
        scale = lerp(1.5, 1.0, ease_out_cubic(total_t / 0.3))
        f = font(int(44 * scale))
        c = color_lerp(BG, RED, min(1, total_t / 0.15))
        draw_text_centered(draw, 1150, "~₽800/мес на подписки", f, c)
        draw_text_centered(draw, 1220, "и данные на чужих серверах", font(26, False), DIM)
        if total_t < 0.06:
            img = apply_flash(img, 0.4)
            img = apply_shake(img, 20)

    return img


def scene_twist(t, dur):
    """Dramatic 'А что если...' with glitch transition."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    img = draw_radial_glow(img, W//2, H//2, 400, PURPLE, 0.06 * min(1, t / 0.5))
    draw = ImageDraw.Draw(img)

    # "А что если..." typewriter
    full_text = "А что если..."
    chars = int(len(full_text) * min(1, t / 0.8))
    text = full_text[:chars]
    if text:
        draw_text_centered(draw, 820, text, font(52, False), DIM, shadow=False)

    # "всё это в одном?" EXPLODES in
    beat1 = t - BEAT * 2.5
    if beat1 > 0:
        p = ease_out_back(beat1 / 0.2)
        scale = lerp(3.0, 1.0, p)
        f = font(int(72 * scale))
        draw_text_centered(draw, int(lerp(800, 950, ease_out_cubic(beat1 / 0.3))),
                           "всё это", f, WHITE)

        p2 = ease_out_back((beat1 - 0.15) / 0.2)
        if beat1 > 0.15:
            f2 = font(int(72 * lerp(2.5, 1.0, p2)))
            draw_text_centered(draw, int(lerp(900, 1060, ease_out_cubic((beat1 - 0.15) / 0.3))),
                               "в ОДНОМ?", f2, PURPLE)

        if beat1 < 0.08:
            img = apply_glitch(img, 25)
            img = apply_flash(img, 0.5)
            img = apply_shake(img, 25)

    return img


def scene_hero(t, dur):
    """Hero reveal — app icon scales up with massive glow."""
    img = Image.new("RGB", (W, H), BG)

    # Multiple glow layers pulsing
    pulse = 0.06 + 0.03 * math.sin(t * 4)
    img = draw_radial_glow(img, W//2, 650, 500, PURPLE, pulse)
    img = draw_radial_glow(img, W//2, 650, 250, PURPLE, pulse * 2)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 40, PURPLE, seed=4)

    # App icon bounces in
    p = ease_out_back(t / 0.3)
    icon_size = int(140 * p)
    if icon_size > 5:
        ix, iy = W // 2, 550
        r = icon_size // 2
        rr = max(5, int(icon_size * 0.28))
        draw_rounded_rect(draw, (ix - r, iy - r, ix + r, iy + r), rr, PURPLE)
        cf = font(int(icon_size * 0.6))
        bbox = draw.textbbox((0, 0), "✓", font=cf)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((ix - tw // 2, iy - th // 2 - 10), "✓", font=cf, fill=WHITE)

    # "Todo Budget" text
    beat1 = t - BEAT * 1.5
    if beat1 > 0:
        p2 = ease_out_back(beat1 / 0.25)
        f = font(int(lerp(120, 82, p2)))
        draw_text_centered(draw, int(lerp(600, 710, ease_out_cubic(beat1 / 0.3))),
                           "Todo Budget", f, WHITE)
        if beat1 < 0.06:
            img = apply_flash(img, 0.6)
            img = apply_shake(img, 18)

    # Subtitle slides up
    beat2 = t - BEAT * 3
    if beat2 > 0:
        p3 = ease_out_cubic(beat2 / 0.3)
        draw_text_centered(draw, int(lerp(870, 830, p3)),
                           "Задачи · Бюджет · Помодоро · Заметки",
                           font(30, False), color_lerp(BG, DIM, p3), shadow=False)

    # "0 ₽" badge
    beat3 = t - BEAT * 4.5
    if beat3 > 0:
        p4 = ease_out_elastic(beat3 / 0.3)
        scale = lerp(2.0, 1.0, ease_out_cubic(beat3 / 0.25))
        f = font(int(62 * scale))
        draw_text_centered(draw, int(lerp(890, 950, p4)), "0 ₽", f, GREEN)
        draw_text_centered(draw, 1035, "Навсегда бесплатно",
                           font(28, False), color_lerp(BG, DIM, min(1, beat3 / 0.3)), shadow=False)
        if beat3 < 0.05:
            img = apply_shake(img, 15)

    return img


def scene_tasks(t, dur):
    """Task list with cards flying in from alternating sides."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 20, PURPLE, seed=5)
    img = draw_radial_glow(img, 200, 300, 300, PURPLE, 0.03)
    draw = ImageDraw.Draw(img)

    # Title slams in
    p0 = ease_out_back(t / 0.2)
    draw_text_centered(draw, int(lerp(-80, 200, p0)), "✅ Умные задачи",
                       font(int(56 * lerp(1.5, 1.0, p0))), WHITE)
    if t < 0.06:
        img = apply_shake(img, 12)
        draw = ImageDraw.Draw(img)

    tasks = [
        ("Купить продукты", "Сегодня, 18:00", RED, "Высокий"),
        ("Оплатить интернет", "Выполнено", GREEN, "✓"),
        ("Подготовить отчёт", "Завтра, 10:00", ORANGE, "Средний"),
        ("Прочитать книгу", "Пт, 21:00 · 2 подзадачи", CYAN, "Низкий"),
    ]

    for i, (title, sub, color, prio) in enumerate(tasks):
        entry_t = t - BEAT * (1 + i * 0.75)
        if entry_t <= 0:
            continue

        p = ease_out_back(entry_t / 0.2)
        y = 350 + i * 155
        # Alternate entry direction
        if i % 2 == 0:
            x_off = int(lerp(W + 100, 0, p))
        else:
            x_off = int(lerp(-W - 100, 0, p))

        rect = (70 + x_off, y, 1010 + x_off, y + 130)
        draw_rounded_rect(draw, rect, 20, CARD_BG, outline=(*color, 60), width=2)

        # Priority circle
        cx, cy = 120 + x_off, y + 65
        if prio == "✓":
            draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(*GREEN, 60))
            draw.text((cx - 8, cy - 12), "✓", font=font(20), fill=GREEN)
        else:
            draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=color, width=3)

        draw.text((160 + x_off, y + 30), title, font=font(24), fill=WHITE if prio != "✓" else DIM)
        draw.text((160 + x_off, y + 70), sub, font=font(16, False), fill=DIM)

        # Priority bar
        draw.rounded_rectangle([880 + x_off, y + 48, 960 + x_off, y + 58], radius=5, fill=color)

        if entry_t < 0.06:
            img = apply_shake(img, 8)
            draw = ImageDraw.Draw(img)

    # Feature pills at bottom
    pills_t = t - BEAT * 5
    if pills_t > 0:
        pills = ["Приоритеты", "Подзадачи", "Свайпы", "Напоминания"]
        total_w = 0
        pill_widths = []
        for pill in pills:
            bbox = draw.textbbox((0, 0), pill, font=font(16))
            pw = bbox[2] - bbox[0] + 36
            pill_widths.append(pw)
            total_w += pw + 12
        start_x = (W - total_w) // 2
        for j, (pill, pw) in enumerate(zip(pills, pill_widths)):
            pp = ease_out_cubic((pills_t - j * 0.05) / 0.2)
            if pp <= 0:
                continue
            alpha = int(pp * 255)
            y_pill = 1040
            draw_rounded_rect(draw, (start_x, y_pill, start_x + pw, y_pill + 42), 21,
                              (*PURPLE, 40), outline=(*PURPLE, alpha // 3), width=1)
            bbox = draw.textbbox((0, 0), pill, font=font(16))
            tw2 = bbox[2] - bbox[0]
            draw.text((start_x + (pw - tw2) // 2, y_pill + 10), pill,
                      font=font(16), fill=color_lerp(BG, (184, 160, 255), pp))
            start_x += pw + 12

    return img


def scene_budget(t, dur):
    """Budget screen with animated chart bars growing."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 20, GREEN, seed=6)
    img = draw_radial_glow(img, 800, 400, 300, GREEN, 0.03)
    draw = ImageDraw.Draw(img)

    # Title
    p0 = ease_out_back(t / 0.2)
    draw_text_centered(draw, int(lerp(-80, 200, p0)), "💰 Учёт финансов",
                       font(int(56 * lerp(1.5, 1.0, p0))), WHITE)
    if t < 0.06:
        img = apply_shake(img, 12)
        draw = ImageDraw.Draw(img)

    # Balance card
    bal_t = t - BEAT * 1.5
    if bal_t > 0:
        p1 = ease_out_back(bal_t / 0.25)
        y_off = int(lerp(200, 0, p1))
        rect = (70, 360 + y_off, 1010, 560 + y_off)
        draw_rounded_rect(draw, rect, 24, CARD_BG, outline=(*GREEN, 50), width=2)
        draw.text((110, 390 + y_off), "Текущий баланс", font=font(20, False), fill=DIM)

        # Animated counter
        target = 42350
        current = int(target * min(1, (bal_t - 0.2) / 0.5))
        if current > 0:
            draw.text((110, 440 + y_off), f"₽{current:,}".replace(",", " "),
                      font=font(58), fill=GREEN)
        draw.text((480, 460 + y_off), "↑ +12%", font=font(22), fill=GREEN)

        if bal_t < 0.06:
            img = apply_flash(img, 0.3)
            draw = ImageDraw.Draw(img)

    # Chart bars growing
    chart_t = t - BEAT * 3
    if chart_t > 0:
        rect = (70, 600, 1010, 920)
        draw_rounded_rect(draw, rect, 24, CARD_BG)
        draw.text((110, 625), "Расходы по категориям", font=font(18, False), fill=DIM)

        categories = [
            ("Еда", 500, RED, "₽8 500"),
            ("Транспорт", 350, ORANGE, "₽5 200"),
            ("Развлечения", 250, CYAN, "₽4 100"),
            ("Прочее", 180, (184, 160, 255), "₽2 850"),
        ]

        for j, (cat, bar_w, color, amount) in enumerate(categories):
            bt = chart_t - j * BEAT * 0.4
            if bt <= 0:
                continue
            p = ease_out_cubic(bt / 0.4)
            y = 670 + j * 55
            actual_w = int(bar_w * p)
            draw.rounded_rectangle([110, y, 110 + actual_w, y + 30], radius=8, fill=color)
            if p > 0.5:
                draw.text((120 + bar_w + 15, y + 3), f"{cat} — {amount}",
                          font=font(15, False), fill=DIM)

    # Health bar
    health_t = t - BEAT * 5.5
    if health_t > 0:
        p = ease_out_cubic(health_t / 0.4)
        rect = (70, 960, 1010, 1080)
        draw_rounded_rect(draw, rect, 24, (10, 42, 26), outline=(*GREEN, 40), width=1)
        draw.text((110, 985), "Здоровье бюджета", font=font(18, False), fill=DIM)
        bar_w = int(600 * p)
        draw.rounded_rectangle([110, 1020, 110 + bar_w, 1042], radius=9, fill=GREEN)
        draw.rounded_rectangle([110, 1020, 710, 1042], radius=9, outline=(*GREEN, 30), width=1)
        if p > 0.8:
            draw.text((740, 1018), "78% ✓", font=font(20), fill=GREEN)

    return img


def scene_pomodoro(t, dur):
    """Pomodoro timer with animated circular progress."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 20, RED, seed=7)

    # Title
    p0 = ease_out_back(t / 0.2)
    draw_text_centered(draw, int(lerp(-80, 200, p0)), "⏱ Помодоро",
                       font(int(56 * lerp(1.5, 1.0, p0))), WHITE)
    if t < 0.06:
        img = apply_shake(img, 12)
        draw = ImageDraw.Draw(img)

    # Animated circular timer
    timer_t = t - BEAT * 1.5
    if timer_t > 0:
        cx, cy = W // 2, 650
        radius = 180

        # Background circle
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     outline=(*RED, 30), width=6)

        # Animated arc
        progress = ease_out_cubic(timer_t / 1.5) * 0.75  # 75% filled
        start_angle = -90
        end_angle = start_angle + 360 * progress
        draw.arc([cx - radius, cy - radius, cx + radius, cy + radius],
                 start_angle, end_angle, fill=RED, width=8)

        # Time display - counting down
        total_secs = int(25 * 60 * (1 - progress))
        mins = total_secs // 60
        secs = total_secs % 60
        time_str = f"{mins:02d}:{secs:02d}"
        draw.text((cx - 100, cy - 45), time_str, font=font(72), fill=WHITE)
        draw_text_centered(draw, cy + 40, "Фокусировка", font(22, False), (255, 138, 138))

    # Notes section
    notes_t = t - BEAT * 5
    if notes_t > 0:
        # Divider
        p_div = ease_out_cubic(notes_t / 0.3)
        div_w = int(800 * p_div)
        draw.rectangle([W // 2 - div_w // 2, 920, W // 2 + div_w // 2, 922], fill=(*DIM, 50))

        draw_text_centered(draw, 960, "📝 + Заметки", font(44), WHITE)

        # Animated note card
        note_t = notes_t - BEAT
        if note_t > 0:
            p = ease_out_back(note_t / 0.2)
            x_off = int(lerp(W, 0, p))
            rect = (80 + x_off, 1060, 1000 + x_off, 1180)
            draw_rounded_rect(draw, rect, 20, CARD_BG, outline=(*CYAN, 40), width=1)
            draw.text((130 + x_off, 1090), "Идея для проекта: API для...", font=font(22, False), fill=WHITE)
            draw.text((130 + x_off, 1125), "Сегодня, 14:32", font=font(14, False), fill=DIM)
            draw.text((920 + x_off, 1095), "🎤", font=font(28), fill=CYAN)

        draw_text_centered(draw, 1240, "Текст + Голосовой ввод", font(22, False),
                           color_lerp(BG, CYAN, min(1, max(0, notes_t - BEAT) / 0.3)))

    return img


def scene_stats(t, dur):
    """Key stats — numbers count up, slam effects."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 30, GREEN, seed=8)

    # "Почему?" fades in
    p0 = ease_out_cubic(t / 0.3)
    draw_text_centered(draw, int(lerp(200, 250, p0)), "Почему Todo Budget?",
                       font(44, False), color_lerp(BG, DIM, p0), shadow=False)

    # 9 MB — huge, slams in
    stat1_t = t - BEAT
    if stat1_t > 0:
        p = ease_out_back(stat1_t / 0.2)
        scale = max(1.0, lerp(3.0, 1.0, p))
        f = font(min(180, int(120 * scale)))
        draw_text_centered(draw, int(lerp(250, 420, ease_out_cubic(stat1_t / 0.25))),
                           "9 МБ", f, GREEN)
        draw_text_centered(draw, 570, "Легче одной фотки", font(26, False),
                           color_lerp(BG, DIM, min(1, stat1_t / 0.3)), shadow=False)
        if stat1_t < 0.06:
            img = apply_shake(img, 20)
            img = apply_flash(img, 0.4)
            draw = ImageDraw.Draw(img)

    # 0 ₽
    stat2_t = t - BEAT * 3
    if stat2_t > 0:
        p = ease_out_back(stat2_t / 0.2)
        scale = max(1.0, lerp(3.0, 1.0, p))
        f = font(min(180, int(120 * scale)))
        draw_text_centered(draw, int(lerp(500, 680, ease_out_cubic(stat2_t / 0.25))),
                           "0 ₽", f, RED)
        draw_text_centered(draw, 830, "Без подписок. Навсегда.", font(26, False),
                           color_lerp(BG, DIM, min(1, stat2_t / 0.3)), shadow=False)
        if stat2_t < 0.06:
            img = apply_shake(img, 20)
            img = apply_flash(img, 0.4)
            draw = ImageDraw.Draw(img)

    # Stat blocks
    blocks = [
        ("📴", "Оффлайн", CYAN),
        ("🔒", "Приватно", (184, 160, 255)),
        ("🌙", "Тёмная тема", ORANGE),
        ("📦", "CSV экспорт", GREEN),
    ]

    for i, (emoji, label, color) in enumerate(blocks):
        bt = t - BEAT * 5 - i * BEAT * 0.5
        if bt <= 0:
            continue
        p = ease_out_back(bt / 0.2)
        col = i % 2
        row = i // 2
        x = 80 + col * 500
        y = 920 + row * 170
        y_off = int(lerp(80, 0, p))
        rect = (x, y + y_off, x + 440, y + 140 + y_off)
        draw_rounded_rect(draw, rect, 22, CARD_BG, outline=(*color, 40), width=1)
        draw.text((x + 180, y + 30 + y_off), emoji, font=font(40), fill=WHITE)
        bbox = draw.textbbox((0, 0), label, font=font(22))
        tw = bbox[2] - bbox[0]
        draw.text((x + 220 - tw // 2, y + 85 + y_off), label, font=font(22), fill=color)

    return img


def scene_cta(t, dur):
    """Final CTA — everything builds to download button."""
    img = Image.new("RGB", (W, H), BG)

    # Pulsing glow
    pulse = 0.05 + 0.04 * math.sin(t * 5)
    img = draw_radial_glow(img, W // 2, 960, 600, PURPLE, pulse)
    img = draw_radial_glow(img, W // 2, 960, 350, PURPLE, pulse * 1.5)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, t, 50, PURPLE, seed=9)
    draw_particles(draw, t * 1.3, 30, GREEN, seed=10)

    # Feature emojis floating
    emojis = [("✅", 200, 380), ("💰", 850, 420), ("⏱", 220, 1520), ("📝", 880, 1560)]
    for em, ex, ey in emojis:
        bob = 15 * math.sin(t * 2 + ex * 0.01)
        draw.text((ex, ey + bob), em, font=font(50), fill=DIM)

    # "Todo Budget" — BIG reveal
    p0 = ease_out_back(t / 0.3)
    scale = lerp(2.5, 1.0, p0)
    f = font(int(85 * scale))
    draw_text_centered(draw, int(lerp(500, 650, ease_out_cubic(t / 0.3))),
                       "Todo Budget", f, WHITE)
    if t < 0.06:
        img = apply_flash(img, 0.8)
        img = apply_glitch(img, 30)
        img = apply_shake(img, 25)
        draw = ImageDraw.Draw(img)

    # Subtitle
    sub_t = t - BEAT * 1.5
    if sub_t > 0:
        draw_text_centered(draw, 780, "4 в 1 · 9 МБ · Бесплатно",
                           font(32, False), color_lerp(BG, DIM, min(1, sub_t / 0.3)), shadow=False)

    # FREE badge pulses
    badge_t = t - BEAT * 2.5
    if badge_t > 0:
        p = ease_out_elastic(badge_t / 0.4)
        pulse2 = 1 + 0.05 * math.sin(badge_t * 6)
        f = font(int(52 * p * pulse2))
        draw_text_centered(draw, 870, "БЕСПЛАТНО", f, GREEN)

    # CTA Button
    btn_t = t - BEAT * 4
    if btn_t > 0:
        p = ease_out_back(btn_t / 0.25)
        y = int(lerp(1200, 1060, p))
        bw, bh = 520, 90
        rect = (W // 2 - bw // 2, y, W // 2 + bw // 2, y + bh)
        draw_rounded_rect(draw, rect, bh // 2, PURPLE)
        draw_text_centered(draw, y + 20, "📲 Скачать в RuStore", font(32), WHITE, shadow=False)
        if btn_t < 0.06:
            img = apply_shake(img, 12)
            draw = ImageDraw.Draw(img)

    # Website
    web_t = t - BEAT * 5.5
    if web_t > 0:
        p = ease_out_cubic(web_t / 0.3)
        y = 1220
        draw_text_centered(draw, y, "emil-a-dev.github.io/todofin",
                           font(24, False), color_lerp(BG, CYAN, p), shadow=False)

    # Bottom hint pulsing
    link_t = t - BEAT * 7
    if link_t > 0:
        alpha = 0.5 + 0.5 * math.sin(link_t * 3)
        draw_text_centered(draw, 1400, "Ссылка в описании ↓",
                           font(24, False), color_lerp(BG, DIM, alpha), shadow=False)

    return img


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE TIMELINE
# ═══════════════════════════════════════════════════════════════════════════════

# (renderer, duration, transition_type)
TIMELINE = [
    (scene_intro,    2.5,  "glitch"),   # 0.0 - 2.5
    (scene_problem,  3.5,  "glitch"),   # 2.5 - 6.0
    (scene_twist,    2.0,  "flash"),    # 6.0 - 8.0
    (scene_hero,     3.5,  "flash"),    # 8.0 - 11.5
    (scene_tasks,    3.5,  "glitch"),   # 11.5 - 15.0
    (scene_budget,   3.5,  "glitch"),   # 15.0 - 18.5
    (scene_pomodoro, 3.5,  "flash"),    # 18.5 - 22.0
    (scene_stats,    3.5,  "flash"),    # 22.0 - 25.5
    (scene_cta,      4.5,  "none"),     # 25.5 - 30.0
]

TOTAL_DUR = sum(d for _, d, _ in TIMELINE)
TRANS_DUR = 0.15  # transition duration in seconds


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATION — Heavy electronic
# ═══════════════════════════════════════════════════════════════════════════════

def generate_heavy_beat():
    """Generate a heavy, dark, punchy beat."""
    from pydub import AudioSegment

    sr = 44100
    total_ms = int(TOTAL_DUR * 1000) + 3000
    beat_ms = int(BEAT * 1000)
    half = beat_ms // 2

    def make_kick(dur_ms=150, freq=45):
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = np.exp(-t * 25)
        freq_sweep = freq * (1 + 6 * np.exp(-t * 35))
        sig = env * np.sin(2 * np.pi * np.cumsum(freq_sweep) / sr)
        # Add punch with distortion
        sig = np.tanh(sig * 3) * 0.8
        return AudioSegment(
            (sig * 32767).astype(np.int16).tobytes(),
            frame_rate=sr, sample_width=2, channels=1
        )

    def make_snare(dur_ms=100):
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = np.exp(-t * 30)
        noise = np.random.uniform(-1, 1, len(t))
        tone = np.sin(2 * np.pi * 200 * t)
        sig = env * (noise * 0.7 + tone * 0.3)
        sig = np.tanh(sig * 2) * 0.5
        return AudioSegment(
            (sig * 32767).astype(np.int16).tobytes(),
            frame_rate=sr, sample_width=2, channels=1
        )

    def make_hihat(dur_ms=40):
        samples = int(sr * dur_ms / 1000)
        noise = np.random.uniform(-1, 1, samples)
        env = np.exp(-np.linspace(0, 15, samples))
        sig = (noise * env * 0.2 * 32767).astype(np.int16)
        return AudioSegment(sig.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_sub(dur_ms=300, freq=35):
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = np.exp(-t * 4)
        sig = env * np.sin(2 * np.pi * freq * t)
        sig = (sig * 32767 * 0.5).astype(np.int16)
        return AudioSegment(sig.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    def make_riser(dur_ms=2000):
        """Tension-building riser sound."""
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = t / t[-1]  # linear rise
        freq = 200 + 2000 * (t / t[-1]) ** 2
        sig = env * np.sin(2 * np.pi * np.cumsum(freq) / sr)
        noise = np.random.uniform(-1, 1, len(t)) * env * 0.15
        sig = (sig + noise) * 0.3
        return AudioSegment(
            (sig * 32767).astype(np.int16).tobytes(),
            frame_rate=sr, sample_width=2, channels=1
        )

    def make_impact():
        """Big cinematic impact sound."""
        dur_ms = 500
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = np.exp(-t * 8)
        # Low frequencies
        sig = env * np.sin(2 * np.pi * 30 * t) * 0.8
        # Noise burst
        noise_env = np.exp(-t * 20)
        sig += noise_env * np.random.uniform(-1, 1, len(t)) * 0.4
        sig = np.tanh(sig * 2) * 0.9
        return AudioSegment(
            (sig * 32767).astype(np.int16).tobytes(),
            frame_rate=sr, sample_width=2, channels=1
        )

    # Atmospheric pad
    def make_dark_pad(dur_ms=4000, freq=55):
        t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000))
        env = (1 - np.exp(-t * 1.5)) * np.exp(-t * 0.15)
        s1 = np.sin(2 * np.pi * freq * t)
        s2 = np.sin(2 * np.pi * freq * 1.003 * t)
        s3 = np.sin(2 * np.pi * freq * 0.997 * t)
        s4 = np.sin(2 * np.pi * freq * 1.5 * t) * 0.2  # fifth
        sig = env * (s1 + s2 + s3 + s4) / 3.5 * 0.15
        return AudioSegment(
            (sig * 32767).astype(np.int16).tobytes(),
            frame_rate=sr, sample_width=2, channels=1
        )

    kick = make_kick()
    snare = make_snare()
    hh = make_hihat()
    sub = make_sub()

    # Build beat pattern
    track = AudioSegment.silent(duration=total_ms)

    num_beats = total_ms // beat_ms + 1

    for b in range(num_beats):
        pos = b * beat_ms

        # Kick on every beat
        track = track.overlay(kick, position=pos)

        # Snare on beats 2 and 4
        if b % 4 in [1, 3]:
            track = track.overlay(snare, position=pos)

        # Hi-hats on every 8th note
        track = track.overlay(hh, position=pos)
        track = track.overlay(hh, position=pos + half)

        # Extra hi-hat ghost notes for groove
        if b % 2 == 1:
            track = track.overlay(hh - 6, position=pos + half // 2)

        # Sub bass on beats 1 and 3
        if b % 4 in [0, 2]:
            track = track.overlay(sub, position=pos)

    # Add dark pad layer
    pad_layer = AudioSegment.silent(duration=total_ms)
    pad_notes = [55, 41.2, 55, 73.4]  # Am pentatonic roots
    bar_ms = beat_ms * 4
    for i in range(total_ms // bar_ms + 1):
        note = pad_notes[i % len(pad_notes)]
        pad = make_dark_pad(dur_ms=bar_ms, freq=note)
        pad_layer = pad_layer.overlay(pad, position=i * bar_ms)

    # Add impacts at scene transitions
    impact = make_impact()
    scene_times = []
    t_acc = 0
    for _, dur, _ in TIMELINE:
        scene_times.append(t_acc)
        t_acc += dur

    for st in scene_times[1:]:  # skip first
        pos_ms = int(st * 1000)
        track = track.overlay(impact, position=max(0, pos_ms - 50))

    # Add riser before twist scene (scene 2 → 3)
    riser = make_riser(dur_ms=1500)
    twist_time = sum(d for _, d, _ in TIMELINE[:2])
    track = track.overlay(riser - 3, position=max(0, int((twist_time - 1.5) * 1000)))

    # Add riser before CTA
    cta_time = sum(d for _, d, _ in TIMELINE[:8])
    track = track.overlay(riser - 3, position=max(0, int((cta_time - 1.5) * 1000)))

    # Mix
    final = track.overlay(pad_layer)
    final = final.fade_in(500).fade_out(2000)
    final = final[:total_ms]

    # Normalize
    final = final.normalize()

    path = str(OUT_DIR / "beat.wav")
    final.export(path, format="wav")
    print(f"  Beat: {len(final)/1000:.1f}s → {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER ALL FRAMES + ASSEMBLE
# ═══════════════════════════════════════════════════════════════════════════════

def render_all_frames():
    """Render every frame (1080x1920 @ 30fps)."""
    total_frames = int(TOTAL_DUR * FPS)
    frames_path = OUT_DIR / "frames"
    frames_path.mkdir(exist_ok=True)

    print(f"  Rendering {total_frames} frames ({TOTAL_DUR:.1f}s × {FPS}fps)...")

    frame_files = []
    prev_img = None

    for frame_idx in range(total_frames):
        global_t = frame_idx / FPS

        # Find current scene
        t_acc = 0
        scene_idx = 0
        for idx, (renderer, dur, trans) in enumerate(TIMELINE):
            if global_t < t_acc + dur:
                scene_idx = idx
                local_t = global_t - t_acc
                break
            t_acc += dur
        else:
            scene_idx = len(TIMELINE) - 1
            local_t = global_t - t_acc

        renderer, dur, trans = TIMELINE[scene_idx]
        img = renderer(local_t, dur)

        # Transition IN effect at start of scene
        if local_t < TRANS_DUR and scene_idx > 0 and prev_img is not None:
            p = local_t / TRANS_DUR
            if trans == "glitch":
                img = apply_glitch(img, int(20 * (1 - p)))
                img = Image.blend(prev_img, img, p)
            elif trans == "flash":
                img = Image.blend(prev_img, img, p)
                img = apply_flash(img, 0.6 * (1 - p))
            else:
                img = Image.blend(prev_img, img, p)

        # Fade out at the very end
        if global_t > TOTAL_DUR - 1.5:
            fade_p = (TOTAL_DUR - global_t) / 1.5
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, max(0, min(1, fade_p)))

        # Fade in at the very start
        if global_t < 0.5:
            fade_p = global_t / 0.5
            black = Image.new("RGB", (W, H), (0, 0, 0))
            img = Image.blend(black, img, fade_p)

        # Save
        path = frames_path / f"frame_{frame_idx:05d}.png"
        img.save(str(path), optimize=False)
        frame_files.append(str(path))

        # Keep last frame for transitions
        if local_t >= dur - 1.0 / FPS:
            prev_img = img.copy()

        # Progress
        if frame_idx % (FPS * 2) == 0:
            print(f"    {frame_idx}/{total_frames} ({100*frame_idx/total_frames:.0f}%)")

    print(f"  ✅ {total_frames} frames rendered")
    return frame_files, str(frames_path)


def assemble_with_ffmpeg(frames_dir, audio_path):
    """Use ffmpeg to assemble frames + audio into MP4."""
    import subprocess

    print(f"  Assembling video with ffmpeg...")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_dir}/frame_%05d.png",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
        print(f"  ✅ Video: {OUTPUT} ({size_mb:.1f} MB)")
    else:
        print(f"  ❌ ffmpeg error: {result.stderr[-500:]}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🎬 TODO BUDGET — KILLER REELS")
    print("=" * 60)
    print(f"📐 {W}×{H} @ {FPS}fps")
    print(f"🎵 {BPM} BPM dark electronic beat")
    print(f"⏱  {TOTAL_DUR:.1f}s ({len(TIMELINE)} scenes)")
    print(f"🎞  ~{int(TOTAL_DUR * FPS)} frames to render")
    print()

    print("━" * 40)
    print("1️⃣  Generating beat")
    print("━" * 40)
    audio_path = generate_heavy_beat()
    print()

    print("━" * 40)
    print("2️⃣  Rendering frames (this takes a while)")
    print("━" * 40)
    _, frames_dir = render_all_frames()
    print()

    print("━" * 40)
    print("3️⃣  Assembling final video")
    print("━" * 40)
    assemble_with_ffmpeg(frames_dir, audio_path)
    print()

    print("=" * 60)
    print("✅ DONE!")
    print(f"📁 {OUTPUT}")
    print()
    t = 0
    for i, (_, dur, trans) in enumerate(TIMELINE):
        names = ["intro", "problem", "twist", "hero", "tasks",
                 "budget", "pomodoro", "stats", "cta"]
        print(f"  {t:5.1f}s → {t+dur:5.1f}s  [{names[i]}] ({trans})")
        t += dur
    print()
    print("🎬 Effects: glitch, shake, flash, slide-in, scale, typewriter,")
    print("   elastic bounce, floating particles, radial glow, beat-sync")
    print("🎵 Audio: 140 BPM kick/snare/hat + sub bass + dark pad + risers + impacts")
    print("=" * 60)


if __name__ == "__main__":
    main()
