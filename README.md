# 🎥 Real-Time ASCII Camera Synthesizer

A Python application that transforms your live webcam feed into an interactive ASCII visual synthesizer. Built with `OpenCV`, `NumPy`, and `Pygame`.

---

## 🌟 Features

- 🎥 **Live Camera Feed & Fallback Demo**: Connects to your webcam via OpenCV. If no camera is available, an animated synthetic test pattern plays automatically.
- 📂 **Import Image / Video**: Drop a file onto the window (or run `python main.py <file>`) to view it as ASCII art. Videos play at their own frame rate and loop. Press `C` to go back to the camera.
- 💾 **Export**: Press `S` to save the output with the current settings: a PNG for the camera or an image, the whole video as an MP4 (no audio) for a video.
- 🔤 **Multiple Character Ramps**: Switch between **Classic ASCII**, **Extended**, **Matrix Digital**, **Block Shades**, and **Binary (0/1)**.
- 🎨 **Real-Time Color Palettes**:
  - 🟢 **Matrix Green**: Hacker-style phosphor CRT.
  - 🔵 **Cyber Neon**: High-contrast cyan.
  - 🟠 **Amber CRT**: Retro 1980s terminal.
  - ⚪ **Monochrome**: Clean white-on-black.
  - 🌈 **Full RGB**: Characters drawn with original webcam colors.
- ✏️ **Edge Detection**: Native OpenCV Canny edges drawn as directional characters (`|` `/` `-` `\`) that follow the outline. No ML model needed. Toggle with `D`.
- 📺 **CRT Scanline Effect**: Translucent overlay simulates retro CRT monitors.
- ⌨️ **Interactive Controls**: Real-time hotkeys for grid resolution, brightness, palettes, and character ramps.

---

## 🔬 Mathematical Principles

### Aspect Ratio Correction & Downscaling
Monospaced font characters are taller than wide (aspect ratio ≈ 0.55). To prevent stretching:
$$\text{Rows} = \left\lfloor \text{Cols} \times \frac{\text{Frame Height}}{\text{Frame Width}} \times 0.55 \right\rfloor$$

### Vectorized Luminance Mapping
1. Auto-levels: webcam frames are often dull, so the 2nd to 98th brightness percentiles ($p_2$, $p_{98}$) are stretched to the full range (skipped if $p_{98} - p_2 < 32$, i.e. a flat frame). This keeps the whole ramp in use and keeps edge detection working in low light:
   $$L' = \text{clip}\left(\frac{L - p_2}{p_{98} - p_2} \times 255,\ 0,\ 255\right)$$
2. Brightness adjustment:
   $$L_{\text{adjusted}} = \text{clip}(L' + \text{brightness}, 0, 255)$$
3. Character index lookup (vectorized with NumPy):
   $$\text{Index} = \left\lfloor \frac{L_{\text{adjusted}}}{256} \times \text{Ramp Length} \right\rfloor$$
4. The glyph behind each index is chosen by measured ink, not by the order the characters are listed. Each glyph is rendered, its mean coverage $a_g$ is measured, and level $k$ of $n$ takes the glyph closest to the $k$-th evenly spaced target:
   $$g_k = \arg\min_g \left| a_g - \left(a_{\min} + \tfrac{k}{n-1}(a_{\max} - a_{\min})\right) \right|$$
   So brightness maps linearly to ink in any font, and every ramp (even `MATRIX` or `BINARY`) reads as a smooth gradient.

### Edge Detection
1. Downscale to 4 pixels per cell column (keeping the source aspect ratio), grayscale, blur.
2. Canny with thresholds from Otsu's method: $\text{high} = 2 \times T_{\text{Otsu}}$, $\text{low} = \text{high} / 2$.
3. Sobel gradients $G_x, G_y$ at edge pixels give each cell a dominant gradient angle via the structure tensor:
   $$\theta = \tfrac{1}{2}\,\text{atan2}\left(2\sum G_xG_y,\ \sum G_x^2 - \sum G_y^2\right)
   $$
4. The edge runs perpendicular to the gradient. $\theta$ is snapped to 0°, 45°, 90°, 135° and shown as `|`, `/`, `-`, `\`.
5. A cell counts as an edge only if its edge pixels cover at least one pixel per cell row.

---

## 🛠️ Installation

### Requirements:
- Python 3.10+
- Dependencies: `opencv-python`, `numpy`, `pygame-ce`

### Quick Setup:
```bash
pip install -r requirements.txt
python main.py              # webcam (or demo pattern)
python main.py photo.jpg    # or open an image / video file
```

Exports are written to the current directory as `<name>_ascii_<timestamp>.png` / `.mp4`. Hold `ESC` during a video export to cancel it.

---

## 🧩 File Structure

```
├── main.py             # Pygame loop, keyboard controls, HUD
├── camera.py           # Frame sources: OpenCV webcam, animated demo fallback, image/video files
├── export.py           # Save current output as PNG, or render a whole video to MP4
├── ascii_engine.py     # Character ramps, luminance + edge detection, glyph atlas, vectorized grid render
├── filters.py          # Color palette definitions
├── tests/              # Self-check: python -m tests.test_ascii_engine
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

---

## ⌨️ Keyboard Controls

| Key | Function |
| :--- | :--- |
| `1` - `5` | Switch Character Ramp (Classic, Extended, Matrix, Blocks, Binary) |
| `Q` `W` `E` `R` `T` | Switch Color Palette (Matrix Green, Cyber Neon, Amber, Monochrome, Full RGB) |
| `D` | Toggle Edge Detection |
| `I` | Toggle Invert Luminance |
| `UP` / `DOWN` | Increase / Decrease Grid Resolution (±10) |
| `LEFT` / `RIGHT` | Decrease / Increase Brightness |
| `SPACE` | Pause / Resume Video Stream |
| `S` | Save output (PNG, or MP4 for an imported video) |
| `C` | Back to the camera after importing a file |
| Drop a file | Import an image or video |
| `ESC` | Quit Application |