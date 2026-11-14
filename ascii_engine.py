import cv2
import numpy as np

# Character ramps ordered from dark to bright
RAMPS = [
    {"name": "CLASSIC", "chars": " .:-=+*#%@"},
    {"name": "EXTENDED", "chars": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"},
    {"name": "MATRIX", "chars": " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    {"name": "BLOCKS", "chars": " ░▒▓█"},
    {"name": "BINARY", "chars": " 01"}
]

def process_frame(frame, cols, brightness, invert, ramp_idx):
    """
    Downsamples the frame and converts it to ASCII indices.
    Returns:
        indices (np.ndarray): 2D array of character indices into the ramp.
        rgb_colors (np.ndarray): 2D array of RGB colors (for full-color mode).
        ramp (str): The character ramp string.
    """
    h, w = frame.shape[:2]

    # Calculate rows to maintain aspect ratio 
    rows = max(1, int((h / w) * cols * 0.55))

    # Downsample with area interpolation
    resized = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)

    # Grayscale for luminance mapping
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # RGB copy for full-color mode
    rgb_colors = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    # Brightness adjustment
    adjusted = np.clip(gray + brightness, 0, 255)

    if invert:
        adjusted = 255 - adjusted

    # Map luminance (0-255) to character index
    ramp = RAMPS[ramp_idx % len(RAMPS)]["chars"]
    indices = np.floor((adjusted / 255.0) * (len(ramp) - 1)).astype(np.int32)

    return indices, rgb_colors, ramp
