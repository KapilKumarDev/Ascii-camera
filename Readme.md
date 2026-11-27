# ASCII Camera

Real-time video to ASCII, shown in an OpenCV window.

## Install

```
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless
pip install -r requirements.txt
```

The uninstall step matters. The `-headless` builds have no window support
(`cv2.imshow` fails with "The function is not implemented"), and they share one
`cv2` folder with `opencv-python`, so having both breaks the window.

## Run

```
python ascii_video.py              # webcam 0, 120 columns
python ascii_video.py 1            # webcam 1
python ascii_video.py clip.mp4 160 # video file (loops), 160 columns
```

## Keys

| Key | Action |
|-----|--------|
| `1`-`4` | character ramp (10 / 70 / 6 / 2 chars) |
| `z` `x` `c` | white / green / amber |
| `v` | colour from source video |
| `i` | invert |
| `q` | quit |

## Test

```
python test_ascii_video.py
```