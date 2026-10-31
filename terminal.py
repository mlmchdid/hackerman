"""Original Window/Terminal interface with a cinematic visual skin.

The original stroke-based open/close/reset state, append-only text and cursor
behavior are retained. Cosmetic improvements live in draw() and _draw_chrome().
"""
import pygame
from fonts import mono_font
import ui_theme as ui

# Keep these import names for compatibility with the original main.py.
GREEN = ui.GREEN
DIM_GREEN = ui.GREEN_DIM
TITLE_BG = ui.TITLE_BG
BORDER = ui.BORDER
PANEL_BG = ui.PANEL
RED = ui.RED
RED_DIM = (120, 35, 48)
RED_TITLE_BG = (43, 13, 22)
RED_BORDER = ui.RED
RED_PANEL = (24, 10, 17)

class Window:
    """Original window-manager state + new renderer (drag/close still work)."""
    def __init__(self, title, rect):
        self.title = title
        self.rect = pygame.Rect(rect)
        self.title_font = mono_font(14, bold=True)
        self.title_h = max(37, self.title_font.get_linesize() + 15)
        self.visible = False
        self.closable = True
        self.counter = 0
        self.threshold = 50
        self.compromised = False
        self.primary = False

    def _fg(self):
        return RED if self.compromised else GREEN

    def recolor(self):
        pass

    @property
    def title_rect(self):
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.w, self.title_h)

    @property
    def close_rect(self):
        size = self.title_h - 12
        return pygame.Rect(self.rect.right - size - 9,
                           self.rect.y + (self.title_h-size)//2, size, size)

    def _draw_chrome(self, surface):
        ui.chrome(surface, self.rect, self.title, self.title_h,
                  self.closable, self.close_rect, self.primary, self.compromised)


class Terminal(Window):
    """Streaming phosphor-green shell (C output is raw text, not an IDE)."""
    def __init__(self, title, rect, prompt='', cursor=False, font_size=15):
        super().__init__(title, rect)
        self.prompt = prompt
        self.cursor = cursor
        self.primary = cursor
        self.font = mono_font(font_size)
        self.line_h = self.font.get_linesize() + 4
        self.pad = 15
        self.elapsed = 0
        self._line_cache = {}
        self._glow_cache = {}
        self.reset()

    def reset(self):
        self.text = self.prompt
        self._lines = self.text.split('\n')
        self._line_cache = {}
        self._glow_cache = {}
        self._surf = None   # compatibility with the previous widget's private field

    def recolor(self):
        self._line_cache = {}
        self._glow_cache = {}

    def add_text(self, chunk):
        self.text += chunk
        if len(self.text) > 20000:
            self.text = self.text[-20000:]
        self._lines = self.text.split('\n')
        # Retain cached surfaces for historical lines; discard on color change.
        if len(self._line_cache) > 1600:
            self._line_cache = {}
            self._glow_cache = {}

    def _cached_line(self, line):
        """Monochrome rendering: every C token looks like terminal output."""
        key = (line, self.compromised, self.primary)
        cached = self._line_cache.get(key)
        if cached is None:
            color = RED if self.compromised else ((121, 255, 157) if self.primary else self._fg())
            cached = self.font.render(line.expandtabs(4), True, color)
            self._line_cache[key] = cached
        return cached

    def update(self, dt):
        self.elapsed += dt

    def draw(self, surface):
        self._draw_chrome(surface)
        r = self.rect
        if r.w < 90 or r.h < 100:
            return
        is_code = self.primary

        # An actual terminal has no editor gutters, tabs or language-mode status.
        # Its darker interior emphasizes the scrolling green output.
        if is_code:
            inner = pygame.Rect(r.x + 2, r.y + self.title_h + 2,
                                max(1, r.w - 4), max(1, r.h - self.title_h - 4))
            pygame.draw.rect(surface, (1, 9, 4) if not self.compromised
                             else (16, 3, 5), inner)
            # A hairline across the top is a shell-style separation, not a tab.
            pygame.draw.line(surface, ui.GREEN_DIM if not self.compromised else RED,
                             (inner.left + 8, inner.top + 1),
                             (inner.right - 8, inner.top + 1), 1)

        content = pygame.Rect(r.x + self.pad + (4 if is_code else 0),
                              r.y + self.title_h + (18 if is_code else 13),
                              max(1, r.w - 2 * self.pad - (8 if is_code else 0)),
                              max(1, r.h - self.title_h - (32 if is_code else 28)))
        total = len(self._lines)
        capacity = max(1, content.h // self.line_h)
        start = max(0, total - capacity)

        # The underlying terminal text, scroll position and auto-typing
        # behavior are unchanged. Only the presentation is different.
        old_clip = surface.get_clip()
        surface.set_clip(content)
        for index in range(start, total):
            y = content.y + (index-start) * self.line_h
            if y >= content.bottom:
                break
            line = self._lines[index]
            if is_code and not self.compromised:
                # One-pixel phosphor halo; kept subtle to preserve legibility.
                glow = self._glow_cache.get(line)
                if glow is None:
                    glow = self.font.render(line.expandtabs(4), True, (20, 75, 33))
                    self._glow_cache[line] = glow
                surface.blit(glow, (content.x + 3, y + 1))
            surface.blit(self._cached_line(line), (content.x+2, y))

        if self.cursor and (pygame.time.get_ticks() // 470) % 2 == 0:
            last = self._lines[-1].expandtabs(4)
            x = content.x + 2 + self.font.size(last)[0]
            y = content.y + (total-start-1) * self.line_h
            pygame.draw.rect(surface, RED if self.compromised else (142, 255, 172),
                             (x, y, 9, self.font.get_linesize()))
        surface.set_clip(old_clip)

        # Live event feed keeps its own tiny status footer. The main terminal
        # deliberately has none (no INSERT, Ln/Col, or editor readouts).
        if not is_code:
            fy = r.bottom - 28
            pygame.draw.line(surface, ui.GRID, (r.x+1, fy), (r.right-1, fy))
            pygame.draw.rect(surface, ui.PANEL_INNER, (r.x+1, fy+1, r.w-2, 26))
            ui.text(surface, '●  LISTENING ON :443', r.x+15, fy+7, 10, ui.GREEN)
            if r.w >= 290:
                ui.right_text(surface, f'{total:05d} EVENTS', r.right-15,
                              fy+7, 10, ui.MUTED)
