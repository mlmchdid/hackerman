"""Load fonts by preference, gracefully falling back when bundled TTFs are absent.

If the original repository's DejaVuSansMono files are present, they are used.
No font binaries are redistributed with this visual modification.
"""
from functools import lru_cache
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent

@lru_cache(maxsize=48)
def mono_font(size, bold=False):
    name = 'DejaVuSansMono-Bold.ttf' if bold else 'DejaVuSansMono.ttf'
    path = ROOT / "assets" / "fonts" / name
    if path.exists():
        return pygame.font.Font(str(path), size)
    match = pygame.font.match_font('dejavusansmono', bold=bold)
    if match:
        return pygame.font.Font(match, size)
    font = pygame.font.Font(None, size)
    font.set_bold(bool(bold))
    return font
