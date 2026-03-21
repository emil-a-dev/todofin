#!/usr/bin/env python3
"""
🎨 Todo Budget — Premium Logo Generator

Design concept: "Addictive Precision"
- Squircle shape with rich purple→green gradient
- Bold geometric checkmark that also suggests a rising graph/arrow (growth)
- Subtle coin circle motif (budget)
- Glass highlight for premium depth
- Spark/glow at the checkmark tip (completion dopamine)
- Clean, satisfying geometry — golden proportions

Outputs:
  - logo_master.svg          (vector master)
  - logo_1024.png            (master raster)
  - logo_512.png             (store listing)
  - ic_launcher variants     (Android mipmap)
  - ic_launcher_foreground   (adaptive icon)
  - ic_launcher_background   (adaptive icon)
"""

import math, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = Path(__file__).parent
LOGO_DIR = BASE / "logo"
LOGO_DIR.mkdir(exist_ok=True)

# ─── Brand Colors ───────────────────────────────────────────────────────
PURPLE_DARK  = (88, 38, 200)    # #5826C8
PURPLE       = (108, 58, 224)   # #6C3AE0
PURPLE_LIGHT = (140, 90, 255)   # #8C5AFF
GREEN        = (0, 229, 160)    # #00E5A0
GREEN_LIGHT  = (100, 255, 200)  # #64FFC8
CYAN         = (0, 210, 255)    # #00D2FF
WHITE        = (255, 255, 255)

def make_squircle_mask(size, radius_factor=0.28):
    """Create a superellipse (squircle) mask — the iOS icon shape, smoother than round rect."""
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)

    # Use a high-quality superellipse approximation
    n = 5  # exponent (4=normal squircle, 5=more square-ish like iOS)
    cx = cy = size / 2
    r = size / 2 - 2

    points = []
    for angle in range(0, 360):
        t = math.radians(angle)
        cos_t = math.cos(t)
        sin_t = math.sin(t)
        # Superellipse formula
        x = cx + r * abs(cos_t) ** (2/n) * (1 if cos_t >= 0 else -1)
        y = cy + r * abs(sin_t) ** (2/n) * (1 if sin_t >= 0 else -1)
        points.append((x, y))

    draw.polygon(points, fill=255)
    return img


