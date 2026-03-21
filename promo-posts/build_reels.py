#!/usr/bin/env python3
"""
Скрипт для сборки Instagram Reels видео из SVG-кадров.
Зависимости: pip install cairosvg pillow

Для сборки в MP4 нужен ffmpeg:
  sudo apt install ffmpeg
  
Запуск: python3 build_reels.py
"""

import os
import subprocess
import cairosvg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REELS_DIR = os.path.join(BASE_DIR, "reels")
OUTPUT_DIR = os.path.join(REELS_DIR, "png")

# Кадры и длительность каждого (секунды)
FRAMES = [
    ("frame1-problem.svg", 3),    # Проблема: 3 приложения, ₽500/мес
    ("frame2-solution.svg", 3),   # Решение: Todo Budget
    ("frame3-features.svg", 4),   # 4 функции
    ("frame4-stats.svg", 4),      # Преимущества: 9 МБ, 0₽, оффлайн
    ("frame5-cta.svg", 4),        # CTA: скачать
]

FPS = 30
WIDTH = 1080
HEIGHT = 1920


def svg_to_png():
    """Конвертирует все SVG кадры в PNG."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for svg_name, _ in FRAMES:
        svg_path = os.path.join(REELS_DIR, svg_name)
        png_name = svg_name.replace(".svg", ".png")
        png_path = os.path.join(OUTPUT_DIR, png_name)
        
        print(f"  Конвертация {svg_name} → {png_name}")
        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=WIDTH,
            output_height=HEIGHT
        )
    
    print(f"  ✅ PNG кадры сохранены в {OUTPUT_DIR}")


def build_video():
    """Собирает MP4 из PNG кадров через ffmpeg."""
    # Создаём файл с описанием сцен для ffmpeg concat demuxer
    concat_file = os.path.join(REELS_DIR, "concat.txt")
    
    with open(concat_file, "w") as f:
        for svg_name, duration in FRAMES:
            png_name = svg_name.replace(".svg", ".png")
            png_path = os.path.join(OUTPUT_DIR, png_name)
            f.write(f"file '{png_path}'\n")
            f.write(f"duration {duration}\n")
        # Повторить последний кадр (требование ffmpeg concat)
        last_png = FRAMES[-1][0].replace(".svg", ".png")
        f.write(f"file '{os.path.join(OUTPUT_DIR, last_png)}'\n")
    
    output_path = os.path.join(BASE_DIR, "instagram-reels.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-vf", f"scale={WIDTH}:{HEIGHT},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-r", str(FPS),
        "-movflags", "+faststart",
        output_path
    ]
    
    print(f"  Сборка видео...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✅ Видео готово: {output_path} ({size_mb:.1f} МБ)")
    else:
        print(f"  ❌ Ошибка ffmpeg: {result.stderr[-500:]}")
        print(f"\n  Если ffmpeg не установлен:")
        print(f"    sudo apt install ffmpeg")
        print(f"\n  PNG кадры можно собрать в видео вручную через CapCut, InShot или другой редактор.")


def main():
    print("🎬 Сборка Instagram Reels")
    print()
    
    print("1️⃣  Конвертация SVG → PNG")
    svg_to_png()
    print()
    
    # Проверяем наличие ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        has_ffmpeg = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_ffmpeg = False
    
    if has_ffmpeg:
        print("2️⃣  Сборка MP4")
        build_video()
    else:
        print("2️⃣  ffmpeg не найден — пропускаю сборку видео")
        print()
        print("   Варианты:")
        print("   a) Установи ffmpeg: sudo apt install ffmpeg")
        print("      Затем запусти скрипт снова")
        print()
        print("   b) Собери кадры вручную в CapCut / InShot / VN:")
        for i, (svg_name, duration) in enumerate(FRAMES, 1):
            png_name = svg_name.replace(".svg", ".png")
            print(f"      Кадр {i}: {png_name} — {duration} сек")
    
    print()
    print("📝 Раскладка Reels (18 сек):")
    total = 0
    for i, (svg_name, duration) in enumerate(FRAMES, 1):
        desc = {
            "frame1-problem.svg": "Проблема — 3 приложения, подписки",
            "frame2-solution.svg": "Решение — Todo Budget",
            "frame3-features.svg": "4 функции в одном",
            "frame4-stats.svg": "Почему это круто: 9МБ, 0₽, оффлайн",
            "frame5-cta.svg": "CTA — скачать в RuStore",
        }[svg_name]
        print(f"   {total}с–{total+duration}с  Кадр {i}: {desc}")
        total += duration
    print(f"   Итого: {total} секунд")


if __name__ == "__main__":
    main()
