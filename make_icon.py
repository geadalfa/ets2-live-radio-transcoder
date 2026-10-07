import os
from PIL import Image, ImageDraw

out_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(out_dir, "radio_tray_icon.png")
ico_path = os.path.join(out_dir, "radio_tray_icon.ico")

size = (64, 64)
img = Image.new("RGBA", size, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background rounded square / badge with modern ETS2 dark orange / cyber blue style
# Dark slate rounded rect
draw.rounded_rectangle([2, 2, 62, 62], radius=14, fill=(24, 28, 36, 255), outline=(230, 110, 20, 255), width=2)

# Radio speaker / grill circles
# Antenna
draw.line([16, 16, 24, 26], fill=(230, 110, 20, 255), width=3)
draw.ellipse([14, 14, 18, 18], fill=(255, 140, 0, 255))

# Radio body inside
draw.rounded_rectangle([12, 26, 52, 52], radius=6, fill=(35, 42, 54, 255), outline=(60, 70, 90, 255), width=2)

# Speaker mesh circle
draw.ellipse([16, 30, 36, 50], fill=(15, 18, 24, 255), outline=(230, 110, 20, 255), width=2)
draw.ellipse([23, 37, 29, 43], fill=(255, 120, 0, 255))

# Radio dial / buttons on right
draw.rectangle([40, 32, 48, 35], fill=(80, 160, 255, 255))
draw.rectangle([40, 38, 48, 41], fill=(200, 200, 200, 255))
draw.rectangle([40, 44, 48, 47], fill=(200, 200, 200, 255))

img.save(png_path, "PNG")

# Also save ICO multi-resolution (64, 32, 16)
img.save(ico_path, format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])

print(f"Created icon at:\n - {png_path}\n - {ico_path}")
