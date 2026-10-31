"""HACKERMAN — original gameplay and triggers, redesigned presentation.

Preserved: async pygame loop, auto-generated C per keystroke, 1/50/100/150
module unlock thresholds, window z-order/drag/close, W+Q / P+O endings,
three-Esc exit, Matrix rain, 10-second countdown and fake crash ending.
"""
import asyncio
import math
import random
import sys
import pygame
from fonts import mono_font
from data import CODE, PHRASES
from matrix import Matrix
from terminal import Terminal, GREEN, RED, TITLE_BG, BORDER, PANEL_BG
from radar import Radar
from hexdecoder import HexDecoder
from bsod_screen import WindowsBlueScreen
import ui_theme as ui

MARGIN, GAP = 22, 13
LAUNCH_DURATION = 10.0
BG = ui.BG
YELLOW = ui.AMBER
BLACK = (0, 0, 0)
THREAT_LINES = [
    'SYSTEM COMPROMISED',
    'UNAUTHORIZED INTRUSION TRACED',
    'YOUR LOCATION HAS BEEN LOGGED',
    'AUTHORITIES HAVE BEEN NOTIFIED',
    'CONNECTION TERMINATED',
]
MOD_KEYS = {pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL,
            pygame.K_LALT, pygame.K_RALT, pygame.K_CAPSLOCK, pygame.K_TAB,
            pygame.K_LSUPER, pygame.K_RSUPER, pygame.K_MENU, pygame.K_NUMLOCK,
            pygame.K_SCROLLOCK, pygame.K_MODE}


