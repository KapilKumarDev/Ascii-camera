# 🎥 Real-Time ASCII Camera Synthesizer

A Python application that transforms your live webcam feed into an interactive ASCII visual synthesizer. Built with `OpenCV`, `NumPy`, and `Pygame`.

---

## 🌟 Features

- 🎥 **Live Camera Feed & Fallback Demo**: Connects to your webcam via OpenCV. If no camera is available, an animated synthetic test pattern plays automatically.
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
1. Brightness adjustment:
   $$L_{\text{adjusted}} = \text{clip}(L + \text{brightness}, 0, 255)$$
2. Character index lookup (vectorized with NumPy):
   $$\text{Index} = \left\lfloor \frac{L_{\text{adjusted}}}{256} \times \text{Ramp Length} \right\rfloor$$

### Edge Detection
1. Downscale to 4 pixels per cell column (keeping the source aspect ratio), grayscale, blur.
2. Canny with thresholds from Otsu's method: $\text{high} = 2 \times T_{\text{Otsu}}$, $\text{low} = \text{high} / 2$.
3. Sobel gradients $G_x, G_y$ at edge pixels give each cell a dominant gradient angle via the structure tensor:
   $$\theta = \tfrac{1}{2}\,\operatorname{atan2}\left(2\sum G_xG_y,\ \sum G_x^2 - \sum G_y^2\right)$$
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
python main.py
```

---

## 🧩 File Structure

```
├── main.py             # Pygame loop, keyboard controls, HUD
├── camera.py           # OpenCV webcam handler & animated demo fallback
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
| `ESC` | Quit Application |