import cv2
import numpy as np
import time

def init_camera(camera_index=0, width=1280, height=720):
    """Opens the webcam."""
    cap = cv2.VideoCapture(camera_index)
    use_fallback = False

    if not cap.isOpened():
        print(f"Warning: Camera {camera_index} not available. Using demo pattern.")
        use_fallback = True
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        ret, _ = cap.read()
        if not ret:
            print("Warning: Camera opened but can't read frames. Using demo pattern.")
            use_fallback = True

    return {
        "cap": cap,
        "use_fallback": use_fallback,
        "start_time": time.time(),
        "width": width,
        "height": height
    }

def get_frame(cam):
    """Returns a BGR frame from the camera, or a synthetic pattern as fallback."""
    if not cam["use_fallback"]:
        ret, frame = cam["cap"].read()
        if ret:
            return frame

    return _synthetic_pattern(cam)

def _synthetic_pattern(cam):
    """Animated wave + bouncing shapes demo when no camera is available."""
    t = time.time() - cam["start_time"]
    w, h = cam["width"], cam["height"]

    # Each wave depends on one axis only, so keep them 1-D and let numpy broadcast
    wave1 = np.sin(np.arange(w) * 0.01 + t * 2) * 50 + 128
    wave2 = np.cos(np.arange(h)[:, None] * 0.02 - t * 3) * 50 + 128

    frame = np.empty((h, w, 3), dtype=np.uint8)
    frame[:, :, 0] = np.clip(wave1 * 0.6 + wave2 * 0.4, 0, 255)
    frame[:, :, 1] = np.clip(np.sin(t * 0.5) * 127 + 128, 0, 255)
    frame[:, :, 2] = np.clip(wave2, 0, 255)

    # Bouncing circle
    cx = int(w / 2 + np.cos(t * 1.5) * (w / 3))
    cy = int(h / 2 + np.sin(t * 2.1) * (h / 3))
    cv2.circle(frame, (cx, cy), h // 5, (255, 255, 255), -1)

    # Bouncing square
    sx = int(w / 2 + np.sin(t * 1.1) * (w / 3))
    sy = int(h / 2 + np.cos(t * 1.7) * (h / 3))
    s = h // 6
    cv2.rectangle(frame, (sx - s, sy - s), (sx + s, sy + s), (0, 0, 0), -1)

    return frame

def release_camera(cam):
    """Releases the OpenCV capture device."""
    cap = cam["cap"]
    if cap and cap.isOpened():
        cap.release()
