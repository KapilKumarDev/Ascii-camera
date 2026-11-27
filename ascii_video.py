"""Real-time video -> ASCII. Webcam or file. Keys: see HELP."""
import sys

import cv2
import numpy as np

# Size in pixels of one character cell in the output window.
# 8x12 matches the usual "characters are taller than wide" shape of text.
TILE_W, TILE_H = 8, 12

# Pixel coordinates inside one tile, used to build the block characters below.
YY, XX = np.mgrid[:TILE_H, :TILE_W]

# cv2.putText only has Hershey fonts (ASCII only), so block characters cannot be
# drawn with it. They are built as dither patterns instead, like a terminal draws them.
SHADES = {
    "█": np.ones((TILE_H, TILE_W), bool),  # 100% ink
    "▓": (XX % 2 == 1) | (YY % 2 == 1),    # 75% ink
    "▒": (XX + YY) % 2 == 0,               # 50% ink (checkerboard)
    "░": (XX % 2 == 0) & (YY % 2 == 0),    # 25% ink
}

# Character sets only: chars get sorted by measured ink, so order here is irrelevant.
RAMPS = {
    "1": " .:-=+*#%@",
    "2": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "3": " .oO0@",
    "4": " █▓▒░",
    "5": " #",
}

BLACK = (0, 0, 0)
# Colour schemes as BGR (OpenCV order). fg = colour of the text, bg = colour behind it.
# bg may be left out and then defaults to BLACK. None means "colour from the source video".
COLORS = {
    "q": {"fg": (255, 255, 255)},  # white
    "w": {"fg": (0, 255, 0)},      # green
    "e": {"fg": (0, 191, 255)},    # amber
    "r": {"fg": None},             # real colour
}
ESC = "\x1b"  # the Esc key as returned by waitKey
HELP = "1-5 ramp | q white  w green  e amber  r real colour | c contrast | [ ] stability | i invert | Esc quit"

# CLAHE = local contrast boost. Each region of the image gets its own contrast
# stretch, so flat, dim webcam video uses the whole range of characters.
# clipLimit caps the boost (higher = harsher, more noise); tileGridSize is the
# number of regions across and down.
CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
# Smallest brightness spread (out of 255) that stretch() will magnify to full range.
MIN_SPAN = 32


def glyph(ch):
    """Draw one character into a TILE_H x TILE_W grayscale tile (0 = background, 255 = ink)."""
    if ch in SHADES:  # block characters: putText cannot draw them
        return SHADES[ch].astype(np.uint8) * 255
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


def stretch(gray):
    """Rescale brightness so the dimmest cells hit 0 and the brightest hit 255.

    Real video never spans the full 0..255 range (a dim room sits around 25..110),
    so without this the blank and the densest characters almost never appear.
    The 2nd and 98th percentiles are used instead of min and max so that one
    stray pixel cannot squash the whole range.
    """
    lo, hi = np.percentile(gray, (2, 98))
    hi = max(hi, lo + MIN_SPAN)  # near-flat frame (lens cap): do not blow noise up to full range
    return np.clip((gray.astype(np.float32) - lo) * 255 / (hi - lo), 0, 255).astype(np.uint8)


def settle(gray, held, threshold):
    """Keep each cell's previous value unless it moved by more than threshold.

    Sensor noise moves a cell by a few levels every frame. Holding the old value
    stops static areas (background) from flickering between neighbouring characters.
    """
    if held is None or held.shape != gray.shape:  # first frame, or grid size changed
        return gray
    moved = np.abs(gray.astype(np.int16) - held) > threshold  # int16: uint8 would wrap on subtract
    return np.where(moved, gray, held)


def layer(spec, small):
    """Colour layer (uint16) for one colour spec, ready to blend with the ink mask.

    spec  -- a BGR tuple, or None to use the video's own colours
    small -- the shrunken frame, one pixel per character cell
    """
    if spec is None:
        # Blow each cell colour up to the size of a tile (nearest = no blending).
        return cv2.resize(small, None, fx=TILE_W, fy=TILE_H, interpolation=cv2.INTER_NEAREST).astype(np.uint16)
    return np.array(spec, np.uint16)  # one colour: broadcasts over the whole image, no big array needed


