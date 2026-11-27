import numpy as np

from ascii_video import RAMPS, TILE_H, TILE_W, atlas, render


def test_render():
    dark, bright = np.zeros((90, 160, 3), np.uint8), np.full((90, 160, 3), 255, np.uint8)
    t = atlas(RAMPS["1"])
    d, b = render(dark, t, (0, 255, 0), 40), render(bright, t, (0, 255, 0), 40)
    assert d.shape == b.shape == (int(40 * 90 / 160 * TILE_W / TILE_H) * TILE_H, 40 * TILE_W, 3)
    assert d.sum() < b.sum()                      # brighter frame -> denser glyphs
    assert b[..., 0].max() == 0 and b[..., 1].max() > 0   # green tint: only G channel lit
    assert render(bright, t, None, 40).sum() > 0  # source-colour mode
    assert render(bright, t, (0, 255, 0), 40, invert=True).sum() < b.sum()


def test_every_char_used():
    # 256 columns, one per brightness level 0..255, one cell per column.
    row = np.arange(256, dtype=np.uint8)
    frame = np.dstack([np.tile(row, (256, 1))] * 3)
    for ramp in RAMPS.values():
        t = atlas(ramp)
        out = render(frame, t, (255, 255, 255), 256)[..., 0]
        # Take the top row of cells and count how many columns use each glyph.
        cells = out[:TILE_H].reshape(TILE_H, 256, TILE_W).transpose(1, 0, 2)
        used = {c.tobytes() for c in cells}
        assert len(used) == len(t)  # every character appears, last one included
        # Last char owns about 1/n of the brightness range, not just pure white.
        last = sum(c.tobytes() == t[-1].tobytes() for c in cells)
        assert last >= 256 // len(t) - 1


if __name__ == "__main__":
    test_render()
    test_every_char_used()
    print("ok")