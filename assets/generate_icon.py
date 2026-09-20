"""
Generate application icon and logo for FaceSoter.
"""

from pathlib import Path
from PIL import Image, ImageDraw

def create_app_icon():
    assets_dir = Path(__file__).resolve().parent
    icons_dir = assets_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    size = 256
    # Create image with smooth dark rounded background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle (Fluent Blue / Dark gradient style)
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=48,
        fill=(0, 120, 212, 255),
        outline=(25, 136, 224, 255),
        width=4,
    )

    # Inner face silhouette and sorting arrows
    # Head / face circle
    cx, cy = size // 2, size // 2 - 16
    r = 44
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))

    # Shoulders
    sx, sy = cx, cy + 86
    sr_x, sr_y = 66, 44
    draw.chord([sx - sr_x, sy - sr_y, sx + sr_x, sy + sr_y], start=180, end=0, fill=(255, 255, 255, 255))

    # Scanner / sorting grid corners (4 corner brackets representing face detection)
    bracket_margin = 40
    bw = 20
    lw = 6
    color = (255, 220, 100, 255) # Golden yellow scanner brackets

    # Top-Left
    draw.line([(bracket_margin, bracket_margin), (bracket_margin + bw, bracket_margin)], fill=color, width=lw)
    draw.line([(bracket_margin, bracket_margin), (bracket_margin, bracket_margin + bw)], fill=color, width=lw)

    # Top-Right
    draw.line([(size - bracket_margin, bracket_margin), (size - bracket_margin - bw, bracket_margin)], fill=color, width=lw)
    draw.line([(size - bracket_margin, bracket_margin), (size - bracket_margin, bracket_margin + bw)], fill=color, width=lw)

    # Bottom-Left
    draw.line([(bracket_margin, size - bracket_margin), (bracket_margin + bw, size - bracket_margin)], fill=color, width=lw)
    draw.line([(bracket_margin, size - bracket_margin), (bracket_margin, size - bracket_margin - bw)], fill=color, width=lw)

    # Bottom-Right
    draw.line([(size - bracket_margin, size - bracket_margin), (size - bracket_margin - bw, size - bracket_margin)], fill=color, width=lw)
    draw.line([(size - bracket_margin, size - bracket_margin), (size - bracket_margin, size - bracket_margin - bw)], fill=color, width=lw)

    # Save PNG
    png_path = assets_dir / "logo.png"
    img.save(png_path, "PNG")

    # Save multi-size ICO (256, 128, 64, 48, 32, 16)
    ico_path = icons_dir / "app_icon.ico"
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Generated icons:\n  {png_path}\n  {ico_path}")

if __name__ == "__main__":
    create_app_icon()