def render(frame, tiles, color, cols, invert=False, enhance=False, held=None, threshold=0):
    """Turn one BGR video frame into (ASCII-art BGR image, gray values used).

    frame  -- BGR frame from OpenCV
    tiles  -- glyph tiles from atlas(), dark -> bright
    color  -- dict with "fg" (text colour) and optional "bg" (default BLACK); None = video colour
    cols   -- number of characters per row
    invert -- swap dark and bright
    enhance -- boost contrast (CLAHE, then stretch to the full range) before choosing characters
    held -- gray values returned by the previous call (None on the first frame)
    threshold -- a cell keeps its held value until it changes by more than this
    """
    h, w = frame.shape[:2]
    # Rows are fewer than cols * h / w because each cell is taller than it is wide.
    rows = max(1, int(cols * h / w * TILE_W / TILE_H))
    # Shrink the frame to one pixel per character cell. INTER_AREA averages pixels,
    # which is the right filter for shrinking.
    small = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    if enhance:  # applied on the small image: cheap, and it directly changes what gets mapped
        gray = stretch(CLAHE.apply(gray))  # local contrast first, then use the full 0..255 range
    if invert:
        gray = 255 - gray
    gray = settle(gray, held, threshold)  # last step before mapping: stabilise what picks the characters
    # Map brightness 0..255 to a tile index 0..n-1 in n equal buckets.
    # Dividing by 256 (not 255) keeps the last character reachable by a whole
    # bucket of brightness values, not only by pure white.
    idx = gray.astype(np.intp) * len(tiles) // 256
    # Look up a tile for every cell: shape (rows, cols, TILE_H, TILE_W).
    mask = tiles[idx]
    # Move the pixel rows next to the cell rows, then merge into one big image:
    # (rows, TILE_H, cols, TILE_W) -> (rows * TILE_H, cols * TILE_W).
    mask = mask.transpose(0, 2, 1, 3).reshape(rows * TILE_H, cols * TILE_W)
    ink = mask[..., None].astype(np.uint16)  # 0 = pure background, 255 = pure text colour
    fg = layer(color["fg"], small)
    bg = layer(color.get("bg", BLACK), small)
    # Blend per pixel: ink picks how much text colour vs background colour.
    # uint16 is enough: bg*(255-ink) + fg*ink never exceeds 255*255.
    image = ((bg * (255 - ink) + fg * ink) // 255).astype(np.uint8)
    return image, gray  # gray goes back in as `held` on the next frame


def main(source="0", cols=120):
    """Open the source, then render and show frames until Esc is pressed."""
    is_file = not source.isdigit()  # "0", "1" = webcam index; anything else = file path
    cap = cv2.VideoCapture(source if is_file else int(source))
    atlases = {k: atlas(r) for k, r in RAMPS.items()}  # build every ramp once, up front
    # start: ramp 1, green on black, not inverted, contrast boost on
    ramp, color, invert, enhance = "1", COLORS["w"], False, True
    held, threshold = None, 10  # previous frame's gray values; stability (0 = off)
    print(HELP)
    while True:
        ok, frame = cap.read()
        if not ok and is_file:  # video file ended: jump back to frame 0 and loop
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok:  # webcam failed, or file is unreadable
            sys.exit(f"cannot read video source: {source}")
        image, held = render(frame, atlases[ramp], color, cols, invert, enhance, held, threshold)
        cv2.imshow("ascii", image)
        # waitKey(1) = wait 1 ms for a key; returns -1 if none (& 0xFF turns that into 255).
        key = chr(cv2.waitKey(1) & 0xFF)
        if key == ESC:
            break
        if key in RAMPS:  # 1-5: switch character ramp
            ramp = key
        elif key in COLORS:  # q w e r: switch colour scheme
            color = COLORS[key]
        elif key == "i":  # i: toggle invert
            invert = not invert
        elif key == "c":  # c: toggle contrast boost
            enhance = not enhance
        elif key in "[]":  # [ ]: less / more stability
            threshold = max(0, threshold + (2 if key == "]" else -2))
            print(f"stability threshold: {threshold}")
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Usage: python ascii_video.py [source] [columns]   (defaults: webcam 0, 120 columns)
    src, *rest = sys.argv[1:] or ["0"]
    main(src, int(rest[0]) if rest else 120)