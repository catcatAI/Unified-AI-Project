#!/bin/bash
# Create a simple PNG icon using ImageMagick or Python PIL

if command -v convert &> /dev/null; then
    # Use ImageMagick
    convert -size 32x32 xc:'#764ba2' -fill white -gravity center -pointsize 20 -annotate 0 'A' icon.png
    echo "Created icon.png using ImageMagick"
elif command -v python3 &> /dev/null; then
    # Use Python PIL
    python3 << 'PYEOF'
from PIL import Image, ImageDraw

# Create a 32x32 purple icon
img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw purple background
draw.ellipse([2, 2, 30, 30], fill=(118, 75, 162, 255))

# Save
img.save('icon.png')
print('Created icon.png using PIL')
PYEOF
else
    echo "Neither ImageMagick nor Python PIL available"
fi
