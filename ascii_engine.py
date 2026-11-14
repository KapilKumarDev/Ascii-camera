from functools import lru_cache

import cv2
import numpy as np
import pygame

CHAR_ASPECT = 0.55  # monospace glyph width / height
FONTS = "dejavusansmono,couriernew,menlo,consolas,monospace"

# Character ramps ordered from dark to bright
RAMPS = [
    {"name": "CLASSIC", "chars": " .:-=+*#%@"},
    {"name": "EXTENDED", "chars": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"},
    {"name": "MATRIX", "chars": " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    {"name": "BLOCKS", "chars": " ░▒▓█"},
    {"name": "BINARY", "chars": " 01"},
]


def process_frame(frame, cols, brightness, invert, ramp_idx):
    """
    Downsamples a BGR frame to a grid of ramp indices.
    Returns (indices, rgb_colors), both shaped (rows, cols[, 3]).
    """
    h, w = frame.shape[:2]
    rows = max(1, int(h / w * cols * CHAR_ASPECT))
    resized = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32)
    adjusted = np.clip(gray + brightness, 0, 255)
    if invert:
        adjusted = 255 - adjusted

    # 256 equal bins, so every ramp char (incl. the last) gets its share
    indices = (adjusted * len(RAMPS[ramp_idx]["chars"]) / 256).astype(np.int32)
    return indices, cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)


def cell_size(rows, cols, win_w, win_h):
    """Largest integer glyph cell (w, h) that keeps CHAR_ASPECT and fits the window."""
    cw = max(1, min(win_w // cols, int(win_h * CHAR_ASPECT / rows)))
    return cw, max(1, int(cw / CHAR_ASPECT))


@lru_cache(maxsize=8)
def build_atlas(ramp_idx, cw, ch):
    """Glyph coverage masks (n_chars, ch, cw) in 0..1. Needs pygame.font initialised."""
    font = pygame.font.SysFont(FONTS, ch * 2)  # render big, scale down: crisper
    glyphs = []
    for c in RAMPS[ramp_idx]["chars"]:
        glyph = pygame.transform.smoothscale(font.render(c, True, "white"), (cw, ch))
        glyphs.append(pygame.surfarray.array_alpha(glyph).T)
    return np.stack(glyphs).astype(np.float32) / 255


def compose(indices, rgb, atlas, bg, fg):
    """Paint the whole grid at once. fg=None means use each source pixel's colour."""
    rows, cols = indices.shape
    ch, cw = atlas.shape[1:]
    color = rgb[:, :, None, None] if fg is None else np.array(fg, np.float32)
    bg = np.array(bg, np.float32)
    img = bg + (color - bg) * atlas[indices][..., None]  # rows, cols, ch, cw, 3
    return img.astype(np.uint8).transpose(0, 2, 1, 3, 4).reshape(rows * ch, cols * cw, 3)