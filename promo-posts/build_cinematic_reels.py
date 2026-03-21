#!/usr/bin/env python3
"""
🎬 Todo Budget — Cinematic Instagram Reels Builder
Создаёт кинематографичный ролик с:
  - 9 динамических сцен
  - Zoom/pan анимации
  - Плавные crossfade/fade переходы
  - Синтетический drum & bass бит
  - Озвучка через Google TTS
  - Кинематографичные титры

Запуск: python3 build_cinematic_reels.py
"""

import os
import sys
import numpy as np
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
WORK = BASE / "cinematic"
WORK.mkdir(exist_ok=True)
FRAMES_DIR = WORK / "frames"
FRAMES_DIR.mkdir(exist_ok=True)
AUDIO_DIR = WORK / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

OUTPUT = BASE / "instagram-reels-cinematic.mp4"

W, H = 1080, 1920
FPS = 30


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Generate SVG frames (9 scenes)
# ═══════════════════════════════════════════════════════════════════════════════

SCENES = []

def add_scene(name, duration, svg, voiceover_text):
    SCENES.append({
        "name": name,
        "duration": duration,
        "svg": svg,
        "voiceover": voiceover_text,
    })

# ── Scene 1: Dramatic Intro (dark, one line appears) ────────────────────────
add_scene("intro", 2.5, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#050510"/>
      <stop offset="100%" style="stop-color:#0a0a1f"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="540" cy="960" r="600" fill="#6C3AE0" opacity="0.03"/>
  <circle cx="540" cy="960" r="400" fill="#6C3AE0" opacity="0.04"/>
  <text x="540" y="900" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" fill="#555577">У тебя есть</text>
  <text x="540" y="1020" text-anchor="middle" font-family="system-ui, sans-serif" font-size="88" font-weight="bold" fill="#fff" filter="url(#glow)">3 приложения</text>
  <text x="540" y="1120" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" fill="#555577">для продуктивности</text>
</svg>''', "У тебя три приложения для продуктивности.")

# ── Scene 2: The Problem (red accent) ───────────────────────────────────────
add_scene("problem", 3.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0510"/>
      <stop offset="100%" style="stop-color:#1a0a1f"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="300" cy="600" r="200" fill="#FF6B6B" opacity="0.04"/>
  <circle cx="800" cy="1400" r="250" fill="#FF6B6B" opacity="0.03"/>

  <g transform="translate(100, 450)">
    <rect width="880" height="180" rx="24" fill="#1a1020" stroke="#FF6B6B" stroke-width="2" stroke-opacity="0.3"/>
    <text x="60" y="70" font-size="50">📋</text>
    <text x="140" y="70" font-family="system-ui, sans-serif" font-size="36" fill="#ccc">Todoist</text>
    <text x="140" y="120" font-family="system-ui, sans-serif" font-size="28" fill="#FF6B6B" font-weight="bold">₽359/мес</text>
    <text x="140" y="155" font-family="system-ui, sans-serif" font-size="20" fill="#666">за приоритеты и фильтры</text>
  </g>

  <g transform="translate(100, 680)">
    <rect width="880" height="180" rx="24" fill="#1a1020" stroke="#FF6B6B" stroke-width="2" stroke-opacity="0.3"/>
    <text x="60" y="70" font-size="50">💰</text>
    <text x="140" y="70" font-family="system-ui, sans-serif" font-size="36" fill="#ccc">Money Manager</text>
    <text x="140" y="120" font-family="system-ui, sans-serif" font-size="28" fill="#FF6B6B" font-weight="bold">₽199 за отключение рекламы</text>
    <text x="140" y="155" font-family="system-ui, sans-serif" font-size="20" fill="#666">полноэкранные ролики каждые 30 сек</text>
  </g>

  <g transform="translate(100, 910)">
    <rect width="880" height="180" rx="24" fill="#1a1020" stroke="#FF6B6B" stroke-width="2" stroke-opacity="0.3"/>
    <text x="60" y="70" font-size="50">🌳</text>
    <text x="140" y="70" font-family="system-ui, sans-serif" font-size="36" fill="#ccc">Forest</text>
    <text x="140" y="120" font-family="system-ui, sans-serif" font-size="28" fill="#FF6B6B" font-weight="bold">₽299 единоразово</text>
    <text x="140" y="155" font-family="system-ui, sans-serif" font-size="20" fill="#666">только таймер, больше ничего</text>
  </g>

  <g transform="translate(540, 1250)">
    <text x="0" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="44" fill="#FF6B6B" font-weight="bold" filter="url(#glow)">~₽800/мес на подписки</text>
    <text x="0" y="60" text-anchor="middle" font-family="system-ui, sans-serif" font-size="30" fill="#666">и данные на чужих серверах</text>
  </g>
</svg>''', "Todoist, Money Manager, Forest. Восемьсот рублей в месяц на подписки. И данные на чужих серверах.")

