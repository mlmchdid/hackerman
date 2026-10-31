"""Windows 10 style stop-error renderer. No game state or keyboard input here.

The blue-screen artwork is drawn in Pygame, so it scales with the window and
works offline. The bundled QR image encodes https://www.windows.com/stopcode.
This is a *visual recreation*, not an operating system crash.
"""
from functools import lru_cache
from pathlib import Path
import pygame

BLUE = (0, 120, 215)   # familiar Windows 10 stop-screen blue (#0078D7)
WHITE = (255, 255, 255)
QR_PATH = Path(__file__).resolve().parent / 'assets' / 'windows_stopcode_qr.png'

# The original game still supplies fictional ending IDs; only the DISPLAYED
# Windows stop codes change to valid, recognizable ones.
WINDOWS_STOP_CODES = {
    'NUCLEAR_LAUNCH_DETECTED': 'CRITICAL_PROCESS_DIED',
    'SYSTEM_COMPROMISED': 'SYSTEM_SERVICE_EXCEPTION',
}


@lru_cache(maxsize=30)
def _windows_font(size):
    """Segoe UI when available, then a close sans-serif system fallback."""
    size = max(9, int(size))
    for family in ('segoe ui', 'segoeuil', 'arial', 'liberation sans', 'dejavu sans'):
        path = pygame.font.match_font(family)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def _line(surface, text, x, y, size):
    rendered = _windows_font(size).render(text, True, WHITE)
    surface.blit(rendered, (int(x), int(y)))
    return rendered.get_height()


def _wrap(text, font, limit):
    """Wrap based on pixel width, never split individual words."""
    lines = []
    current = ''
    for word in text.split():
        candidate = f'{current} {word}'.strip()
        if current and font.size(candidate)[0] > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


class WindowsBlueScreen:
    def __init__(self):
        self._qr = None
        self._sized_qr = None
        self._qr_size = None

    def _qr_surface(self, side):
        if self._qr is None:
            try:
                self._qr = pygame.image.load(str(QR_PATH))
            except (pygame.error, OSError):
                return None
        if self._qr_size != side:
            # Use nearest-neighbor scaling to keep QR modules perfectly sharp.
            self._sized_qr = pygame.transform.scale(self._qr, (side, side))
            self._qr_size = side
        return self._sized_qr

    def draw(self, surface, percent, internal_code):
        w, h = surface.get_size()
        surface.fill(BLUE)
        # Coordinates follow the Windows 10 stop-screen proportions rather
        # than a centered dialog or a custom hacker overlay.
        scale = max(.52, min(w / 1366.0, h / 768.0))
        left = max(28, int(w * .123))
        top = max(20, int(h * .154))
        large = max(64, int(112 * scale))
        body = max(17, int(25 * scale))
        minor = max(10, int(12.5 * scale))
        _line(surface, ':(', left, top, large)

        message = ("Your PC ran into a problem and needs to restart. "
                   "We're just collecting some error info, and then we'll "
                   "restart for you.")
        font = _windows_font(body)
        max_width = max(300, w - left - int(50*scale))
        message_lines = _wrap(message, font, max_width)
        y = top + int(145*scale)
        step = max(font.get_linesize(), int(34*scale))
        for line in message_lines:
            _line(surface, line, left, y, body)
            y += step

        # Windows 10 displays a bare percentage: no progress bar.
        y += int(23*scale)
        _line(surface, f'{min(100, max(0, int(percent)))}% complete', left, y, body)
        y += int(64*scale)
        qr_side = int(116 * scale)
        qr = self._qr_surface(qr_side)
        if qr is not None:
            surface.blit(qr, (left, y))

        # Real stop-screen small print beside the QR code.
        right = left + qr_side + int(17*scale)
        small_width = max(150, w - right - int(30*scale))
        yy = y + int(2*scale)
        notes = (
            'For more information about this issue and possible fixes, visit',
            'https://www.windows.com/stopcode',
            '',
            'If you call a support person, give them this info:',
            'Stop code: ' + WINDOWS_STOP_CODES.get(internal_code, 'CRITICAL_PROCESS_DIED'),
        )
        smallfont = _windows_font(minor)
        step2 = max(smallfont.get_linesize(), int(18*scale))
        for note in notes:
            if not note:
                yy += step2//2
                continue
            for line in _wrap(note, smallfont, small_width):
                _line(surface, line, right, yy, minor)
                yy += step2
