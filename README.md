# HACKERMAN // Cinematic Terminal Edition

**A fictional movie-hacking simulator. Nothing in this app actually hacks anything.**

This is a visual redesign of [mlmchdid/hackerman](https://github.com/mlmchdid/hackerman).
The goal is **a classic neon-green hacking terminal inside a cinematic dashboard**, while keeping the original
keystroke-driven gameplay and hidden endings. It is a complete standalone source
package, not a GitHub commit.

## Run on Linux / Windows / macOS

Python **3.10+** is required. In an activated virtual environment:

```bash
python -m pip install -r requirements.txt
python main.py
```

Or use `uv run main.py` as in the original project.

### Ubuntu example

```bash
cd hackerman_cinematic
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The app launches fullscreen on desktop, using your display's native resolution.
It launches in a 1280x720 window under Pygbag/browser mode.

## Controls / original behavior

| Action | Behavior |
|---|---|
| Any non-modifier key | Prints the **next four** characters from the bundled fictional C source in the main terminal |
| First key | Opens main C terminal |
| 50 keys | Opens event/phrases terminal |
| 100 keys | Opens animated network radar |
| 150 keys | Opens animated hex decoder |
| Drag a title bar | Moves a window |
| Click a panel | Moves it to the front, **but typing still goes to the C terminal** |
| Click `X` on a side panel | Closes/reset panel; it reopens after its original threshold of further keystrokes |
| Hold `W`, then press `Q` | ACCESS GRANTED pop-up (Enter dismisses) |
| Hold `P`, then press `O` | ACCESS DENIED pop-up (Enter dismisses) |
| 3 grants, all four panels visible | Original 10-second nuclear-launch ending and fake crash |
| 3 denies, all four panels visible | Original 5-second compromised ending and fake crash |
| Escape, Escape, Escape | Quits the app |

**No separate input focus is ever required.** The graphical dashboard is purely
visual; typing only advances the kernel C code irrespective of which floating
panel was last clicked. Side panels show autonomously generated fake activity.

## What looks different

- Main editor is now a large, permanently emphasized **primary** panel.
- Right-side radar, live event stream, and decoder have an intentional visual
  hierarchy, rather than competing with the C source.
- Animated radar has a translucent scanner fan, concentric rings, marker echoes,
  and separate telemetry readout.
- C source now appears as **single-color phosphor-green terminal output** on
  near-black, with no IDE syntax palette, line numbers, tabs, or editor status bar.
- Matrix background is more atmospheric and less distracting, with a cooler tone.
- Window chrome uses neon accents, top bars, bordered cards, hoverable close
  controls, HUD labels, simulated readouts, and subtle shadows.
- Dialogs and both secret endings retain their visual treatments.
- The fake crash is a Windows 10-style blue screen: solid blue, white sans-serif
  text, sad-face icon, genuine QR code and realistic stop code. It is not a real
  OS error.
- The title/metrics header and footer have been removed, freeing more space.

## Project layout

```text
hackerman_cinematic/
├── main.py             # Existing event flow, triggers, and window management
├── data.py             # Kernel C source / fictional system phrases
├── terminal.py         # Window base, terminal/editor, syntax colors
├── radar.py            # Radar behavior and animated visual skin
├── hexdecoder.py       # Hex stream behavior and visual skin
├── matrix.py           # Matrix rain physics and revised colors
├── ui_theme.py         # Shared palette, panel chrome, overlays
├── fonts.py            # Cached monospace font loading with fallback
├── bsod_screen.py      # Windows 10-style mock BSOD renderer
├── tests/
│   └── test_behavior.py # Regression tests with a lightweight pygame shim
├── assets/             # Generated Windows help QR image
├── pyproject.toml
├── requirements.txt
├── requirements-web.txt
├── pygbag.ini
└── VISUAL_CHANGELOG.md
```

## Test original gameplay logic

The included regression tests simulate pygame input/state without needing a
monitor or the actual pygame package. They test the important user-facing
behaviors, including graphical draw code paths with a minimal surface shim:

```bash
python -m unittest discover -s tests -v
```

For **actual visual testing**, install pygame and run `python main.py` on your
machine. A full Pygame window wasn't available in the environment where this
package was created, so the graphics haven't been checked on a physical display.

## Pygbag (web build, optional)

```bash
python -m pip install -r requirements-web.txt
python -m pygbag main.py
```

The original TTFs were *not* included in this package. If you add the original
`DejaVuSansMono.ttf` and `DejaVuSansMono-Bold.ttf` alongside `fonts.py`, they
will be used automatically; otherwise the program uses an installed font or a
pygame fallback. A browser build may use the basic pygame fallback.

## Design guardrails

- `data.py` is plain C **text**, and the live panels are all simulated.
- Unlocked panels do not intercept keystrokes or introduce real network requests.
- The redesign minimizes game logic modifications: it changes placement and
  presentation, preserving triggers, counter logic, stream generation and endings.
- The filename structure stays compatible with the original app. The new theme
  is a separate module rather than a wholesale restructure of gameplay files.

## Changes in this revision

The top-left HACKERMAN heading, session duration, keystroke counter, and
bottom HUD are completely removed. The primary C window is now a minimal
terminal, not a code-editor simulation. The fake BSOD visually matches the
familiar Windows 10 design rather than the earlier cyberpunk custom screen.
The three-Escape exit and all existing unlocking/endings behavior still work.
The Windows 10 BSOD is for entertainment only; the app does not crash the OS.
