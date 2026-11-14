"""Run from project root: python -m tests.test_ascii_engine"""
import os
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"

import cv2
import numpy as np
import pygame

import ascii_engine as ae
import camera
import export
from filters import PALETTES

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

# Dull frame (grey 100..160 only) must still span the whole ramp, flat frame must not be stretched
dull = np.tile(np.linspace(100, 160, 128).astype(np.uint8)[None, :, None], (72, 1, 3))
idx = ae.process_frame(dull, 10, 0, False, 0, False)[0]
assert idx.min() == 0 and idx.max() == len(ae.RAMPS[0]["chars"]) - 1
assert (ae.autolevel(white) == white).all()

# Ramp rows are ordered by measured ink in every ramp: brighter level never has less ink, level 0 is blank
for i, ramp in enumerate(ae.RAMPS):
    ink = ae.build_atlas(i, 10, 18)[: len(ramp["chars"])].mean((1, 2))
    assert (np.diff(ink) >= 0).all() and ink[0] == 0, ramp["name"]

# Import/export: image and video files open as sources; save() writes a PNG / an MP4 of the rendered output
pygame.display.init()  # video export reports progress in the window caption


def render(f):
    return ae.render_frame(f, 40, 0, False, 0, True, PALETTES[0], 320, 180)


assert render(dull).shape[0] <= 180 and render(dull).shape[1] <= 320

cwd = os.getcwd()
with tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)

    cv2.imwrite("pic.png", dull)
    cam = camera.open_file("pic.png")
    assert cam["kind"] == "image" and camera.get_frame(cam).shape == dull.shape
    png = export.save(cam, camera.get_frame(cam), render).removeprefix("Saved ")
    assert cv2.imread(png).shape == render(dull).shape

    writer = cv2.VideoWriter("clip.avi", cv2.VideoWriter_fourcc(*"MJPG"), 10, (128, 72))
    for k in range(5):
        writer.write(np.roll(dull, k * 10, axis=1))
    writer.release()
    cam = camera.open_file("clip.avi")
    assert cam["kind"] == "video" and camera.get_frame(cam).shape == dull.shape
    mp4 = export.save(cam, None, render).removeprefix("Saved ")
    out = cv2.VideoCapture(mp4)
    assert int(out.get(cv2.CAP_PROP_FRAME_COUNT)) == 5
    out.release()
    camera.release_camera(cam)

    assert camera.open_file("missing.png") is None
    os.chdir(cwd)

print("ok")