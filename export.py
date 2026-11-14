import os
import time

import cv2
import pygame


def _stem(cam):
    """Output name: source file name (or 'camera') + _ascii + timestamp, so exports never overwrite."""
    name = os.path.splitext(os.path.basename(cam.get("path", "camera")))[0]
    return f"{name}_ascii_{time.strftime('%Y%m%d_%H%M%S')}"


def _export_video(src_path, render, out_path):
    """Renders every frame of a video file through `render` into an MP4. ESC or closing the window cancels."""
    cap = cv2.VideoCapture(src_path)  # own handle, so playback position is untouched
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    writer = None
    cancelled = False
    done = 0
    while not cancelled:
        ret, frame = cap.read()
        if not ret:
            break
        img = render(frame)
        if writer is None:
            h, w = img.shape[:2]
            writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        done += 1
        pygame.display.set_caption(f"Exporting {done}/{total if total > 0 else '?'} - ESC cancels")
        cancelled = any(
            e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)
            for e in pygame.event.get()
        )
    cap.release()
    if writer:
        writer.release()
    if cancelled:
        os.remove(out_path)
        return "Export cancelled"
    return f"Saved {out_path}"


def save(cam, frame, render):
    """
    Saves the current output with the current settings. `render` maps a BGR frame to an RGB image.
    Camera/image -> PNG of the shown frame. Video -> whole video as MP4 (no audio).
    Returns a status message.
    """
    stem = _stem(cam)
    if cam["kind"] == "video":
        return _export_video(cam["path"], render, stem + ".mp4")
    path = stem + ".png"
    cv2.imwrite(path, cv2.cvtColor(render(frame), cv2.COLOR_RGB2BGR))
    return f"Saved {path}"