"""Run from project root: python -m tests.test_ascii_engine"""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import numpy as np
import pygame

import ascii_engine as ae

pygame.font.init()
white = np.full((72, 128, 3), 255, np.uint8)
black = np.zeros_like(white)

for i, ramp in enumerate(ae.RAMPS):
    n = len(ramp["chars"])
    assert ae.process_frame(white, 10, 0, False, i, False)[0].max() == n - 1, ramp["name"]
    assert ae.process_frame(black, 10, 0, False, i, False)[0].max() == 0, ramp["name"]

idx, rgb = ae.process_frame(white, 300, 0, False, 1, False)
rows, cols = idx.shape
cw, ch = ae.cell_size(rows, cols, 1280, 720)
assert cols * cw <= 1280 and rows * ch <= 720

img = ae.compose(idx, rgb, ae.build_atlas(1, cw, ch), (5, 10, 5), (0, 255, 65))
assert img.shape == (rows * ch, cols * cw, 3)
assert img[..., 1].max() > 100  # glyphs actually drawn
assert img[..., 0].max() <= 5  # fg red is 0, so red only fades from bg

# Edges: flat frames have none; each edge angle maps to its matching char
assert not ae.detect_edges(white, 80, 25)[0].any()
assert not ae.detect_edges(black, 80, 25)[0].any()

H, W = 360, 640
yy, xx = np.mgrid[0:H, 0:W]
shapes = {  # half-planes: bright side puts the edge along that line
    "|": xx > W // 2,
    "-": yy > H // 2,
    "/": (xx + yy * W / H) > W,  # edge runs bottom-left to top-right
    "\\": (xx - yy * W / H) > 0,  # edge runs top-left to bottom-right
}
for char, bright in shapes.items():
    frame = np.repeat((bright * 255).astype(np.uint8)[..., None], 3, axis=2)
    is_edge, direction = ae.detect_edges(frame, 80, 22)
    assert is_edge.any(), char
    assert (direction[is_edge] == ae.EDGE_CHARS.index(char)).all(), char

# process_frame puts edge chars after the ramp; atlas has a glyph for each
indices, _ = ae.process_frame(frame, 80, 0, False, 0, True)
n = len(ae.RAMPS[0]["chars"])
assert indices.max() >= n and indices.max() < n + len(ae.EDGE_CHARS)
assert ae.build_atlas(0, 4, 7).shape[0] == n + len(ae.EDGE_CHARS)
print("ok")