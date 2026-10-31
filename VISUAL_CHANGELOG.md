# Visual redesign notes

## Design direction

- Concept: command-center dashboard from a hacker movie, not a functional pen-test utility.
- Background: deep navy/charcoal with low-contrast Matrix rain and grid.
- Primary action: unmistakably highlighted kernel C editor with continuously growing text.
- Secondary activity: independent radar, fake connection log and simulated hexdump.
- Palette: mint/cyan for status and scanning, amber for warnings/strings, purple for C keywords, red for critical endings.

## Behavior preservation

The following progression is intentionally kept the same as in the original `main.py`:

1. First valid keystroke opens main terminal and appends 4 characters of CODE.
2. 50/100/150 keystrokes show phrases/radar/hex respectively.
3. Closing any side panel resets its counter and stream; another threshold of keystrokes opens it again.
4. On each tick phrases are emitted in original timed 15-message bursts; radar target lifetime and hex discovery process remain unchanged.
5. `W+Q` and `P+O` increment separate access counters; `Enter` hides the current access dialog.
6. Nuclear ending requires >=3 grants plus all visible panels; countdown remains 10 seconds and then the fake crash.
7. Compromise ending requires >=3 denies plus all visible panels; it freezes panels and triggers the fake crash after 5 seconds.
8. Escape remains a three-press exit. Windows can still be dragged and reordered.

## Intentional layout-only changes

- The original large centered terminal and corner windows are replaced with a 61–64% left-side C editor and three vertically aligned side windows. This prevents the panels from obscuring the C code at the default positions.
- The close icon/toolbar are larger, and window chrome consumes a few more pixels.
- Main terminal line numbers and syntax highlight do not affect the content string or keystroke handling.
- Font loading falls back gracefully when the original font files are unavailable; no font files are redistributed.
- A cached dark overlay and cached panel shadows avoid allocating full-screen translucent surfaces each frame.

## Verification performed

- Python compilation of all source files (`compileall`)
- Test progression, code input with another window in front, closing/reopening, both endings, three-Escape exit
- Test rendering calls with a pygame-compatible lightweight shim
- Real window rendering **not** tested because pygame was not installed in the packaging environment

## V2: terminal / BSOD polish

- Removed upper-left HACKERMAN branding, session clock and keystroke total.
- Removed full-width bottom bar and the text about simulated input.
- Gave the main C display a green-on-near-black monochrome terminal, removing
  C keyword syntax colors, line-number gutter, file tab and editor status.
- All keystrokes and 1/50/100/150 unlock logic remain unchanged.
- Replaced custom fictional crash presentation with Windows 10-style blue
  stop screen (Segoe UI style sans, large sad face, real QR image, stop code).
- The fictional crash IDs remain part of internal logic but are displayed as
  normal Windows stop codes; the percentage progression and exit remain intact.