def draw_gradient_squircle(size):
    """Draw the gradient background squircle."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Create diagonal gradient: purple-dark → purple → green
    for y in range(size):
        for x in range(size):
            # Diagonal progress (top-left to bottom-right)
            p = (x / size * 0.6 + y / size * 0.4)
            # Three-stop gradient
            if p < 0.4:
                t = p / 0.4
                r = int(PURPLE_DARK[0] + (PURPLE[0] - PURPLE_DARK[0]) * t)
                g = int(PURPLE_DARK[1] + (PURPLE[1] - PURPLE_DARK[1]) * t)
                b = int(PURPLE_DARK[2] + (PURPLE[2] - PURPLE_DARK[2]) * t)
            elif p < 0.75:
                t = (p - 0.4) / 0.35
                r = int(PURPLE[0] + (GREEN[0] - PURPLE[0]) * t)
                g = int(PURPLE[1] + (GREEN[1] - PURPLE[1]) * t)
                b = int(PURPLE[2] + (GREEN[2] - PURPLE[2]) * t)
            else:
                t = (p - 0.75) / 0.25
                r = int(GREEN[0] + (GREEN_LIGHT[0] - GREEN[0]) * t)
                g = int(GREEN[1] + (GREEN_LIGHT[1] - GREEN[1]) * t)
                b = int(GREEN[2] + (GREEN_LIGHT[2] - GREEN[2]) * t)
            grad.putpixel((x, y), (r, g, b, 255))

    # Apply squircle mask
    mask = make_squircle_mask(size)
    img.paste(grad, (0, 0), mask)
    return img, mask


def draw_glass_highlight(size, mask):
    """Draw the premium glossy highlight on top."""
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(highlight)

    # Top-left elliptical highlight
    h_w = int(size * 0.7)
    h_h = int(size * 0.35)
    h_x = int(size * 0.05)
    h_y = int(size * 0.02)

    # Create gradient highlight
    for y in range(h_y, h_y + h_h):
        for x in range(h_x, h_x + h_w):
            # Elliptical distance
            ex = (x - h_x - h_w / 2) / (h_w / 2)
            ey = (y - h_y - h_h / 2) / (h_h / 2)
            d = math.sqrt(ex * ex + ey * ey)
            if d < 1.0:
                alpha = int(45 * (1 - d) ** 2)  # Soft falloff
                highlight.putpixel((x, y), (255, 255, 255, alpha))

    # Mask to squircle
    h_mask = Image.new("L", (size, size), 0)
    h_data = highlight.split()[3]
    # Combine with squircle mask
    from PIL import ImageChops
    h_mask = ImageChops.multiply(h_data, mask)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(highlight, (0, 0), h_mask)
    return result


def draw_checkmark(draw, size, cx, cy, scale=1.0, stroke_width=None):
    """
    Draw a bold, geometric checkmark.
    The checkmark is designed to also subtly suggest an upward arrow/growth trend.
    """
    s = scale
    if stroke_width is None:
        stroke_width = int(size * 0.075 * s)

    # Checkmark geometry — satisfying proportions
    # Three points: start (left), vertex (bottom), end (top-right)
    # Slightly offset from center to feel dynamic

    # Start point (left middle)
    x1 = cx - int(size * 0.22 * s)
    y1 = cy - int(size * 0.02 * s)

    # Vertex (bottom of check)
    x2 = cx - int(size * 0.04 * s)
    y2 = cy + int(size * 0.20 * s)

    # End point (top-right, higher than start = growth feeling)
    x3 = cx + int(size * 0.26 * s)
    y3 = cy - int(size * 0.22 * s)

    return [(x1, y1), (x2, y2), (x3, y3)], stroke_width


def draw_coin_ring(draw, size, cx, cy, scale=1.0):
    """Draw a subtle circular ring (coin/completeness motif)."""
    r = int(size * 0.32 * scale)
    ring_w = max(2, int(size * 0.015 * scale))

    # Draw arc — not full circle, partial for elegance
    bbox = [cx - r, cy - r, cx + r, cy + r]
    draw.arc(bbox, start=-60, end=240, fill=(*WHITE, 60), width=ring_w)


def draw_spark(draw, size, x, y, scale=1.0):
    """Draw a sparkle/star at the checkmark tip — completion feeling."""
    s = scale
    r1 = int(size * 0.04 * s)  # outer
    r2 = int(size * 0.015 * s)  # inner

    # 4-pointed star
    points = []
    for i in range(8):
        angle = math.radians(i * 45 - 90)  # start from top
        r = r1 if i % 2 == 0 else r2
        points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
    draw.polygon(points, fill=(*WHITE, 220))

    # Center glow
    gr = int(size * 0.025 * s)
    draw.ellipse([x - gr, y - gr, x + gr, y + gr], fill=(*WHITE, 100))


def draw_mini_dots(draw, size, cx, cy, scale=1.0):
    """Draw 3 small dots suggesting list items / data points — reinforces the app concept."""
    s = scale
    dot_r = int(size * 0.018 * s)
    gap = int(size * 0.065 * s)

    # Position them subtly near the bottom-left of the checkmark
    base_x = cx - int(size * 0.18 * s)
    base_y = cy + int(size * 0.08 * s)

    for i in range(3):
        dx = base_x
        dy = base_y + i * gap
        alpha = 200 - i * 50
        draw.ellipse([dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r],
                     fill=(*WHITE, alpha))


def generate_logo(size=1024):
    """Generate the complete logo at given size."""
    # 1. Gradient squircle background
    img, mask = draw_gradient_squircle(size)
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    # Slight offset up for visual balance (optical center)
    cy_visual = cy - int(size * 0.02)

    # 2. Subtle coin ring
    draw_coin_ring(draw, size, cx, cy_visual)

    # 3. Bold checkmark — THE main element
    points, sw = draw_checkmark(draw, size, cx, cy_visual)

    # Draw checkmark with thick rounded strokes
    # Shadow first
    shadow_off = max(2, int(size * 0.008))
    shadow_pts = [(x + shadow_off, y + shadow_off) for x, y in points]
    draw.line(shadow_pts, fill=(0, 0, 0, 40), width=sw + 4, joint="curve")

    # Main white checkmark
    draw.line(points, fill=(*WHITE, 255), width=sw, joint="curve")

    # Round caps at start and end
    cap_r = sw // 2
    for pt in [points[0], points[2]]:
        draw.ellipse([pt[0] - cap_r, pt[1] - cap_r, pt[0] + cap_r, pt[1] + cap_r],
                     fill=(*WHITE, 255))
    # Vertex cap
    draw.ellipse([points[1][0] - cap_r, points[1][1] - cap_r,
                  points[1][0] + cap_r, points[1][1] + cap_r],
                 fill=(*WHITE, 255))

    # 4. Spark at checkmark tip
    draw_spark(draw, size, points[2][0] + int(size * 0.01),
               points[2][1] - int(size * 0.02))

    # 5. Glass highlight for depth
    highlight = draw_glass_highlight(size, mask)
    img = Image.alpha_composite(img, highlight)

    # 6. Subtle outer glow
    glow = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    glow.paste(img, (20, 20))
    glow_only = glow.filter(ImageFilter.GaussianBlur(radius=8))
    # Dim the glow
    glow_data = glow_only.split()
    glow_alpha = glow_data[3].point(lambda x: min(40, x))
    glow_only.putalpha(glow_alpha)

    final = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    final = Image.alpha_composite(final, glow_only)
    final.paste(img, (20, 20), img)

    return final, img  # (with_glow, clean)


def generate_adaptive_foreground(size=1024):
    """
    Android adaptive icon foreground layer.
    108dp with 72dp safe zone centered.
    We render at 432px (xxxhdpi *4 factor, or just use our 1024 and scale).
    """
    # The foreground should be the symbol only on transparent bg
    # Safe zone: inner 66.67% circle
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2 - int(size * 0.02)

    # Coin ring
    draw_coin_ring(draw, size, cx, cy, scale=0.75)

    # Checkmark
    points, sw = draw_checkmark(draw, size, cx, cy, scale=0.75)

    # Shadow
    shadow_off = max(2, int(size * 0.005))
    shadow_pts = [(x + shadow_off, y + shadow_off) for x, y in points]
    draw.line(shadow_pts, fill=(0, 0, 0, 50), width=sw + 4, joint="curve")

    # White checkmark
    draw.line(points, fill=(*WHITE, 255), width=sw, joint="curve")
    cap_r = sw // 2
    for pt in [points[0], points[1], points[2]]:
        draw.ellipse([pt[0] - cap_r, pt[1] - cap_r, pt[0] + cap_r, pt[1] + cap_r],
                     fill=(*WHITE, 255))

    # Spark
    draw_spark(draw, size, points[2][0] + int(size * 0.008),
               points[2][1] - int(size * 0.015), scale=0.75)

    return img


def generate_adaptive_background(size=1024):
    """Adaptive icon background — just the gradient."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Full gradient fill (no squircle mask — the system applies the mask)
    for y in range(size):
        for x in range(size):
            p = (x / size * 0.6 + y / size * 0.4)
            if p < 0.4:
                t = p / 0.4
                r = int(PURPLE_DARK[0] + (PURPLE[0] - PURPLE_DARK[0]) * t)
                g = int(PURPLE_DARK[1] + (PURPLE[1] - PURPLE_DARK[1]) * t)
                b = int(PURPLE_DARK[2] + (PURPLE[2] - PURPLE_DARK[2]) * t)
            elif p < 0.75:
                t = (p - 0.4) / 0.35
                r = int(PURPLE[0] + (GREEN[0] - PURPLE[0]) * t)
                g = int(PURPLE[1] + (GREEN[1] - PURPLE[1]) * t)
                b = int(PURPLE[2] + (GREEN[2] - PURPLE[2]) * t)
            else:
                t = (p - 0.75) / 0.25
                r = int(GREEN[0] + (GREEN_LIGHT[0] - GREEN[0]) * t)
                g = int(GREEN[1] + (GREEN_LIGHT[1] - GREEN[1]) * t)
                b = int(GREEN[2] + (GREEN_LIGHT[2] - GREEN[2]) * t)
            img.putpixel((x, y), (r, g, b, 255))
    return img