# ── Scene 3: Plot twist ─────────────────────────────────────────────────────
add_scene("twist", 2.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#050510"/>
      <stop offset="100%" style="stop-color:#0a0a1f"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="15" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="540" cy="960" r="300" fill="#6C3AE0" opacity="0.06"/>

  <text x="540" y="880" text-anchor="middle" font-family="system-ui, sans-serif" font-size="48" fill="#666688">А что, если...</text>
  <text x="540" y="1020" text-anchor="middle" font-family="system-ui, sans-serif" font-size="80" font-weight="bold" fill="#fff" filter="url(#glow)">всё это</text>
  <text x="540" y="1130" text-anchor="middle" font-family="system-ui, sans-serif" font-size="80" font-weight="bold" fill="#6C3AE0" filter="url(#glow)">в одном?</text>
</svg>''', "А что если всё это, в одном приложении?")

# ── Scene 4: Hero reveal ────────────────────────────────────────────────────
add_scene("hero", 3.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0a1a"/>
      <stop offset="100%" style="stop-color:#161630"/>
    </linearGradient>
    <linearGradient id="purple" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6C3AE0"/>
      <stop offset="100%" style="stop-color:#9B6BFF"/>
    </linearGradient>
    <filter id="bigGlow"><feGaussianBlur stdDeviation="20" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glow"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>

  <!-- Dramatic radial glow -->
  <circle cx="540" cy="700" r="500" fill="#6C3AE0" opacity="0.06"/>
  <circle cx="540" cy="700" r="300" fill="#6C3AE0" opacity="0.08"/>
  <circle cx="540" cy="700" r="150" fill="#6C3AE0" opacity="0.1"/>

  <!-- App icon placeholder -->
  <g transform="translate(540, 580)">
    <rect x="-80" y="-80" width="160" height="160" rx="40" fill="url(#purple)" filter="url(#bigGlow)"/>
    <text x="0" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="80" fill="#fff">✓</text>
  </g>

  <text x="540" y="840" text-anchor="middle" font-family="system-ui, sans-serif" font-size="90" font-weight="bold" fill="#ffffff" filter="url(#glow)" letter-spacing="-3">Todo Budget</text>

  <text x="540" y="940" text-anchor="middle" font-family="system-ui, sans-serif" font-size="36" fill="#8888aa">Задачи · Бюджет · Помодоро · Заметки</text>

  <!-- Glowing zero price -->
  <g transform="translate(540, 1100)">
    <rect x="-140" y="-50" width="280" height="100" rx="50" fill="#00E5A0" opacity="0.12" stroke="#00E5A0" stroke-width="2" stroke-opacity="0.4"/>
    <text x="0" y="18" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" fill="#00E5A0" filter="url(#glow)">0 ₽</text>
  </g>

  <text x="540" y="1240" text-anchor="middle" font-family="system-ui, sans-serif" font-size="32" fill="#555577">Навсегда бесплатно</text>
</svg>''', "Todo Budget. Задачи, бюджет, помодоро и заметки. Ноль рублей. Навсегда.")

