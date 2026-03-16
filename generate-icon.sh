#!/bin/bash
#
# Generate macOS app icon (.icns) — modern style
# Blue gradient rounded square with refresh arrows + "TV" text
#

ICONSET="AppIcon.iconset"
rm -rf "$ICONSET" AppIcon.icns
mkdir -p "$ICONSET"

python3 << 'PYEOF'
import struct, zlib, os, math, shutil

def create_icon(size, filename):
    """Modern macOS-style icon: blue gradient rounded rect with TV + refresh symbol."""
    pixels = []
    cx, cy = size / 2, size / 2
    # macOS icon has ~80% fill with rounded corners
    rect_r = size * 0.40
    corner = size * 0.18
    shadow_off = size * 0.008

    for y in range(size):
        row = []
        for x in range(size):
            # Check rounded rectangle
            def in_rrect(px, py, cr_x, cr_y):
                dx = abs(px - cr_x)
                dy = abs(py - cr_y)
                if dx <= rect_r and dy <= rect_r:
                    ex = max(0, dx - (rect_r - corner))
                    ey = max(0, dy - (rect_r - corner))
                    return ex * ex + ey * ey <= corner * corner
                return False

            in_shape = in_rrect(x, y, cx, cy)
            in_shadow = in_rrect(x, y - shadow_off * 2, cx, cy)

            if in_shape:
                # Gradient: top=#1a6dff → bottom=#0040aa
                t = (y - (cy - rect_r)) / (2 * rect_r)
                t = max(0, min(1, t))
                r = int(26 + (0 - 26) * t)
                g = int(109 + (64 - 109) * t)
                b = int(255 + (170 - 255) * t)
                a = 255

                # Subtle inner glow at top
                if t < 0.15:
                    glow = 1 - t / 0.15
                    r = min(255, int(r + 60 * glow))
                    g = min(255, int(g + 60 * glow))
                    b = min(255, int(b + 30 * glow))

                # Draw "TV" text
                s = size / 128  # scale factor
                nx = (x - cx) / s
                ny = (y - cy) / s

                is_text = False
                lw = 4.5  # line width

                # "T" — left side
                # Top bar
                if -28 <= nx <= -6 and -18 <= ny <= -18 + lw:
                    is_text = True
                # Vertical stem
                if -17 - lw/2 <= nx <= -17 + lw/2 and -18 <= ny <= 14:
                    is_text = True

                # "V" — right side
                if 4 <= nx <= 28 and -18 <= ny <= 14:
                    # Left diagonal of V
                    expected_x = 8 + (ny + 18) * (-4/32) * (-1)
                    # V goes from (8,-18) and (24,-18) meeting at (16,14)
                    left_x = 8 + (ny + 18) * (16 - 8) / (14 + 18)
                    right_x = 24 + (ny + 18) * (16 - 24) / (14 + 18)
                    if abs(nx - left_x) < lw or abs(nx - right_x) < lw:
                        is_text = True

                # Refresh arrow (circular) — bottom right area
                arrow_cx = 28 * s + cx
                arrow_cy = 28 * s + cy
                arrow_r = 12 * s
                arrow_w = 2.8 * s
                dist = math.sqrt((x - arrow_cx)**2 + (y - arrow_cy)**2)
                angle = math.atan2(y - arrow_cy, x - arrow_cx)

                # Draw arc (270 degrees, gap at top-right)
                if arrow_r - arrow_w < dist < arrow_r + arrow_w:
                    # Arc from 45° to 315° (270° arc)
                    a_deg = math.degrees(angle) % 360
                    if 30 < a_deg < 330:
                        is_text = True

                # Arrowhead at the end of arc (~330°)
                ah_angle = math.radians(330)
                ah_x = arrow_cx + arrow_r * math.cos(ah_angle)
                ah_y = arrow_cy + arrow_r * math.sin(ah_angle)
                # Triangle arrowhead
                dx_a = x - ah_x
                dy_a = y - ah_y
                if abs(dx_a) < 6 * s and abs(dy_a) < 6 * s:
                    # Simple triangle pointing clockwise
                    rot_x = dx_a * math.cos(-ah_angle) - dy_a * math.sin(-ah_angle)
                    rot_y = dx_a * math.sin(-ah_angle) + dy_a * math.cos(-ah_angle)
                    if rot_x > -5*s and abs(rot_y) < (5*s - rot_x) * 0.7:
                        is_text = True

                if is_text:
                    r, g, b = 255, 255, 255

                row.extend([r, g, b, a])
            elif in_shadow and not in_shape:
                row.extend([0, 0, 0, 25])
            else:
                row.extend([0, 0, 0, 0])

        pixels.append(bytes(row))

    write_png(filename, size, size, pixels)


def write_png(filename, width, height, rows):
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''
    for row in rows:
        raw += b'\x00' + row
    with open(filename, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)))
        f.write(chunk(b'IDAT', zlib.compress(raw, 9)))
        f.write(chunk(b'IEND', b''))


iconset = "AppIcon.iconset"
for s in [16, 32, 64, 128, 256, 512, 1024]:
    print(f"  {s}x{s}...", end=" ", flush=True)
    create_icon(s, f"{iconset}/icon_{s}x{s}.png")
    print("ok")

# @2x variants
for small, big in [(16,32), (32,64), (128,256), (256,512), (512,1024)]:
    src = f"{iconset}/icon_{big}x{big}.png"
    dst = f"{iconset}/icon_{small}x{small}@2x.png"
    if os.path.exists(src):
        shutil.copy2(src, dst)

print("  PNGs ready.")
PYEOF

# Convert to icns
if [ -d "$ICONSET" ]; then
    iconutil -c icns "$ICONSET" -o AppIcon.icns 2>/dev/null
    if [ -f "AppIcon.icns" ]; then
        echo "✅ AppIcon.icns created"
    else
        echo "⚠ Fallback: using sips"
        sips -s format icns "$ICONSET/icon_256x256.png" --out AppIcon.icns 2>/dev/null || true
    fi
    rm -rf "$ICONSET"
fi
