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
- 📺 **CRT Scanline Effect**: Translucent overlay simulates retro CRT monitors.
- ⌨️ **Interactive Controls**: Real-time hotkeys for grid resolution, brightness, palettes, and character ramps.

---

## 🔬 Mathematical Principles

### Aspect Ratio Correction & Downscaling
Monospaced font characters are taller than wide (aspect ratio ≈ 0.55). To prevent stretching:
$$\text{Rows} = \text{round}\left( \text{Cols} \times \frac{\text{Frame Height}}{\text{Frame Width}} \times 0.55 \right)$$

### Vectorized Luminance Mapping
1. Brightness adjustment:
   $$L_{\text{adjusted}} = \text{clip}(L + \text{brightness}, 0, 255)$$
2. Character index lookup (vectorized with NumPy):
   $$\text{Index} = \left\lfloor \frac{L_{\text{adjusted}}}{255} \times (\text{Ramp Length} - 1) \right\rfloor$$

---

## 🛠️ Installation

### Requirements:
- Python 3.8+
- Dependencies: `opencv-python`, `numpy`, `pygame-ce`

### Quick Setup:
```bash
pip install -r requirements.txt
python main.py
```

---

## 🧩 File Structure

```
├── main.py             # Pygame render loop, keyboard controls, HUD
├── camera.py           # OpenCV webcam handler & animated demo fallback
├── ascii_engine.py     # Luminance math, character ramps, frame-to-ASCII conversion
├── filters.py          # Color palette definitions
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

---

## ⌨️ Keyboard Controls

| Key | Function |
| :--- | :--- |
| `1` - `5` | Switch Character Ramp (Classic, Extended, Matrix, Blocks, Binary) |
| `F1` - `F5` | Switch Color Palette (Matrix Green, Cyber Neon, Amber, Monochrome, Full RGB) |
| `I` | Toggle Invert Luminance |
| `UP` / `DOWN` | Increase / Decrease Grid Resolution (±10) |
| `LEFT` / `RIGHT` | Decrease / Increase Brightness |
| `SPACE` | Pause / Resume Video Stream |
| `ESC` / `Q` | Quit Application |
