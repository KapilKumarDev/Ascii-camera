import pygame
import camera
import ascii_engine
from ascii_engine import RAMPS
from filters import PALETTES

WINDOW_W, WINDOW_H = 1280, 720

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("ASCII Camera Synthesizer")
    clock = pygame.time.Clock()

    cam = camera.init_camera(width=WINDOW_W, height=WINDOW_H)

    # Pre-build the CRT scanline overlay once (never changes)
    crt_overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    for y in range(0, WINDOW_H, 3):
        pygame.draw.line(crt_overlay, (0, 0, 0, 70), (0, y), (WINDOW_W, y))

    # Pre-build HUD fonts once
    hud_font = pygame.font.SysFont("couriernew", 16, bold=True)
    help_font = pygame.font.SysFont("couriernew", 14)

    # State
    cols = 120
    brightness = 0
    invert = False
    ramp_idx = 0
    palette_idx = 0
    paused = False
    frame = None

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:  paused = not paused
                    elif event.key == pygame.K_i:      invert = not invert
                    elif event.key == pygame.K_UP:     cols = min(cols + 10, 300)
                    elif event.key == pygame.K_DOWN:   cols = max(cols - 10, 30)
                    elif event.key == pygame.K_RIGHT:  brightness = min(brightness + 10, 100)
                    elif event.key == pygame.K_LEFT:   brightness = max(brightness - 10, -100)
                    elif event.key == pygame.K_1: ramp_idx = 0
                    elif event.key == pygame.K_2: ramp_idx = 1
                    elif event.key == pygame.K_3: ramp_idx = 2
                    elif event.key == pygame.K_4: ramp_idx = 3
                    elif event.key == pygame.K_5: ramp_idx = 4
                    elif event.key == pygame.K_q: palette_idx = 0
                    elif event.key == pygame.K_w: palette_idx = 1
                    elif event.key == pygame.K_e: palette_idx = 2
                    elif event.key == pygame.K_r: palette_idx = 3
                    elif event.key == pygame.K_t: palette_idx = 4

            # Get camera frame
            if not paused:
                new_frame = camera.get_frame(cam)
                if new_frame is not None:
                    frame = new_frame

            if frame is None:
                continue

            # Convert frame to ASCII
            indices, rgb_colors, ramp = ascii_engine.process_frame(
                frame, cols, brightness, invert, ramp_idx
            )

            rows = indices.shape[0]
            cell_w = WINDOW_W / cols
            cell_h = WINDOW_H / rows
            render_font = pygame.font.SysFont("couriernew", max(int(cell_h * 1.1), 8), bold=True)

            palette = PALETTES[palette_idx % len(PALETTES)]
            bg_col = palette["bg"]
            fg_col = palette["fg"]
            screen.fill(bg_col)

            # Render ASCII grid
            if fg_col is not None:
                # Single-color mode: render whole rows as strings (fast)
                for r in range(rows):
                    row_str = "".join(ramp[indices[r, c]] for c in range(cols))
                    screen.blit(render_font.render(row_str, False, fg_col), (0, r * cell_h))
            else:
                # Full-color mode: render each character with its source pixel color
                for r in range(rows):
                    for c in range(cols):
                        color = tuple(rgb_colors[r, c])
                        screen.blit(
                            render_font.render(ramp[indices[r, c]], False, color),
                            (c * cell_w, r * cell_h)
                        )

            # CRT scanline effect
            screen.blit(crt_overlay, (0, 0))

            # HUD
            fps = int(clock.get_fps())
            hud_str = f"FPS:{fps:2d} | GRID:{cols}x{rows} | RAMP:{RAMPS[ramp_idx]['name']} | MODE:{palette['name']}"
            screen.blit(hud_font.render(hud_str, True, (255, 255, 255), (20, 20, 20)), (15, 15))

            help_str = "[1-5]Ramps [QWERT]Color [I]Inv [UP/DN]Res [L/R]Brt [SPC]Pause"
            screen.blit(help_font.render(help_str, True, (150, 150, 150), (20, 20, 20)), (15, WINDOW_H - 35))

            pygame.display.flip()
            clock.tick(60)
    finally:
        camera.release_camera(cam)
        pygame.quit()

if __name__ == "__main__":
    main()
