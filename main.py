import os
import sys

import pygame

import ascii_engine
import camera
import export
from ascii_engine import RAMPS
from filters import PALETTES

WINDOW_W, WINDOW_H = 1280, 720
CAPTION = "ASCII Camera Synthesizer"
RAMP_KEYS = {pygame.K_1 + i: i for i in range(len(RAMPS))}
PALETTE_KEYS = dict(zip((pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t), range(len(PALETTES))))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(CAPTION)
    clock = pygame.time.Clock()

    # Optional first argument: an image or video file to open instead of the webcam
    cam = (len(sys.argv) > 1 and camera.open_file(sys.argv[1])) or camera.init_camera(width=WINDOW_W, height=WINDOW_H)

    # Pre-build static overlays once
    crt_overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    for y in range(0, WINDOW_H, 3):
        pygame.draw.line(crt_overlay, (0, 0, 0, 70), (0, y), (WINDOW_W, y))

    hud_font = pygame.font.SysFont(ascii_engine.FONTS, 16, bold=True)
    help_font = pygame.font.SysFont(ascii_engine.FONTS, 14)
    help_surf = help_font.render(
        "[1-5]Ramps [QWERT]Color [D]Edges [I]Inv [UP/DN]Res [L/R]Brt [SPC]Pause [S]Save [C]Cam | Drop a file to import",
        True, (150, 150, 150), (20, 20, 20),
    )

    # State
    cols = 120
    brightness = 0
    invert = False
    edges = True
    ramp_idx = 0
    palette_idx = 0
    paused = False
    status = ""
    frame = camera.get_frame(cam)

    def render(f):
        return ascii_engine.render_frame(
            f, cols, brightness, invert, ramp_idx, edges, PALETTES[palette_idx], WINDOW_W, WINDOW_H)

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    if key == pygame.K_ESCAPE:
                        running = False
                    elif key == pygame.K_SPACE:  paused = not paused
                    elif key == pygame.K_i:      invert = not invert
                    elif key == pygame.K_d:      edges = not edges
                    elif key == pygame.K_s:
                        status = export.save(cam, frame, render)
                        pygame.display.set_caption(CAPTION)
                    elif key == pygame.K_c and cam["kind"] != "camera":
                        camera.release_camera(cam)
                        cam = camera.init_camera(width=WINDOW_W, height=WINDOW_H)
                        frame, status = camera.get_frame(cam), "Camera"
                    elif key == pygame.K_UP:     cols = min(cols + 10, 300)
                    elif key == pygame.K_DOWN:   cols = max(cols - 10, 30)
                    elif key == pygame.K_RIGHT:  brightness = min(brightness + 10, 100)
                    elif key == pygame.K_LEFT:   brightness = max(brightness - 10, -100)
                    elif key in RAMP_KEYS:       ramp_idx = RAMP_KEYS[key]
                    elif key in PALETTE_KEYS:    palette_idx = PALETTE_KEYS[key]
                elif event.type == pygame.DROPFILE:
                    new = camera.open_file(event.file)
                    if new:
                        camera.release_camera(cam)
                        cam = new
                        frame, status = camera.get_frame(cam), f"Opened {os.path.basename(event.file)}"
                    else:
                        status = f"Can't read {os.path.basename(event.file)}"

            if not paused:
                frame = camera.get_frame(cam)

            palette = PALETTES[palette_idx]
            img = render(frame)
            img_h, img_w = img.shape[:2]
            rows = ascii_engine.grid_rows(*frame.shape[:2], cols)

            screen.fill(palette["bg"])
            screen.blit(
                pygame.image.frombuffer(img, (img_w, img_h), "RGB"),
                ((WINDOW_W - img_w) // 2, (WINDOW_H - img_h) // 2),
            )
            screen.blit(crt_overlay, (0, 0))

            # HUD
            hud_str = f"FPS:{int(clock.get_fps()):2d} | GRID:{cols}x{rows} | RAMP:{RAMPS[ramp_idx]['name']} | MODE:{palette['name']} | EDGES:{'ON' if edges else 'OFF'}"
            screen.blit(hud_font.render(hud_str, True, (255, 255, 255), (20, 20, 20)), (15, 15))
            if status:
                screen.blit(hud_font.render(status, True, (255, 255, 255), (20, 20, 20)), (15, 40))
            screen.blit(help_surf, (15, WINDOW_H - 35))

            pygame.display.flip()
            clock.tick(60)
    finally:
        camera.release_camera(cam)
        pygame.quit()


if __name__ == "__main__":
    main()