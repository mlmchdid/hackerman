"""Radar: original simulated blip state with richer HUD/sonar rendering."""
import math
import random
import pygame
from fonts import mono_font
from terminal import Window
import ui_theme as ui

GREEN = ui.GREEN
DIM_GREEN = ui.GREEN_DIM
SWEEP = ui.CYAN
RED = ui.RED
RED_DIM = (107, 36, 49)
RED_SWEEP = (255, 115, 128)


class Radar(Window):
    def __init__(self, title, rect):
        super().__init__(title, rect)
        self.label_font = mono_font(10)
        self.angle = 0.0
        self.blips = []
        self.elapsed = 0.0

    def reset(self):
        self.angle = 0.0
        self.blips = []
        self.elapsed = 0.0

    def _center_radius(self):
        r = self.rect
        content_height = r.h - self.title_h - 32
        radius = max(10, min(content_height // 2 - 8, int(r.w * .22)))
        cx = r.x + max(60, min(int(r.w*.30), radius + 26))
        cy = r.y + self.title_h + content_height // 2 + 7
        return cx, cy, radius

    def _pal(self):
        return (RED, RED_DIM, RED_SWEEP) if self.compromised else (GREEN, DIM_GREEN, SWEEP)

    def update(self, dt):
        self.elapsed += dt
        self.angle = (self.angle + dt * 55) % 360.0
        if random.random() < dt * 2.5:
            self.blips.append([random.uniform(-0.9, 0.9),
                               random.uniform(-0.9, 0.9),
                               random.choice(('TARGET', 'DATA')),
                               random.randint(1000, 999999),
                               0.0, random.uniform(3.0, 6.0)])
        for b in self.blips:
            b[4] += dt
        self.blips = [b for b in self.blips if b[4] < b[5]]

    def draw(self, surface):
        self._draw_chrome(surface)
        r = self.rect
        if r.h < 115 or r.w < 165:
            return
        fg, dim, sweep = self._pal()
        cx, cy, radius = self._center_radius()
        pygame.draw.rect(surface, ui.PANEL_INNER,
                         (r.x+1, r.y+self.title_h+1, r.w-2, 24))
        ui.text(surface, '● ACTIVE SCAN    /    SWEEP 055°/S',
                r.x+15, r.y+self.title_h+7, 10, ui.GREEN_DIM, True)
        pygame.draw.circle(surface, mix_color(dim, ui.PANEL, .5), (cx, cy), radius)
        for frac in (.25, .50, .75, 1.0):
            pygame.draw.circle(surface, dim, (cx, cy), max(1, int(radius*frac)), 1)
        pygame.draw.line(surface, dim, (cx-radius, cy), (cx+radius, cy))
        pygame.draw.line(surface, dim, (cx, cy-radius), (cx, cy+radius))
        for k in range(0, 360, 30):
            a = math.radians(k)
            pygame.draw.line(surface, dim,
                             (cx+int(math.cos(a)*(radius-5)), cy+int(math.sin(a)*(radius-5))),
                             (cx+int(math.cos(a)*radius), cy+int(math.sin(a)*radius)))
        # Sweeping translucent fan gives a hologram feel without changing the blip logic.
        glow = pygame.Surface((2*radius+4, 2*radius+4), pygame.SRCALPHA)
        gc = (radius+2, radius+2)
        for step in range(18, 0, -1):
            a = math.radians(self.angle-step*2.2)
            b = math.radians(self.angle-(step-1)*2.2)
            poly = [gc,
                    (gc[0]+int(radius*math.cos(a)), gc[1]+int(radius*math.sin(a))),
                    (gc[0]+int(radius*math.cos(b)), gc[1]+int(radius*math.sin(b)))]
            pygame.draw.polygon(glow, (*sweep, max(3, int(40-step*1.5))), poly)
        surface.blit(glow, (cx-radius-2, cy-radius-2))
        a = math.radians(self.angle)
        pygame.draw.line(surface, sweep, (cx, cy),
                         (cx+int(math.cos(a)*radius), cy+int(math.sin(a)*radius)), 2)
        pygame.draw.circle(surface, fg, (cx, cy), 3)
        pygame.draw.circle(surface, fg, (cx, cy), radius, 1)

        surface.set_clip(pygame.Rect(r.x+2, r.y+self.title_h+25,
                                     r.w-4, r.h-self.title_h-50))
        for fx, fy, kind, idnum, age, life in self.blips:
            alpha = max(.1, 1-age/life)
            base = (255, 239, 187) if kind == 'TARGET' else fg
            if self.compromised:
                base = RED
            c = tuple(int(v*alpha) for v in base)
            px = cx+int(fx*radius)
            py = cy+int(fy*radius)
            pygame.draw.circle(surface, c, (px, py), 3)
            if kind == 'TARGET':
                pygame.draw.circle(surface, c, (px, py), 7, 1)
            # Keep labels from obscuring the compass on tiny screens.
            if r.w >= 350:
                ui.text(surface, f'{idnum}', px+9, py-5, 9, c)
        surface.set_clip(None)
        info_x = r.x + max(145, int(r.w*.59))
        if info_x < r.right - 95:
            ui.text(surface, 'NETWORK TELEMETRY', info_x,
                    r.y+self.title_h+39, 10, ui.CYAN, True)
            ui.text(surface, 'ACTIVE TARGETS', info_x,
                    r.y+self.title_h+65, 9, ui.MUTED)
            ui.text(surface, f'{len(self.blips):02d}', info_x,
                    r.y+self.title_h+77, 22, fg, True)
            ui.text(surface, 'SCAN ANGLE', info_x,
                    r.y+self.title_h+112, 9, ui.MUTED)
            ui.text(surface, f'{int(self.angle):03d} DEG', info_x,
                    r.y+self.title_h+127, 13, ui.WHITE)
            if r.h >= 240:
                ui.text(surface, 'PACKET UPLINK', info_x,
                        r.y+self.title_h+158, 9, ui.MUTED)
                ui.tiny_meter(surface, info_x, r.y+self.title_h+174,
                              min(150, r.right-info_x-20),
                              (math.sin(self.elapsed*3)+1)/2, fg)
        fy = r.bottom-26
        pygame.draw.rect(surface, ui.PANEL_INNER, (r.x+1, fy, r.w-2, 25))
        pygame.draw.line(surface, ui.GRID, (r.x, fy), (r.right, fy))
        ui.text(surface, '●  NODES DISCOVERED', r.x+14, fy+7, 9, fg)
        ui.right_text(surface, 'SIGNAL // STABLE', r.right-14, fy+7, 9, ui.MUTED)


def mix_color(a, b, frac):
    return tuple(int(a[i]*(1-frac)+b[i]*frac) for i in range(3))