def generate_svg():
    """Generate an SVG version of the logo."""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Main gradient: deep purple → purple → green → light green -->
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="80%" y2="100%">
      <stop offset="0%" style="stop-color:#5826C8"/>
      <stop offset="35%" style="stop-color:#6C3AE0"/>
      <stop offset="70%" style="stop-color:#00E5A0"/>
      <stop offset="100%" style="stop-color:#64FFC8"/>
    </linearGradient>

    <!-- Glass highlight gradient -->
    <radialGradient id="glass" cx="35%" cy="25%" r="50%" fx="30%" fy="20%">
      <stop offset="0%" style="stop-color:rgba(255,255,255,0.22)"/>
      <stop offset="100%" style="stop-color:rgba(255,255,255,0)"/>
    </radialGradient>

    <!-- Outer glow -->
    <filter id="glow" x="-15%" y="-15%" width="130%" height="130%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Checkmark shadow -->
    <filter id="check-shadow" x="-5%" y="-5%" width="115%" height="115%">
      <feDropShadow dx="2" dy="3" stdDeviation="3" flood-color="rgba(0,0,0,0.2)"/>
    </filter>

    <!-- Spark glow -->
    <filter id="spark-glow">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Squircle (superellipse) clip -->
    <clipPath id="squircle">
      <path d="M256,8 C410,8 504,8 504,102 C504,196 504,256 504,256 C504,316 504,410 504,410 C504,504 410,504 256,504 C102,504 8,504 8,410 C8,316 8,256 8,256 C8,196 8,102 8,102 C8,8 102,8 256,8 Z"/>
    </clipPath>
  </defs>

  <!-- Background squircle with gradient -->
  <g clip-path="url(#squircle)" filter="url(#glow)">
    <rect x="0" y="0" width="512" height="512" fill="url(#bg-grad)"/>

    <!-- Glass highlight -->
    <ellipse cx="190" cy="130" rx="180" ry="100" fill="url(#glass)"/>
  </g>

  <!-- Coin ring (subtle) -->
  <circle cx="256" cy="246" r="160" fill="none" stroke="rgba(255,255,255,0.15)"
          stroke-width="4" stroke-dasharray="580 200" stroke-linecap="round"
          clip-path="url(#squircle)"/>

  <!-- Checkmark -->
  <g clip-path="url(#squircle)" filter="url(#check-shadow)">
    <polyline points="146,248 232,348 390,142"
              fill="none" stroke="white" stroke-width="42"
              stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- Spark at checkmark tip -->
  <g clip-path="url(#squircle)" filter="url(#spark-glow)">
    <!-- 4-pointed star -->
    <polygon points="395,128 399,136 407,136 401,142 403,150 395,146 387,150 389,142 383,136 391,136"
             fill="white" opacity="0.85"/>
    <!-- Center glow dot -->
    <circle cx="395" cy="138" r="5" fill="white" opacity="0.5"/>
  </g>