# ── Scene 5: Tasks feature ──────────────────────────────────────────────────
add_scene("tasks", 3.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0a1a"/>
      <stop offset="100%" style="stop-color:#161630"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="200" cy="400" r="300" fill="#6C3AE0" opacity="0.04"/>

  <text x="540" y="280" text-anchor="middle" font-size="80">✅</text>
  <text x="540" y="400" text-anchor="middle" font-family="system-ui, sans-serif" font-size="60" font-weight="bold" fill="#ffffff">Умные задачи</text>

  <!-- Task cards -->
  <g transform="translate(80, 500)">
    <rect width="920" height="130" rx="22" fill="#1e1e38" stroke="#6C3AE0" stroke-width="1.5" stroke-opacity="0.3"/>
    <circle cx="60" cy="65" r="22" fill="none" stroke="#FF6B6B" stroke-width="3"/>
    <text x="105" y="55" font-family="system-ui, sans-serif" font-size="28" fill="#eee">Купить продукты</text>
    <text x="105" y="90" font-family="system-ui, sans-serif" font-size="18" fill="#666">Сегодня, 18:00</text>
    <rect x="780" y="50" width="80" height="10" rx="5" fill="#FF6B6B"/>
    <text x="790" y="90" font-family="system-ui, sans-serif" font-size="14" fill="#FF6B6B">Высокий</text>
  </g>

  <g transform="translate(80, 650)">
    <rect width="920" height="130" rx="22" fill="#1e1e38" stroke="#6C3AE0" stroke-width="1.5" stroke-opacity="0.3"/>
    <circle cx="60" cy="65" r="22" fill="#00E5A0" opacity="0.3"/>
    <text x="48" y="73" font-size="26" fill="#00E5A0">✓</text>
    <text x="105" y="55" font-family="system-ui, sans-serif" font-size="28" fill="#666" text-decoration="line-through">Оплатить интернет</text>
    <text x="105" y="90" font-family="system-ui, sans-serif" font-size="18" fill="#444">Выполнено</text>
  </g>

  <g transform="translate(80, 800)">
    <rect width="920" height="130" rx="22" fill="#1e1e38" stroke="#6C3AE0" stroke-width="1.5" stroke-opacity="0.3"/>
    <circle cx="60" cy="65" r="22" fill="none" stroke="#FFB347" stroke-width="3"/>
    <text x="105" y="55" font-family="system-ui, sans-serif" font-size="28" fill="#eee">Подготовить отчёт</text>
    <text x="105" y="90" font-family="system-ui, sans-serif" font-size="18" fill="#666">Завтра, 10:00 · Повторяется</text>
    <rect x="780" y="50" width="80" height="10" rx="5" fill="#FFB347"/>
  </g>

  <g transform="translate(80, 950)">
    <rect width="920" height="130" rx="22" fill="#1e1e38" stroke="#6C3AE0" stroke-width="1.5" stroke-opacity="0.3"/>
    <circle cx="60" cy="65" r="22" fill="none" stroke="#00C9FF" stroke-width="3"/>
    <text x="105" y="55" font-family="system-ui, sans-serif" font-size="28" fill="#eee">Прочитать главу книги</text>
    <text x="105" y="90" font-family="system-ui, sans-serif" font-size="18" fill="#666">Пт, 21:00 · 2 подзадачи</text>
    <rect x="780" y="50" width="80" height="10" rx="5" fill="#00C9FF"/>
  </g>

  <!-- Feature pills bottom -->
  <g transform="translate(540, 1200)">
    <rect x="-420" y="0" width="200" height="50" rx="25" fill="#6C3AE0" opacity="0.2"/>
    <text x="-320" y="33" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#B8A0FF">Приоритеты</text>
    <rect x="-200" y="0" width="180" height="50" rx="25" fill="#6C3AE0" opacity="0.2"/>
    <text x="-110" y="33" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#B8A0FF">Подзадачи</text>
    <rect x="0" y="0" width="200" height="50" rx="25" fill="#6C3AE0" opacity="0.2"/>
    <text x="100" y="33" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#B8A0FF">Свайп-жесты</text>
    <rect x="220" y="0" width="200" height="50" rx="25" fill="#6C3AE0" opacity="0.2"/>
    <text x="320" y="33" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#B8A0FF">Напоминания</text>
  </g>

  <text x="540" y="1360" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#555577">Свайпни → завершить или удалить</text>
</svg>''', "Умные задачи. Приоритеты, подзадачи, свайпы и напоминания.")

# ── Scene 6: Budget feature ──────────────────────────────────────────────────
add_scene("budget", 3.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0a1a"/>
      <stop offset="100%" style="stop-color:#0a1a20"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="800" cy="500" r="300" fill="#00E5A0" opacity="0.03"/>

  <text x="540" y="280" text-anchor="middle" font-size="80">💰</text>
  <text x="540" y="400" text-anchor="middle" font-family="system-ui, sans-serif" font-size="60" font-weight="bold" fill="#ffffff">Учёт финансов</text>

  <!-- Balance card -->
  <g transform="translate(80, 480)">
    <rect width="920" height="200" rx="28" fill="#1e1e38" stroke="#00E5A0" stroke-width="2" stroke-opacity="0.3"/>
    <text x="50" y="55" font-family="system-ui, sans-serif" font-size="22" fill="#666">Текущий баланс</text>
    <text x="50" y="120" font-family="system-ui, sans-serif" font-size="64" font-weight="bold" fill="#00E5A0" filter="url(#glow)">₽42 350</text>
    <text x="420" y="120" font-family="system-ui, sans-serif" font-size="24" fill="#00E5A0">↑ +12.3%</text>
    <text x="50" y="165" font-family="system-ui, sans-serif" font-size="20" fill="#555">Доходы: ₽65 000 · Расходы: ₽22 650</text>
  </g>

  <!-- Chart bars -->
  <g transform="translate(80, 720)">
    <rect width="920" height="260" rx="28" fill="#1e1e38"/>
    <text x="50" y="45" font-family="system-ui, sans-serif" font-size="20" fill="#666">Расходы по категориям</text>

    <rect x="50" y="75" width="500" height="30" rx="8" fill="#FF6B6B" opacity="0.8"/>
    <text x="560" y="97" font-family="system-ui, sans-serif" font-size="16" fill="#ccc">Еда — ₽8 500</text>

    <rect x="50" y="115" width="350" height="30" rx="8" fill="#FFB347" opacity="0.8"/>
    <text x="410" y="137" font-family="system-ui, sans-serif" font-size="16" fill="#ccc">Транспорт — ₽5 200</text>

    <rect x="50" y="155" width="250" height="30" rx="8" fill="#00C9FF" opacity="0.8"/>
    <text x="310" y="177" font-family="system-ui, sans-serif" font-size="16" fill="#ccc">Развлечения — ₽4 100</text>

    <rect x="50" y="195" width="180" height="30" rx="8" fill="#B8A0FF" opacity="0.8"/>
    <text x="240" y="217" font-family="system-ui, sans-serif" font-size="16" fill="#ccc">Прочее — ₽2 850</text>
  </g>

  <!-- Health indicator -->
  <g transform="translate(80, 1020)">
    <rect width="920" height="120" rx="28" fill="#0a2a1a" stroke="#00E5A0" stroke-width="1.5" stroke-opacity="0.3"/>
    <text x="50" y="50" font-family="system-ui, sans-serif" font-size="22" fill="#666">Здоровье бюджета</text>
    <rect x="50" y="70" width="700" height="18" rx="9" fill="#1a3a2a"/>
    <rect x="50" y="70" width="550" height="18" rx="9" fill="#00E5A0"/>
    <text x="770" y="87" font-family="system-ui, sans-serif" font-size="22" font-weight="bold" fill="#00E5A0">78%</text>
    <text x="820" y="87" font-family="system-ui, sans-serif" font-size="18" fill="#00E5A0">✓</text>
  </g>

  <!-- Features -->
  <g transform="translate(540, 1260)">
    <text x="-350" y="0" font-family="system-ui, sans-serif" font-size="22" fill="#00E5A0">✓ Лимиты расходов</text>
    <text x="50" y="0" font-family="system-ui, sans-serif" font-size="22" fill="#00E5A0">✓ Учёт долгов</text>
    <text x="-350" y="50" font-family="system-ui, sans-serif" font-size="22" fill="#00E5A0">✓ Графики</text>
    <text x="50" y="50" font-family="system-ui, sans-serif" font-size="22" fill="#00E5A0">✓ Виджет баланса</text>
  </g>
</svg>''', "Учёт финансов. Расходы, доходы, лимиты. Графики и виджет баланса прямо на рабочий стол.")

