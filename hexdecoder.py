"""Original hexadecimal stream/reveal logic with a cinematic hexdump skin."""
import random
import pygame
from fonts import mono_font
from terminal import Window
import ui_theme as ui

GREEN = ui.GREEN
BRIGHT = ui.WHITE
YELLOW = ui.AMBER
RED = ui.RED
WORDS = ['ACCESS','MATRIX','HACKER','ROOT','PROTOCOL','BREACH',
         'CIPHER','BACKDOOR','VECTOR','GHOST','NEON','MAINFRAME']


class HexDecoder(Window):
    def __init__(self, title, rect):
        super().__init__(title, rect)
        self.font = mono_font(12)
        self.mini_font = mono_font(10)
        self.line_h = self.font.get_linesize() + 3
        self.pad = 14
        self.reset()

    def reset(self):
        self.lines = []
        self.hex_timer = 0.0
        self.find_timer = 2.0
        self.finds = 0
        self.revealed = False
        self.flash = 0.0

    def _add_hex_line(self):
        line = ' '.join(f'{random.randint(0, 255):02X}' for _ in range(16))
        self.lines.append((line, GREEN))
        if len(self.lines) > 400:
            self.lines = self.lines[-400:]

    def update(self, dt):
        self.hex_timer += dt
        while self.hex_timer >= .07:
            self.hex_timer -= .07
            self._add_hex_line()
        if not self.revealed:
            self.find_timer -= dt
            if self.find_timer <= 0:
                self.find_timer = random.uniform(2., 4.)
                word = random.choice(WORDS)
                self.lines.append((f'> FOUND: {word}', YELLOW))
                self.finds += 1
                if self.finds >= 6:
                    self.revealed = True
                    self.flash = 0.
                    self.lines.append(('SECRET MESSAGE: HELLO WORLD', BRIGHT))
        else:
            self.flash += dt

    def draw(self, surface):
        self._draw_chrome(surface)
        r = self.rect
        if r.h < 97 or r.w < 180:
            return
        bar_y = r.y+self.title_h+1
        pygame.draw.rect(surface, ui.PANEL_INNER, (r.x+1, bar_y, r.w-2, 23))
        ui.text(surface, '●  RAW BUFFER / OFFSET 0x0000',
                r.x+14, bar_y+6, 9, ui.CYAN, True)
        if r.w > 375:
            ui.right_text(surface, '16 BYTES/ROW', r.right-15, bar_y+6, 9, ui.GREEN_DIM)
        bottom = r.bottom-28
        content = pygame.Rect(r.x+12, bar_y+25, r.w-24, max(1, bottom-(bar_y+28)))
        visible = max(1, content.h // self.line_h)
        start = max(0, len(self.lines)-visible)
        surface.set_clip(content)
        for i, (line, stored_color) in enumerate(self.lines[start:]):
            y = content.y+i*self.line_h
            if y+self.line_h > content.bottom + 3:
                break
            if line.startswith('SECRET MESSAGE'):
                col = YELLOW if int(self.flash*2.5)%2 == 0 else BRIGHT
                display = line
                pygame.draw.rect(surface, (54, 44, 23), (content.x, y, content.w, self.line_h))
            elif self.compromised and stored_color == GREEN:
                col = RED
                display = line
            else:
                col = ui.GREEN_DIM if stored_color == GREEN else stored_color
                display = line
            if stored_color == GREEN:
                offset = (start+i)*16
                ui.text(surface, f'{offset:06X}', content.x, y+1, 9, ui.MUTED)
                surface.blit(self.font.render(display, True, col), (content.x+55, y))
                if r.w > 525:
                    # Visual-only ASCII lane; content is unchanged.
                    ascii_text = ''.join(chr(int(n, 16)) if 32 <= int(n,16)<127 else '.'
                                         for n in line.split())
                    ui.text(surface, ascii_text, content.x+int(content.w*.72), y+1, 9, ui.CYAN)
            else:
                surface.blit(self.font.render(display, True, col), (content.x+5, y))
        surface.set_clip(None)
        pygame.draw.rect(surface, ui.PANEL_INNER, (r.x+1, bottom, r.w-2, 27))
        pygame.draw.line(surface, ui.GRID, (r.x, bottom), (r.right, bottom))
        ui.text(surface, f'PATTERNS  {self.finds:02d}/06', r.x+15, bottom+8, 10,
                YELLOW if self.revealed else ui.GREEN)
        ui.right_text(surface, 'MESSAGE FOUND' if self.revealed else 'DECODING...',
                      r.right-14, bottom+8, 10,
                      YELLOW if self.revealed else ui.MUTED)
