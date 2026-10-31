"""HACKERMAN visual system. Only drawing helpers and colors live here.

No input handling, progression or game state is defined in this module.
"""
from __future__ import annotations
import math
from functools import lru_cache
import pygame
from fonts import mono_font

# Muted backgrounds with deliberate, bright highlights.
BG = (3, 8, 14)
BG_2 = (6, 15, 24)
PANEL = (7, 18, 27)
PANEL_INNER = (4, 12, 19)
TITLE_BG = (11, 27, 37)
GRID = (20, 43, 54)
BORDER = (31, 83, 93)
BORDER_ACTIVE = (48, 223, 176)
GREEN = (90, 247, 174)
GREEN_DIM = (43, 133, 111)
CYAN = (83, 218, 247)
AMBER = (255, 202, 106)
WHITE = (223, 246, 248)
MUTED = (104, 143, 154)
RED = (255, 84, 106)
PURPLE = (187, 152, 255)
BLUE = (110, 168, 255)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def text(surface, value, x, y, size=12, color=MUTED, bold=False):
    f = mono_font(size, bold=bold)
    s = f.render(str(value), True, color)
    surface.blit(s, (int(x), int(y)))
    return s.get_width()


def right_text(surface, value, right, y, size=12, color=MUTED, bold=False):
    f = mono_font(size, bold=bold)
    s = f.render(str(value), True, color)
    surface.blit(s, (int(right - s.get_width()), int(y)))
    return s.get_width()


@lru_cache(maxsize=16)
def _panel_shadow(w, h):
    """Reuse translucent shadows rather than allocating each animation frame."""
    shadow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 96), (12, 12, w, h), border_radius=8)
    return shadow


def panel_fill(surface, rect, active=False, alert=False):
    """Dark, subtly layered panel with glow confined to its edges."""
    r = pygame.Rect(rect)
    if r.w <= 2 or r.h <= 2:
        return
    base = (26, 11, 20) if alert else ((1, 9, 4) if active else PANEL)
    outline = RED if alert else (BORDER_ACTIVE if active else BORDER)
    surface.blit(_panel_shadow(r.w, r.h), (r.x - 3, r.y - 1))
    pygame.draw.rect(surface, base, r, border_radius=5)
    pygame.draw.rect(surface, outline, r, width=1, border_radius=5)
    if active:
        pygame.draw.rect(surface, mix(outline, BG, .67), r.inflate(4, 4), width=1, border_radius=7)
    # Sharp sci-fi edge anchors; these are intentionally drawn over rounded corners.
    anchor = min(15, r.w // 8, r.h // 8)
    if anchor > 2:
        for x, xd in ((r.left, 1), (r.right, -1)):
            for y, yd in ((r.top, 1), (r.bottom, -1)):
                pygame.draw.line(surface, outline, (x, y + yd * anchor), (x, y), 2)
                pygame.draw.line(surface, outline, (x, y), (x + xd * anchor, y), 2)


def backdrop(surface, t=0.0):
    """Static environmental detail, deliberately subtle behind live Matrix rain."""
    w, h = surface.get_size()
    surface.fill(BG)
    for x in range(0, w, 48):
        pygame.draw.line(surface, (8, 25, 31), (x, 0), (x, h))
    for y in range(0, h, 48):
        pygame.draw.line(surface, (8, 25, 31), (0, y), (w, y))
    for y in range(3, h, 5):
        pygame.draw.line(surface, (7, 16, 23), (0, y), (w, y))
    pygame.draw.line(surface, (25, 91, 86), (0, 0), (w, 0), 2)


def chrome(surface, rect, title, title_h, closable, close_rect, primary=False, alert=False):
    r = pygame.Rect(rect)
    panel_fill(surface, r, active=primary, alert=alert)
    head = pygame.Rect(r.x + 1, r.y + 1, r.w - 2, title_h)
    pygame.draw.rect(surface, (35, 14, 23) if alert else ((3, 22, 12) if primary else TITLE_BG), head, border_top_left_radius=4, border_top_right_radius=4)
    pygame.draw.line(surface, RED if alert else (BORDER_ACTIVE if primary else BORDER),
                     (r.x + 1, head.bottom), (r.right - 1, head.bottom))
    pygame.draw.rect(surface, RED if alert else (GREEN if primary else CYAN),
                     (r.x + 14, r.y + 13, 5, 5), border_radius=1)
    label_color = RED if alert else (GREEN if primary else CYAN)
    title_text = str(title) if primary else str(title).upper()
    max_chars = max(6, (r.w - 132) // 10)
    text(surface, title_text[:max_chars], r.x + 28, r.y + max(6, (title_h - 17)//2), 13, label_color, True)
    if r.w > 250:
        # Small status display; no state change or input behavior.
        status = "PTY CONNECTED" if primary else "LIVE FEED"
        status_color = GREEN if primary else MUTED
        sx = r.right - (115 if closable else 123)
        text(surface, status, sx, r.y + max(9, (title_h - 12)//2), 9, status_color, True)
    if closable:
        cr = close_rect
        hover = cr.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, (92, 27, 39) if hover else (25, 38, 49), cr, border_radius=3)
        color = WHITE if hover else MUTED
        cx, cy = cr.center
        pygame.draw.line(surface, color, (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
        pygame.draw.line(surface, color, (cx - 4, cy + 4), (cx + 4, cy - 4), 2)


def tiny_meter(surface, x, y, w, value, color=GREEN, label=None):
    w = max(8, int(w))
    pygame.draw.rect(surface, GRID, (x, y, w, 4), border_radius=2)
    pygame.draw.rect(surface, color, (x, y, max(1, int(w * max(0, min(1, value)))), 4), border_radius=2)
    if label:
        text(surface, label, x, y - 16, 9, MUTED)


def centered_overlay(surface, heading, lines, tone=GREEN, width=620, height=254, footer="PRESS ENTER TO DISMISS"):
    sw, sh = surface.get_size()
    cover = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cover.fill((1, 5, 10, 202))
    surface.blit(cover, (0, 0))
    r = pygame.Rect(0, 0, min(width, sw-42), min(height, sh-42))
    r.center = (sw//2, sh//2)
    panel_fill(surface, r, active=True, alert=(tone == RED))
    pygame.draw.rect(surface, TITLE_BG, (r.x+1, r.y+1, r.w-2, 45))
    pygame.draw.line(surface, tone, (r.x+1, r.y+45), (r.right-1, r.y+45), 2)
    text(surface, "HACKERMAN // SECURITY EVENT", r.x+22, r.y+15, 12, MUTED, True)
    head_font = mono_font(28, True)
    heading_surf = head_font.render(heading, True, tone)
    surface.blit(heading_surf, heading_surf.get_rect(center=(r.centerx, r.y+94)))
    for i, line in enumerate(lines):
        f = mono_font(13)
        s = f.render(line, True, WHITE if i == 0 else MUTED)
        surface.blit(s, s.get_rect(center=(r.centerx, r.y+141+i*22)))
    if footer:
        f = mono_font(10)
        s = f.render(footer, True, tone)
        surface.blit(s, s.get_rect(center=(r.centerx, r.bottom-24)))