class App:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(300, 40)
        if sys.platform == 'emscripten':
            self.screen = pygame.display.set_mode((1280, 720))
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption('HACKERMAN')
        self.W, self.H = self.screen.get_size()
        self.clock = pygame.time.Clock()
        self.running = True
        self.banner_font = mono_font(28, bold=True)
        self.title_font = mono_font(14, bold=True)
        self.threat_font = mono_font(22, bold=True)
        self.bsod_sad_font = mono_font(90, bold=True)
        self.bsod_text_font = mono_font(20)
        self.bsod_small_font = mono_font(15)
        self.bsod_renderer = WindowsBlueScreen()

        self.matrix = Matrix(self)
        self._rain_veil = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self._rain_veil.fill((2, 9, 16, 130))
        self._layout_rects()
        # Keep the original four Window objects and their behavior.
        self.main = Terminal('root@hacksim: ~', self.main_rect,
                             prompt='root@hacksim:~$ ', cursor=True)
        self.phrases = Terminal('netcat://stream', self._grid(2), font_size=13)
        self.radar = Radar('NETWORK RADAR', self._grid(1))
        self.hex = HexDecoder('HEX DECODER', self._grid(3))

        self.main.threshold = 1
        self.main.closable = False
        self.phrases.threshold = 50
        self.radar.threshold = 100
        self.hex.threshold = 150
        self.radar.slot = 1
        self.phrases.slot = 2
        self.hex.slot = 3
        # Keep original z ordering and click-to-front functionality.
        self.windows = [self.phrases, self.radar, self.hex, self.main]
        self.code_pos = 0
        self._phrase_timer = 0.0
        self._burst_left = 15
        self._in_pause = False
        self.esc_count = 0
        self.access = None
        self.drag = None
        self.granted_count = 0
        self.denied_count = 0
        self.launch_timer = None
        self.compromise_timer = None
        self.frozen = False
        self.compromised_visual = False
        self.launched = False
        self.flash = 0.0
        self.bsod = False
        self.bsod_code = ''
        self.bsod_percent = 0.0
        self.elapsed = 0.0

    def _layout_rects(self):
        """Presentation-only layout: one big editor, three passive HUD panels."""
        margin = 22 if self.W >= 1050 else 13
        header = margin
        footer = margin
        avail_w = self.W - 2 * margin
        avail_h = self.H - header - footer
        # For desktop screens, grant the primary code terminal most of the area.
        primary_w = int((avail_w-GAP) * (.64 if self.W >= 1350 else .61))
        side_x = margin + primary_w + GAP
        side_w = avail_w - primary_w - GAP
        self.main_rect = pygame.Rect(margin, header, primary_w, avail_h)
        self.side_rect = pygame.Rect(side_x, header, side_w, avail_h)
        # Taller radar, plenty of readable area for event and hex panels.
        remainder = avail_h - GAP*2
        self.side_heights = [int(remainder*.40), int(remainder*.30), 0]
        self.side_heights[2] = remainder - sum(self.side_heights[:2])
        # Keep original grid dimensions as public attributes for compatibility.
        self.win_w = side_w
        self.win_h = self.side_heights[0]

    def _grid(self, slot):
        i = max(0, min(2, int(slot)-1))
        y = self.side_rect.y + sum(self.side_heights[:i]) + GAP*i
        return pygame.Rect(self.side_rect.x, y, self.side_rect.w,
                           self.side_heights[i])

    # ---- Original window manager ----
    def _window_at(self, pos):
        for w in reversed(self.windows):
            if w.visible and w.rect.collidepoint(pos):
                return w
        return None

    def _bring_to_front(self, w):
        self.windows.remove(w)
        self.windows.append(w)

    def _close(self, w):
        w.visible = False
        w.counter = 0
        w.reset()
        if w is self.phrases:
            self._phrase_timer = 0.0
            self._burst_left = 15
            self._in_pause = False

    def handle_mouse_down(self, pos):
        if self.frozen:
            return
        w = self._window_at(pos)
        if w is None:
            return
        self._bring_to_front(w)
        if w.closable and w.close_rect.collidepoint(pos):
            self._close(w)
            return
        if w.title_rect.collidepoint(pos):
            self.drag = (w, pos[0]-w.rect.x, pos[1]-w.rect.y)

    def handle_mouse_motion(self, pos):
        if self.drag:
            w, dx, dy = self.drag
            w.rect.x = pos[0]-dx
            w.rect.y = pos[1]-dy

    def handle_mouse_up(self, pos):
        self.drag = None

    # ---- Original ending conditions / timing ----
    def _all_open(self):
        return all(w.visible for w in self.windows)

    def _maybe_launch(self):
        if (self.granted_count >= 3 and self._all_open()
                and self.launch_timer is None and not self.launched
                and not self.compromised_visual):
            self.launch_timer = LAUNCH_DURATION

    def _maybe_compromise(self):
        if (self.denied_count >= 3 and self._all_open()
                and not self.launched and not self.compromised_visual):
            self.compromised_visual = True
            self.frozen = True
            self.launch_timer = None
            self.compromise_timer = 5.0
            for w in self.windows:
                w.compromised = True
                w.recolor()

    def _update_endings(self, dt):
        if self.launch_timer is not None:
            self.launch_timer -= dt
            if self.launch_timer <= 0:
                self.launch_timer = None
                self.launched = True
                self.flash = 0.6
        if self.flash > 0:
            self.flash = max(0., self.flash-dt)
            if self.flash <= 0.0 and self.launched:
                self._show_bsod('NUCLEAR_LAUNCH_DETECTED')
        if self.compromise_timer is not None:
            self.compromise_timer -= dt
            if self.compromise_timer <= 0:
                self.compromise_timer = None
                self._show_bsod('SYSTEM_COMPROMISED')

    def _show_bsod(self, code):
        self.bsod = True
        self.bsod_code = code
        self.bsod_percent = 0.0
        self.frozen = True

    # ---- Original input and unlock logic (global input, not UI focus) ----
    def _type_code(self):
        if self.code_pos >= len(CODE):
            self.code_pos = 0
            return
        self.main.add_text(CODE[self.code_pos:self.code_pos+4])
        self.code_pos += 4

    def handle_key(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self.esc_count += 1
            if self.esc_count >= 3:
                self.running = False
            return
        self.esc_count = 0
        if self.bsod:
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.access = None
            return
        if self.frozen:
            return
        if key in MOD_KEYS:
            return
        name = pygame.key.name(key)
        pressed = pygame.key.get_pressed()
        if name == 'q' and pressed[pygame.K_w]:
            self.access = ('ACCESS GRANTED', GREEN)
            self.granted_count += 1
            self._maybe_launch()
        if name == 'o' and pressed[pygame.K_p]:
            self.access = ('ACCESS DENIED', RED)
            self.denied_count += 1
            self._maybe_compromise()
        self._type_code()
        for w in self.windows:
            if not w.visible:
                w.counter += 1
                if w.counter >= w.threshold:
                    if w is not self.main:
                        w.rect = self._grid(w.slot)
                    w.visible = True

    # ---- Original auto-generated activity ----
    def update(self, dt):
        self.elapsed += dt
        if self.bsod:
            self.bsod_percent = min(100.0, self.bsod_percent+dt*5.)
            return
        self.matrix.update(dt)
        if not self.frozen:
            self._update_phrases(dt)
            for w in self.windows:
                if w.visible:
                    w.update(dt)
        self._update_endings(dt)

    def _update_phrases(self, dt):
        if not self.phrases.visible:
            return
        self._phrase_timer -= dt
        if self._phrase_timer > 0:
            return
        if self._in_pause:
            self._in_pause = False
            self._burst_left = 15
            self._phrase_timer = random.uniform(.05, .2)
        else:
            self.phrases.add_text(random.choice(PHRASES)+'\n')
            self._burst_left -= 1
            if self._burst_left <= 0:
                self._in_pause = True
                self._phrase_timer = random.uniform(.8,1.5)
            else:
                self._phrase_timer = random.uniform(.05,.2)

    # ---- Visual presentation (drawing-only) ----
    def draw(self, surface):
        if self.bsod:
            self._draw_bsod(surface)
            return
        surface.fill(BG)
        self.matrix.draw(surface)
        # Subdue the rain: atmospheric behind the terminal, never competing.
        surface.blit(self._rain_veil, (0, 0))
        for x in range(0, self.W, 56):
            pygame.draw.line(surface, (7, 30, 31), (x, 0), (x, self.H))
        for y in range(0, self.H, 56):
            pygame.draw.line(surface, (7, 30, 31), (0, y), (self.W, y))
        for w in self.windows:
            if w.visible:
                w.draw(surface)
        # Idle state is simply a visual instruction. A key still starts the game.
        if not self.main.visible:
            self._draw_welcome(surface)
        self._draw_access(surface)
        self._draw_launch(surface)
        self._draw_compromise(surface)
        if self.flash > 0:
            alpha = int(255 * min(1., self.flash/.6))
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((255, 255, 255, alpha))
            surface.blit(ov, (0, 0))

    def _draw_welcome(self, surface):
        r = self.main_rect
        ui.panel_fill(surface, r, active=True)
        ui.text(surface, '// HACKERMAN  /  ROOT SHELL', r.x+32, r.y+32, 12, ui.CYAN, True)
        big = mono_font(28, True).render('INITIALIZE SESSION', True, ui.WHITE)
        surface.blit(big, big.get_rect(center=(r.centerx, r.centery-42)))
        sub = mono_font(13).render('PRESS ANY KEY TO BEGIN', True, ui.GREEN)
        surface.blit(sub, sub.get_rect(center=(r.centerx, r.centery+8)))
        small = mono_font(11).render('INPUT  >  AUTOGENERATED KERNEL C SOURCE', True, ui.MUTED)
        surface.blit(small, small.get_rect(center=(r.centerx, r.centery+42)))
        pygame.draw.line(surface, ui.BORDER_ACTIVE,
                         (r.x+36, r.bottom-44), (r.right-36, r.bottom-44))
        ui.text(surface, 'UNAUTHORIZED USERS WELCOME', r.x+34, r.bottom-32,
                10, ui.GREEN_DIM)

    def _draw_access(self, surface):
        if self.access is None:
            return
        msg, color = self.access
        ui.centered_overlay(surface, msg,
                            ['AUTHENTICATION CHECK COMPLETE',
                             'SIGNATURE VALIDATED // SESSION OVERRIDE'],
                            tone=color, width=680, height=262)

    def _draw_trefoil(self, surface, cx, cy, radius):
        pygame.draw.circle(surface, YELLOW, (int(cx),int(cy)), int(radius))
        for base in (0,120,240):
            pts = [(int(cx),int(cy))]
            for deg in range(base-30,base+31,4):
                a = math.radians(deg)
                pts.append((int(cx+math.cos(a)*radius),
                            int(cy+math.sin(a)*radius)))
            pygame.draw.polygon(surface, BLACK, pts)
        pygame.draw.circle(surface, BLACK, (int(cx),int(cy)), int(radius*.14))
        pygame.draw.circle(surface, BLACK, (int(cx),int(cy)), int(radius),2)

    def _draw_launch(self, surface):
        if self.launch_timer is None and not self.launched:
            return
        if not self.launched:
            n = max(0,int(math.ceil(self.launch_timer)))
            message = f'LAUNCHING NUCLEAR WEAPONS IN {n}'
        else:
            message = 'LAUNCHED'
        ui.centered_overlay(surface, 'NUCLEAR LAUNCH',
                            [message, 'SIMULATED COUNTDOWN // CRITICAL SYSTEM ALERT'],
                            tone=RED, width=710, height=390, footer='')
        cx, cy = self.W//2, self.H//2 + 94
        self._draw_trefoil(surface, cx, cy, 30)

    def _draw_compromise(self, surface):
        if not self.compromised_visual:
            return
        ui.centered_overlay(surface, 'SYSTEM COMPROMISED',
                            THREAT_LINES, tone=RED, width=770, height=375,
                            footer='SIMULATED SECURITY INCIDENT')

    def _draw_bsod(self, surface):
        """Windows 10-style BSOD. Internal fictional codes remain unchanged."""
        self.bsod_renderer.draw(surface, self.bsod_percent, self.bsod_code)

    async def run(self):
        while self.running:
            dt = self.clock.tick(60)/1000.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_mouse_up(event.pos)
            self.update(dt)
            self.draw(self.screen)
            pygame.display.flip()
            await asyncio.sleep(0)
        pygame.quit()


async def main():
    app = App()
    await app.run()


if __name__ == '__main__':
    asyncio.run(main())