# ── Scene 7: Pomodoro + Notes ────────────────────────────────────────────────
add_scene("pomodoro_notes", 3.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0a1a"/>
      <stop offset="100%" style="stop-color:#1a0a10"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>

  <!-- Pomodoro section -->
  <text x="540" y="250" text-anchor="middle" font-size="70">⏱</text>
  <text x="540" y="360" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" fill="#fff">Помодоро-таймер</text>

  <!-- Timer display -->
  <g transform="translate(540, 580)">
    <circle cx="0" cy="0" r="180" fill="none" stroke="#FF6B6B" stroke-width="6" stroke-opacity="0.2"/>
    <circle cx="0" cy="0" r="180" fill="none" stroke="#FF6B6B" stroke-width="6" stroke-dasharray="850" stroke-dashoffset="212" stroke-linecap="round" transform="rotate(-90)" filter="url(#glow)"/>
    <text x="0" y="-20" text-anchor="middle" font-family="monospace" font-size="80" font-weight="bold" fill="#fff" filter="url(#glow)">18:42</text>
    <text x="0" y="30" text-anchor="middle" font-family="system-ui, sans-serif" font-size="24" fill="#FF8A8A">Фокусировка</text>
    <text x="0" y="70" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#555">Сессия 4 из 8</text>
  </g>

  <!-- Presets -->
  <g transform="translate(540, 850)">
    <rect x="-320" y="-25" width="180" height="50" rx="25" fill="#FF6B6B" opacity="0.2" stroke="#FF6B6B" stroke-width="1" stroke-opacity="0.3"/>
    <text x="-230" y="8" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#FF8A8A">25 мин фокус</text>
    <rect x="-110" y="-25" width="220" height="50" rx="25" fill="#FFB347" opacity="0.15"/>
    <text x="0" y="8" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#FFB347">5 мин перерыв</text>
    <rect x="130" y="-25" width="190" height="50" rx="25" fill="#00C9FF" opacity="0.15"/>
    <text x="225" y="8" text-anchor="middle" font-family="system-ui, sans-serif" font-size="18" fill="#00C9FF">15 мин длинный</text>
  </g>

  <!-- Divider -->
  <rect x="140" y="940" width="800" height="2" rx="1" fill="#333" opacity="0.5"/>

  <!-- Notes section -->
  <text x="540" y="1040" text-anchor="middle" font-size="70">📝</text>
  <text x="540" y="1140" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" fill="#fff">Быстрые заметки</text>

  <g transform="translate(80, 1200)">
    <rect width="920" height="120" rx="22" fill="#1e1e38" stroke="#00C9FF" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="50" y="50" font-family="system-ui, sans-serif" font-size="24" fill="#ccc">Идея для проекта: сделать API для...</text>
    <text x="50" y="85" font-family="system-ui, sans-serif" font-size="16" fill="#555">Сегодня, 14:32</text>
    <text x="800" y="70" font-family="system-ui, sans-serif" font-size="30" fill="#00C9FF">🎤</text>
  </g>

  <g transform="translate(80, 1340)">
    <rect width="920" height="120" rx="22" fill="#1e1e38" stroke="#00C9FF" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="50" y="50" font-family="system-ui, sans-serif" font-size="24" fill="#ccc">Рецепт пасты карбонара 🍝</text>
    <text x="50" y="85" font-family="system-ui, sans-serif" font-size="16" fill="#555">Вчера, 19:15</text>
  </g>

  <text x="540" y="1560" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#00C9FF">Текст + голосовой ввод 🎙</text>
</svg>''', "Помодоро-таймер для фокусировки. И быстрые заметки с голосовым вводом.")

# ── Scene 8: Key stats cinematic ─────────────────────────────────────────────
add_scene("stats", 3.5, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#050510"/>
      <stop offset="100%" style="stop-color:#0a0a20"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="10" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>

  <text x="540" y="280" text-anchor="middle" font-family="system-ui, sans-serif" font-size="48" fill="#555577">Почему Todo Budget?</text>

  <!-- Big stat: Size -->
  <g transform="translate(540, 480)">
    <text x="0" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="130" font-weight="bold" fill="#00E5A0" filter="url(#glow)">9 МБ</text>
    <text x="0" y="55" text-anchor="middle" font-family="system-ui, sans-serif" font-size="28" fill="#555">Легче одной фотки</text>
  </g>

  <!-- Big stat: Price -->
  <g transform="translate(540, 720)">
    <text x="0" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="130" font-weight="bold" fill="#FF6B6B" filter="url(#glow)">0 ₽</text>
    <text x="0" y="55" text-anchor="middle" font-family="system-ui, sans-serif" font-size="28" fill="#555">Навсегда. Без подписок.</text>
  </g>

  <!-- Stat blocks -->
  <g transform="translate(80, 900)">
    <rect width="440" height="150" rx="24" fill="#1e1e38" stroke="#00C9FF" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="220" y="65" text-anchor="middle" font-size="44">📴</text>
    <text x="220" y="115" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#00C9FF">Работает оффлайн</text>
  </g>

  <g transform="translate(560, 900)">
    <rect width="440" height="150" rx="24" fill="#1e1e38" stroke="#B8A0FF" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="220" y="65" text-anchor="middle" font-size="44">🔒</text>
    <text x="220" y="115" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#B8A0FF">Данные локально</text>
  </g>

  <g transform="translate(80, 1080)">
    <rect width="440" height="150" rx="24" fill="#1e1e38" stroke="#FFB347" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="220" y="65" text-anchor="middle" font-size="44">🌙</text>
    <text x="220" y="115" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#FFB347">Тёмная тема</text>
  </g>

  <g transform="translate(560, 1080)">
    <rect width="440" height="150" rx="24" fill="#1e1e38" stroke="#00E5A0" stroke-width="1.5" stroke-opacity="0.2"/>
    <text x="220" y="65" text-anchor="middle" font-size="44">📦</text>
    <text x="220" y="115" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#00E5A0">Экспорт CSV</text>
  </g>

  <text x="540" y="1380" text-anchor="middle" font-family="system-ui, sans-serif" font-size="28" fill="#444">Android 5.0+ · Kotlin · Jetpack Compose</text>
</svg>''', "Девять мегабайт. Ноль рублей. Оффлайн. Все данные на устройстве.")