</svg>'''
    return svg


def main():
    print("=" * 50)
    print("🎨 TODO BUDGET — LOGO GENERATOR")
    print("=" * 50)

    # 1. SVG
    print("\n1️⃣  SVG master...")
    svg = generate_svg()
    svg_path = LOGO_DIR / "logo_master.svg"
    svg_path.write_text(svg)
    print(f"   ✅ {svg_path}")

    # Also save to landing page
    landing_svg = BASE.parent / "docs" / "logo.svg"
    if landing_svg.parent.exists():
        landing_svg.write_text(svg)
        print(f"   ✅ {landing_svg}")

    # 2. High-res PNG renders
    print("\n2️⃣  Master PNG (1024px)...")
    logo_glow, logo_clean = generate_logo(1024)
    logo_glow.save(str(LOGO_DIR / "logo_1024_glow.png"), "PNG")
    logo_clean.save(str(LOGO_DIR / "logo_1024.png"), "PNG")
    print(f"   ✅ logo_1024.png ({os.path.getsize(LOGO_DIR / 'logo_1024.png') // 1024}KB)")

    # 512px for store listing
    logo_512 = logo_clean.resize((512, 512), Image.LANCZOS)
    logo_512.save(str(LOGO_DIR / "logo_512.png"), "PNG")
    print(f"   ✅ logo_512.png")

    # 3. Android mipmap icons
    print("\n3️⃣  Android mipmap icons...")
    mipmap_sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }

    app_res = Path("/home/neko/ещвщ/app/src/main/res")
    for folder, px in mipmap_sizes.items():
        dest_dir = app_res / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        icon = logo_clean.resize((px, px), Image.LANCZOS)
        icon.save(str(dest_dir / "ic_launcher.png"), "PNG")
        icon.save(str(dest_dir / "ic_launcher_round.png"), "PNG")
        print(f"   ✅ {folder}/ic_launcher.png ({px}×{px})")

    # 4. Adaptive icon layers
    print("\n4️⃣  Adaptive icon layers...")
    adaptive_sizes = {
        "mipmap-mdpi": 108,
        "mipmap-hdpi": 162,
        "mipmap-xhdpi": 216,
        "mipmap-xxhdpi": 324,
        "mipmap-xxxhdpi": 432,
    }

    # Generate at high res, then scale down
    print("   Generating foreground layer...")
    fg_master = generate_adaptive_foreground(864)
    print("   Generating background layer...")
    bg_master = generate_adaptive_background(864)

    for folder, px in adaptive_sizes.items():
        dest_dir = app_res / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        fg = fg_master.resize((px, px), Image.LANCZOS)
        bg = bg_master.resize((px, px), Image.LANCZOS)
        fg.save(str(dest_dir / "ic_launcher_foreground.png"), "PNG")
        bg.save(str(dest_dir / "ic_launcher_background.png"), "PNG")
        print(f"   ✅ {folder}/ic_launcher_foreground.png ({px}×{px})")

    # 5. Save to drawable-nodpi (replace old logo)
    print("\n5️⃣  Replacing old logo.png...")
    nodpi = app_res / "drawable-nodpi"
    nodpi.mkdir(parents=True, exist_ok=True)
    # High res for nodpi
    logo_nodpi = logo_clean.resize((512, 512), Image.LANCZOS)
    logo_nodpi.save(str(nodpi / "logo.png"), "PNG")
    print(f"   ✅ drawable-nodpi/logo.png (512×512)")

    # 6. Generate web favicon sizes
    print("\n6️⃣  Web favicons...")
    for sz in [16, 32, 48, 64, 180, 192, 512]:
        ico = logo_clean.resize((sz, sz), Image.LANCZOS)
        ico.save(str(LOGO_DIR / f"favicon_{sz}.png"), "PNG")
    print(f"   ✅ favicons: 16-512px")

    print("\n" + "=" * 50)
    print("✅ LOGO GENERATION COMPLETE!")
    print(f"📁 Logo files: {LOGO_DIR}")
    print(f"📱 Android icons: {app_res}")
    print("=" * 50)


if __name__ == "__main__":
    main()
