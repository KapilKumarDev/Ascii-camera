from functools import lru_cache

import cv2
import numpy as np
import pygame

CHAR_ASPECT = 0.55  # monospace glyph width / height
FONTS = "dejavusansmono,couriernew,menlo,consolas,monospace"
EDGE_CHARS = "|/-\\"  # indexed by edge angle: 0, 45, 90, 135 degrees
EDGE_OVERSAMPLE = 4  # edge-detector pixels per cell column
EDGE_STRENGTH = 2  # scales the Canny thresholds; higher = only stronger edges
MIN_SPAN = 32  # brightness spread below this is a flat frame, not a dull one: leave it alone

# Character sets per ramp; build_atlas orders them by measured ink, so listed order is free
RAMPS = [
    {"name": "CLASSIC", "chars": " .:-=+*#%@"},
    {"name": "EXTENDED", "chars": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"},
    {"name": "MATRIX", "chars": " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    {"name": "BLOCKS", "chars": " ░▒▓█"},
    {"name": "BINARY", "chars": " 01"},
]


def detect_edges(frame, cols, rows):
    """
    Canny edges plus Sobel gradient angle, pooled per cell. Pure OpenCV, no model.
    Returns (is_edge, direction): direction indexes EDGE_CHARS.
    """
    w = cols * EDGE_OVERSAMPLE
    h = int(rows * EDGE_OVERSAMPLE / CHAR_ASPECT)  # same aspect as the source, so angles stay true
    gray = cv2.cvtColor(cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Auto thresholds from the Otsu level (high) and half of it (low), scaled up
    # because Sobel gain is ~4x intensity and plain Otsu also keeps hair/fabric texture
    high = EDGE_STRENGTH * cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    edge = (cv2.Canny(gray, high / 2, high) > 0).astype(np.float32)

    def pool(a):
        return cv2.resize(a, (cols, rows), interpolation=cv2.INTER_AREA)

    # Dominant gradient angle per cell from the structure tensor (edge pixels only)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    sxx, syy, sxy = pool(edge * gx * gx), pool(edge * gy * gy), pool(edge * gx * gy)
    angle = np.degrees(0.5 * np.arctan2(2 * sxy, sxx - syy)) % 180
    direction = np.round(angle / 45).astype(np.int32) % 4

    # A straight edge fills at least 1 pixel per cell row, so require that much
    return pool(edge) >= rows / h, direction


def autolevel(frame):
    """Stretch the 2nd..98th brightness percentile to 0..255 so dull webcam frames use the whole ramp."""
    lo, hi = np.percentile(cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA), (2, 98))
    if hi - lo < MIN_SPAN:
        return frame
    gain = 255 / (hi - lo)
    return cv2.convertScaleAbs(frame, alpha=gain, beta=-lo * gain)


def process_frame(frame, cols, brightness, invert, ramp_idx, edges):
    """
    Downsamples a BGR frame to a grid of char indices. Edge cells (if enabled) use
    EDGE_CHARS, which sit right after the ramp in the glyph atlas.
    Returns (indices, rgb_colors), both shaped (rows, cols[, 3]).
    """
    frame = autolevel(frame)
    h, w = frame.shape[:2]
    rows = max(1, int(h / w * cols * CHAR_ASPECT))
    resized = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32)
    adjusted = np.clip(gray + brightness, 0, 255)
    if invert:
        adjusted = 255 - adjusted

    # 256 equal bins, so every ramp char (incl. the last) gets its share
    n = len(RAMPS[ramp_idx]["chars"])
    indices = (adjusted * n / 256).astype(np.int32)

    if edges:
        is_edge, direction = detect_edges(frame, cols, rows)
        indices = np.where(is_edge, n + direction, indices)

    return indices, cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)


def cell_size(rows, cols, win_w, win_h):
    """Largest integer glyph cell (w, h) that keeps CHAR_ASPECT and fits the window."""
    cw = max(1, min(win_w // cols, int(win_h * CHAR_ASPECT / rows)))
    return cw, max(1, int(cw / CHAR_ASPECT))


@lru_cache(maxsize=8)
def build_atlas(ramp_idx, cw, ch):
    """
    Glyph coverage masks (ramp + edge chars, ch, cw) in 0..1. Needs pygame.font initialised.
    Ramp rows are ordered by measured ink, not by guess: level k gets the glyph whose ink is closest
    to the k-th of n evenly spaced targets, so brightness maps to darkness linearly in any font.
    """
    font = pygame.font.SysFont(FONTS, ch * 2)  # render big, scale down: crisper
    glyphs = []
    for c in RAMPS[ramp_idx]["chars"] + EDGE_CHARS:
        glyph = pygame.transform.smoothscale(font.render(c, True, "white"), (cw, ch))
        glyphs.append(pygame.surfarray.array_alpha(glyph).T)
    atlas = np.stack(glyphs).astype(np.float32) / 255
    n = len(RAMPS[ramp_idx]["chars"])
    ink = atlas[:n].mean((1, 2))
    target = np.linspace(ink.min(), ink.max(), n)
    atlas[:n] = atlas[:n][np.abs(ink - target[:, None]).argmin(1)]
    return atlas


def compose(indices, rgb, atlas, bg, fg):
    """Paint the whole grid at once. fg=None means use each source pixel's colour."""
    rows, cols = indices.shape
    ch, cw = atlas.shape[1:]
    color = rgb[:, :, None, None] if fg is None else np.array(fg, np.float32)
    bg = np.array(bg, np.float32)
    img = bg + (color - bg) * atlas[indices][..., None]  # rows, cols, ch, cw, 3
    return img.astype(np.uint8).transpose(0, 2, 1, 3, 4).reshape(rows * ch, cols * cw, 3)