# ── Scene 9: Final CTA ──────────────────────────────────────────────────────
add_scene("cta", 4.0, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a0a1a"/>
      <stop offset="100%" style="stop-color:#161630"/>
    </linearGradient>
    <linearGradient id="purple" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6C3AE0"/>
      <stop offset="100%" style="stop-color:#9B6BFF"/>
    </linearGradient>
    <filter id="bigGlow"><feGaussianBlur stdDeviation="25" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="glow"><feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>

  <!-- Dramatic circles -->
  <circle cx="540" cy="960" r="600" fill="#6C3AE0" opacity="0.03"/>
  <circle cx="540" cy="960" r="450" fill="#6C3AE0" opacity="0.04"/>
  <circle cx="540" cy="960" r="300" fill="#6C3AE0" opacity="0.05"/>

  <!-- Feature emojis floating -->
  <text x="200" y="350" font-size="60" opacity="0.3">✅</text>
  <text x="800" y="400" font-size="55" opacity="0.3">💰</text>
  <text x="250" y="1500" font-size="50" opacity="0.3">⏱</text>
  <text x="850" y="1550" font-size="55" opacity="0.3">📝</text>

  <!-- Main title -->
  <text x="540" y="680" text-anchor="middle" font-family="system-ui, sans-serif" font-size="100" font-weight="bold" fill="#fff" filter="url(#bigGlow)" letter-spacing="-3">Todo Budget</text>

  <text x="540" y="780" text-anchor="middle" font-family="system-ui, sans-serif" font-size="38" fill="#8888aa">4 приложения в одном. 9 МБ.</text>

  <!-- FREE badge glowing -->
  <g transform="translate(540, 900)">
    <rect x="-160" y="-48" width="320" height="96" rx="48" fill="#00E5A0" opacity="0.12" stroke="#00E5A0" stroke-width="2.5" stroke-opacity="0.5"/>
    <text x="0" y="18" text-anchor="middle" font-family="system-ui, sans-serif" font-size="52" font-weight="bold" fill="#00E5A0" filter="url(#glow)">БЕСПЛАТНО</text>
  </g>

  <!-- CTA Button -->
  <g transform="translate(540, 1100)">
    <rect x="-280" y="-48" width="560" height="96" rx="48" fill="url(#purple)" filter="url(#glow)"/>
    <text x="0" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="36" font-weight="bold" fill="#fff">📲 Скачать в RuStore</text>
  </g>

  <!-- Website -->
  <g transform="translate(540, 1260)">
    <rect x="-280" y="-42" width="560" height="84" rx="42" fill="#1e1e38" stroke="#444" stroke-width="1.5"/>
    <text x="0" y="12" text-anchor="middle" font-family="system-ui, sans-serif" font-size="28" fill="#00C9FF">🌐 emil-a-dev.github.io/todofin</text>
  </g>

  <!-- Bottom text -->
  <text x="540" y="1450" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" fill="#444466">Ссылка в описании профиля ↓</text>

  <!-- Mini features row -->
  <g transform="translate(540, 1600)">
    <text x="-300" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" fill="#555577">✅ Задачи</text>
    <text x="-100" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" fill="#555577">💰 Бюджет</text>
    <text x="100" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" fill="#555577">⏱ Помодоро</text>
    <text x="300" y="0" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" fill="#555577">📝 Заметки</text>
  </g>
</svg>''', "Скачай Todo Budget. Бесплатно. Навсегда. Ссылка в описании.")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Render frames & generate audio
# ═══════════════════════════════════════════════════════════════════════════════

def render_frames():
    """SVG → PNG for all scenes."""
    import cairosvg
    for i, scene in enumerate(SCENES):
        png_path = FRAMES_DIR / f"{i:02d}_{scene['name']}.png"
        svg_path = FRAMES_DIR / f"{i:02d}_{scene['name']}.svg"
        # Save SVG
        with open(svg_path, "w") as f:
            f.write(scene["svg"])
        # Render PNG
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         output_width=W, output_height=H)
        scene["png"] = str(png_path)
        size_kb = os.path.getsize(png_path) // 1024
        print(f"  [{i+1}/{len(SCENES)}] {scene['name']}.png — {size_kb} KB")


def generate_voiceover():
    """Generate TTS voiceover for each scene."""
    from gtts import gTTS
    from pydub import AudioSegment

    vo_clips = []
    for i, scene in enumerate(SCENES):
        mp3_path = AUDIO_DIR / f"vo_{i:02d}.mp3"
        wav_path = AUDIO_DIR / f"vo_{i:02d}.wav"

        # Generate TTS
        tts = gTTS(text=scene["voiceover"], lang="ru", slow=False)
        tts.save(str(mp3_path))

        # Convert to wav and get duration
        audio = AudioSegment.from_mp3(str(mp3_path))

        # Speed up slightly for punchier feel (1.15x)
        audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * 1.15)
        }).set_frame_rate(audio.frame_rate)

        audio.export(str(wav_path), format="wav")
        scene["vo_wav"] = str(wav_path)
        scene["vo_duration"] = len(audio) / 1000.0
        vo_clips.append(audio)
        print(f"  [{i+1}/{len(SCENES)}] vo_{i:02d}.wav — {scene['vo_duration']:.1f}s")

    return vo_clips


def generate_music():
    """Generate a synthetic electronic beat."""
    from pydub import AudioSegment
    from pydub.generators import Sine

    total_duration_ms = int(sum(s["duration"] for s in SCENES) * 1000) + 2000

    # Build a dark electronic beat
    sr = 44100

    # Kick drum synthesis (sine burst with decay)
    def make_kick(duration_ms=120, freq=55):
        t = np.linspace(0, duration_ms/1000, int(sr * duration_ms/1000))
        envelope = np.exp(-t * 30)
        freq_sweep = freq * (1 + 4 * np.exp(-t * 40))
        signal = envelope * np.sin(2 * np.pi * np.cumsum(freq_sweep) / sr)
        signal = (signal * 32767 * 0.7).astype(np.int16)
        return AudioSegment(signal.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    # Hi-hat synthesis
    def make_hihat(duration_ms=60):
        samples = int(sr * duration_ms / 1000)
        noise = np.random.uniform(-1, 1, samples)
        envelope = np.exp(-np.linspace(0, 10, samples))
        signal = (noise * envelope * 32767 * 0.15).astype(np.int16)
        return AudioSegment(signal.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    # Sub bass
    def make_sub(duration_ms=400, freq=40):
        t = np.linspace(0, duration_ms/1000, int(sr * duration_ms/1000))
        envelope = np.exp(-t * 3)
        signal = envelope * np.sin(2 * np.pi * freq * t)
        signal = (signal * 32767 * 0.35).astype(np.int16)
        return AudioSegment(signal.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    # Atmospheric pad
    def make_pad(duration_ms=2000, freq=110):
        t = np.linspace(0, duration_ms/1000, int(sr * duration_ms/1000))
        # Slow attack, sustain
        envelope = 1 - np.exp(-t * 2)
        envelope *= np.exp(-t * 0.3)
        # Detuned oscillators for richness
        sig1 = np.sin(2 * np.pi * freq * t)
        sig2 = np.sin(2 * np.pi * freq * 1.005 * t)
        sig3 = np.sin(2 * np.pi * freq * 2.01 * t) * 0.3
        signal = envelope * (sig1 + sig2 + sig3) / 2.3
        signal = (signal * 32767 * 0.12).astype(np.int16)
        return AudioSegment(signal.tobytes(), frame_rate=sr, sample_width=2, channels=1)

    silence_1ms = AudioSegment.silent(duration=1)

    # BPM: 75 (dark, cinematic feel)
    bpm = 75
    beat_ms = int(60000 / bpm)  # ~800ms per beat
    half_beat = beat_ms // 2

    # Build 1-bar pattern (4 beats)
    def make_bar():
        bar = AudioSegment.silent(duration=beat_ms * 4)

        # Kick on 1 and 3
        kick = make_kick()
        bar = bar.overlay(kick, position=0)
        bar = bar.overlay(kick, position=beat_ms * 2)

        # Hi-hat on every half beat
        hh = make_hihat()
        for i in range(8):
            bar = bar.overlay(hh, position=i * half_beat)

        # Sub bass on 1
        sub = make_sub(duration_ms=beat_ms * 2)
        bar = bar.overlay(sub, position=0)

        return bar

    # Build track
    num_bars = (total_duration_ms // (beat_ms * 4)) + 2
    track = AudioSegment.silent(duration=0)

    for i in range(num_bars):
        bar = make_bar()
        track += bar

    # Add atmospheric pad layer
    pad_layer = AudioSegment.silent(duration=0)
    pad_notes = [110, 82.5, 110, 146.8]  # Am chord tones
    for i in range(num_bars):
        note_freq = pad_notes[i % len(pad_notes)]
        pad = make_pad(duration_ms=beat_ms * 4, freq=note_freq)
        pad_layer += pad
    
    # Trim pad to match
    min_len = min(len(track), len(pad_layer))
    track = track[:min_len]
    pad_layer = pad_layer[:min_len]

    # Mix
    final_music = track.overlay(pad_layer)

    # Fade in/out
    final_music = final_music.fade_in(2000).fade_out(3000)

    # Trim to exact duration
    final_music = final_music[:total_duration_ms]

    music_path = AUDIO_DIR / "music.wav"
    final_music.export(str(music_path), format="wav")
    print(f"  Music: {len(final_music)/1000:.1f}s, saved to {music_path}")
    return final_music, str(music_path)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Assemble cinematic video with moviepy
# ═══════════════════════════════════════════════════════════════════════════════

def assemble_video(music_path):
    """Build final video with transitions, zoom, and audio."""
    from moviepy import (
        ImageClip, CompositeVideoClip, AudioFileClip,
        CompositeAudioClip, concatenate_videoclips, vfx
    )

    TRANSITION = 0.6  # crossfade duration

    clips = []
    current_time = 0

    for i, scene in enumerate(SCENES):
        dur = scene["duration"]

        # Create image clip
        clip = ImageClip(scene["png"], duration=dur + TRANSITION)

        # Ken Burns effect: slow zoom in or out
        if i % 3 == 0:
            # Zoom in from 1.0 to 1.08
            clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.08 * t / (dur + TRANSITION))])
        elif i % 3 == 1:
            # Zoom out from 1.08 to 1.0
            clip = clip.with_effects([vfx.Resize(lambda t: 1.08 - 0.08 * t / (dur + TRANSITION))])
        else:
            # Slight zoom
            clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.04 * t / (dur + TRANSITION))])

        # Resize back to exact dimensions (Ken Burns may shift)
        clip = clip.resized((W, H))

        # Crossfade
        if i > 0:
            clip = clip.with_start(current_time - TRANSITION)
            clip = clip.with_effects([vfx.CrossFadeIn(TRANSITION)])
        else:
            clip = clip.with_start(0)
            clip = clip.with_effects([vfx.CrossFadeIn(0.8)])  # fade in from black

        clips.append(clip)
        current_time += dur

    # Compose video
    total_dur = current_time + 1
    video = CompositeVideoClip(clips, size=(W, H)).with_duration(total_dur)

    # Fade out at the end
    video = video.with_effects([vfx.CrossFadeOut(1.5)])

    # ── Audio mixing ──
    # Music track
    music_clip = AudioFileClip(music_path).with_duration(total_dur)
    music_clip = music_clip.with_volume_scaled(0.35)

    # Voiceover clips positioned in time
    vo_clips = []
    t = 0
    for i, scene in enumerate(SCENES):
        if "vo_wav" in scene and os.path.exists(scene["vo_wav"]):
            vo = AudioFileClip(scene["vo_wav"])
            # Start voice 0.3s into each scene
            vo = vo.with_start(t + 0.4)
            vo = vo.with_volume_scaled(1.2)
            vo_clips.append(vo)
        t += scene["duration"]

    # Mix all audio
    all_audio = [music_clip] + vo_clips
    final_audio = CompositeAudioClip(all_audio).with_duration(total_dur)

    video = video.with_audio(final_audio)

    # Export
    print(f"  Rendering {total_dur:.1f}s video at {W}x{H} {FPS}fps...")
    video.write_videofile(
        str(OUTPUT),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        audio_bitrate="192k",
        preset="medium",
        threads=4,
        logger="bar",
    )

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"  ✅ Video saved: {OUTPUT} ({size_mb:.1f} MB)")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🎬 Todo Budget — Cinematic Reels Builder")
    print("=" * 60)
    print()

    total = sum(s["duration"] for s in SCENES)
    print(f"📐 Resolution: {W}x{H}")
    print(f"🎞  Scenes: {len(SCENES)}")
    print(f"⏱  Total duration: {total:.1f}s")
    print()

    # Step 1
    print("━" * 40)
    print("1️⃣  Rendering SVG → PNG frames")
    print("━" * 40)
    render_frames()
    print()

    # Step 2
    print("━" * 40)
    print("2️⃣  Generating voiceover (Google TTS)")
    print("━" * 40)
    generate_voiceover()
    print()

    # Step 3
    print("━" * 40)
    print("3️⃣  Generating background music")
    print("━" * 40)
    _, music_path = generate_music()
    print()

    # Step 4
    print("━" * 40)
    print("4️⃣  Assembling cinematic video")
    print("━" * 40)
    assemble_video(music_path)
    print()

    # Summary
    print("=" * 60)
    print("✅ DONE!")
    print(f"📁 Output: {OUTPUT}")
    print()
    print("📝 Scene breakdown:")
    t = 0
    for i, s in enumerate(SCENES, 1):
        print(f"   {t:.1f}s – {t+s['duration']:.1f}s  [{s['name']}]")
        t += s["duration"]
    print(f"   Total: {t:.1f}s")
    print()
    print("🎵 Audio: Synthetic dark electronic beat + Russian TTS voiceover")
    print("🎬 Effects: Ken Burns zoom, crossfade transitions, fade in/out")
    print("=" * 60)


if __name__ == "__main__":
    main()
