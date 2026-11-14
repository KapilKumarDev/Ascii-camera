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
    assert ae.process_frame(white, 10, 0, False, i)[0].max() == n - 1, ramp["name"]
    assert ae.process_frame(black, 10, 0, False, i)[0].max() == 0, ramp["name"]

idx, rgb = ae.process_frame(white, 300, 0, False, 1)
rows, cols = idx.shape
cw, ch = ae.cell_size(rows, cols, 1280, 720)
assert cols * cw <= 1280 and rows * ch <= 720

img = ae.compose(idx, rgb, ae.build_atlas(1, cw, ch), (5, 10, 5), (0, 255, 65))
assert img.shape == (rows * ch, cols * cw, 3)
assert img[..., 1].max() > 100  # glyphs actually drawn
assert img[..., 0].max() <= 5  # fg red is 0, so red only fades from bg
print("ok")