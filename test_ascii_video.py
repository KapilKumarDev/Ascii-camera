"""Runnable checks for ascii_video. Run: python test_ascii_video.py"""
import numpy as np

from ascii_video import RAMPS, TILE_H, TILE_W, atlas, render

WHITE = {"fg": (255, 255, 255)}  # bg left out: defaults to black


def cells_of(out, cols):
    """Split a one-channel rendered image into one TILE_H x TILE_W block per character cell."""
    rows = out.shape[0] // TILE_H
    return out.reshape(rows, TILE_H, cols, TILE_W).transpose(0, 2, 1, 3).reshape(-1, TILE_H, TILE_W)


def test_render():
    dark, bright = np.zeros((90, 160, 3), np.uint8), np.full((90, 160, 3), 255, np.uint8)
    t, green = atlas(RAMPS["1"]), {"fg": (0, 255, 0)}
    d, b = render(dark, t, green, 40)[0], render(bright, t, green, 40)[0]
    assert d.shape == b.shape == (int(40 * 90 / 160 * TILE_W / TILE_H) * TILE_H, 40 * TILE_W, 3)
    assert d.sum() < b.sum()                              # brighter frame -> denser glyphs
    assert b[..., 0].max() == 0 and b[..., 1].max() > 0   # green text: only G channel lit
    assert render(bright, t, {"fg": None}, 40)[0].sum() > 0   # real-colour mode
    assert render(bright, t, green, 40, invert=True)[0].sum() < b.sum()


def test_background():
    dark = np.zeros((90, 160, 3), np.uint8)               # all black frame -> every cell is the blank
    t = atlas(RAMPS["1"])
    assert render(dark, t, {"fg": (0, 255, 0)}, 40)[0].max() == 0     # bg defaults to black
    blue_bg = render(dark, t, {"fg": (0, 255, 0), "bg": (255, 0, 0)}, 40)[0]
    assert (blue_bg == (255, 0, 0)).all()                 # blank cells show the bg colour


def test_block_ramp():
    t = atlas(RAMPS["4"])
    assert np.allclose(t.mean((1, 2)) / 255, [0.25, 0.5, 0.75, 1.0])  # ░ ▒ ▓ █, dark -> bright


def test_every_char_used():
    # 256 columns, one per brightness level 0..255, one cell per column.
    row = np.arange(256, dtype=np.uint8)
    frame = np.dstack([np.tile(row, (256, 1))] * 3)
    for ramp in RAMPS.values():
        t = atlas(ramp)
        out = render(frame, t, WHITE, 256)[0][..., 0]  # enhance off: exact mapping
        cells = cells_of(out[:TILE_H], 256)            # top row of cells only
        assert len({c.tobytes() for c in cells}) == len(t)  # every character appears, last one included
        # Last char owns about 1/n of the brightness range, not just pure white.
        assert sum(c.tobytes() == t[-1].tobytes() for c in cells) >= 256 // len(t) - 1


def test_enhance_spreads_flat_video():
    # Flat, low-contrast frame: brightness only spans 100..139.
    row = np.linspace(100, 139, 256).astype(np.uint8)
    frame = np.dstack([np.tile(row, (256, 1))] * 3)
    t = atlas(RAMPS["2"])

    def glyphs_used(enhance):
        out = render(frame, t, WHITE, 64, enhance=enhance)[0][..., 0]
        return len({c.tobytes() for c in cells_of(out, 64)})

    assert glyphs_used(True) > glyphs_used(False)  # CLAHE uses more of the ramp


def test_hold_ignores_small_changes():
    t = atlas(RAMPS["2"])
    flat = lambda v: np.full((90, 160, 3), v, np.uint8)
    first, held = render(flat(100), t, WHITE, 40, threshold=10)
    small, held2 = render(flat(105), t, WHITE, 40, held=held, threshold=10)
    big, _ = render(flat(130), t, WHITE, 40, held=held2, threshold=10)
    assert (small == first).all()                       # change of 5 <= 10: nothing moves
    assert not (big == first).all()                     # change of 30 > 10: updates
    plain, _ = render(flat(105), t, WHITE, 40)
    assert not (plain == first).all()                   # without hold, the same 5 would change it


def test_dim_video_reaches_blank_and_last_char():
    # Dim, noisy frame: brightness only 25..110, like a webcam in a dark room.
    rng = np.random.default_rng(0)
    g = np.tile(np.linspace(25, 110, 640), (480, 1)) + rng.normal(0, 4, (480, 640))
    frame = np.dstack([np.clip(g, 0, 255).astype(np.uint8)] * 3)
    for ramp in RAMPS.values():
        t = atlas(ramp)
        out = render(frame, t, WHITE, 120, enhance=True)[0][..., 0]
        used = {c.tobytes() for c in cells_of(out, 120)}
        assert t[0].tobytes() in used and t[-1].tobytes() in used  # darkest and densest both appear


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")