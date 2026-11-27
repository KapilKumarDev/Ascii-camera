"""Real-time video -> ASCII. Webcam or file. Keys: see HELP."""
import sys

import cv2
import numpy as np

# Size in pixels of one character cell in the output window.
# 8x12 matches the usual "characters are taller than wide" shape of text.
TILE_W, TILE_H = 8, 12

# Character sets only: chars get sorted by measured ink, so order here is irrelevant.
RAMPS = {
    "1": " .:-=+*#%@",
    "2": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "3": " .oO0@",
    "4": " #",
}
# Text colours as BGR (OpenCV order). None means "use the colour of the source video".
COLORS = {
    "z": (255, 255, 255),
    "x": (0, 255, 0),
    "c": (0, 191, 255),
    "v": None,
}
HELP = "1-4 ramp | z white  x green  c amber  v source colour | i invert | q quit"


def glyph(ch):
    """Draw one character into a TILE_H x TILE_W grayscale tile (0 = background, 255 = ink)."""
    tile = np.zeros((TILE_H, TILE_W), np.uint8)  # black tile
    # Baseline sits 3px above the bottom so letters like g, y, p are not cut off.
    cv2.putText(tile, ch, (0, TILE_H - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.35, 255, 1, cv2.LINE_AA)
    return tile


def atlas(chars):
    """Build all tiles for a character set, sorted dark -> bright by real ink amount.

    Sorting by measured ink means the ramp order is always correct, whatever font
    or character set is used.
    """
    tiles = np.stack([glyph(c) for c in chars])  # shape: (n_chars, TILE_H, TILE_W)
    return tiles[np.argsort(tiles.sum((1, 2)), kind="stable")]  # least ink first


def render(frame, tiles, color, cols, invert=False):
    """Turn one BGR video frame into an ASCII-art BGR image.

    frame  -- BGR frame from OpenCV
    tiles  -- glyph tiles from atlas(), dark -> bright
    color  -- BGR tuple for the text, or None to take colours from the frame
    cols   -- number of characters per row
    invert -- swap dark and bright
    """
    h, w = frame.shape[:2]
    # Rows are fewer than cols * h / w because each cell is taller than it is wide.
    rows = max(1, int(cols * h / w * TILE_W / TILE_H))
    # Shrink the frame to one pixel per character cell. INTER_AREA averages pixels,
    # which is the right filter for shrinking.
    small = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    if invert:
        gray = 255 - gray
    # Map brightness 0..255 to a tile index 0..n-1 in n equal buckets.
    # Dividing by 256 (not 255) keeps the last character reachable by a whole
    # bucket of brightness values, not only by pure white.
    idx = gray.astype(np.intp) * len(tiles) // 256
    # Look up a tile for every cell: shape (rows, cols, TILE_H, TILE_W).
    mask = tiles[idx]
    # Move the pixel rows next to the cell rows, then merge into one big image:
    # (rows, TILE_H, cols, TILE_W) -> (rows * TILE_H, cols * TILE_W).
    mask = mask.transpose(0, 2, 1, 3).reshape(rows * TILE_H, cols * TILE_W)
    # Colour of each cell: one fixed colour, or the shrunken frame's own colour.
    tint = small if color is None else np.full_like(small, color)
    # Blow each cell colour up to the size of a tile (nearest = no blending).
    tint = cv2.resize(tint, None, fx=TILE_W, fy=TILE_H, interpolation=cv2.INTER_NEAREST)
    # Ink strength (0..255) scales the colour. uint16 avoids overflow in the multiply.
    return (mask[..., None].astype(np.uint16) * tint // 255).astype(np.uint8)


def main(source="0", cols=120):
    """Open the source, then render and show frames until q is pressed."""
    is_file = not source.isdigit()  # "0", "1" = webcam index; anything else = file path
    cap = cv2.VideoCapture(source if is_file else int(source))
    atlases = {k: atlas(r) for k, r in RAMPS.items()}  # build every ramp once, up front
    ramp, color, invert = "1", COLORS["x"], False  # start: ramp 1, green, not inverted
    print(HELP)
    while True:
        ok, frame = cap.read()
        if not ok and is_file:  # video file ended: jump back to frame 0 and loop
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok:  # webcam failed, or file is unreadable
            sys.exit(f"cannot read video source: {source}")
        cv2.imshow("ascii", render(frame, atlases[ramp], color, cols, invert))
        # waitKey(1) = wait 1 ms for a key; returns -1 if none (& 0xFF turns that into 255).
        key = chr(cv2.waitKey(1) & 0xFF)
        if key == "q":
            break
        if key in RAMPS:  # 1-4: switch character ramp
            ramp = key
        elif key in COLORS:  # z x c v: switch colour
            color = COLORS[key]
        elif key == "i":  # i: toggle invert
            invert = not invert
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Usage: python ascii_video.py [source] [columns]   (defaults: webcam 0, 120 columns)
    src, *rest = sys.argv[1:] or ["0"]
    main(src, int(rest[0]) if rest else 120)