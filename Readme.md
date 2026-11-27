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
| `1`-`5` | character ramp: 1 = 10 chars, 2 = 69 chars, 3 = 6 chars, 4 = blocks `█▓▒░`, 5 = 2 chars |
| `q` `w` `e` | white / green / amber text on black |
| `r` | real colour (text takes the video's colour) |
| `c` | contrast boost (CLAHE + stretch to full brightness range), on at start |
| `[` `]` | less / more stability (hold threshold, step 2, 0 = off, starts at 10) |
| `i` | invert |
| `Esc` | quit |

## Colours

Colour schemes live in the `COLORS` dict in `ascii_video.py`. Each key maps to
`{"fg": ..., "bg": ...}`: `fg` is the text colour, `bg` the colour behind it.
`bg` can be left out and then defaults to black. A colour is a BGR tuple, or
`None` to take it from the video. To add a scheme, add a line, for example
`"t": {"fg": (0, 255, 0), "bg": (60, 0, 0)}`.

## Test

```
python test_ascii_video.py
```