"""Behavior regression tests, runnable without a graphical display or pygame.

They install a minimal pygame shim and exercise the *real* main.py and widget
classes. These tests validate progression and interactions, not pixel output.
"""
import importlib
import os
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            a = args[0]
            args = (a.x, a.y, a.w, a.h) if isinstance(a, Rect) else tuple(a)
        self.x, self.y, self.w, self.h = map(int, args)

    @property
    def right(self): return self.x+self.w
    @property
    def bottom(self): return self.y+self.h
    @property
    def left(self): return self.x
    @property
    def top(self): return self.y
    @property
    def centerx(self): return self.x+self.w//2
    @property
    def centery(self): return self.y+self.h//2
    @property
    def center(self): return (self.centerx, self.centery)
    @center.setter
    def center(self, pos):
        self.x = int(pos[0]-self.w//2)
        self.y = int(pos[1]-self.h//2)
    def collidepoint(self, *p):
        x, y = p[0] if len(p)==1 else p
        return self.x<=x<self.right and self.y<=y<self.bottom
    def inflate(self, a, b):
        return Rect(self.x-a//2,self.y-b//2,self.w+a,self.h+b)


class DummySurface:
    def __init__(self, size, flags=0): self.size = size
    def fill(self, *args, **kwargs): pass
    def blit(self, *args, **kwargs): pass
    def set_clip(self, *args): pass
    def get_clip(self): return Rect(0,0,*self.size)
    def get_size(self): return self.size
    def get_width(self): return self.size[0]
    def get_height(self): return self.size[1]
    def get_rect(self, **kwargs):
        r=Rect(0,0,*self.size)
        if 'center' in kwargs: r.center=kwargs['center']
        return r


class DummyFont:
    def __init__(self, path, size): self.px=size
    def get_linesize(self): return int(self.px*1.30)
    def size(self, line): return (max(1,int(len(str(line))*self.px*.62)), self.px)
    def render(self, line, antialias, color): return DummySurface(self.size(line))
    def set_bold(self, val): pass


pygame=types.ModuleType('pygame')
pygame.Rect=Rect
pygame.Surface=DummySurface
pygame.SRCALPHA=1
pygame.FULLSCREEN=2
pygame.QUIT=10
pygame.KEYDOWN=11
pygame.MOUSEBUTTONDOWN=12
pygame.MOUSEBUTTONUP=13
pygame.MOUSEMOTION=14
for n,k in enumerate('LSHIFT RSHIFT LCTRL RCTRL LALT RALT CAPSLOCK TAB LSUPER RSUPER MENU NUMLOCK SCROLLOCK MODE ESCAPE RETURN KP_ENTER q w p o a'.split(), 100):
    setattr(pygame,'K_'+k,n)
pygame.init=lambda: None
pygame.quit=lambda: None
pygame.time=types.SimpleNamespace(Clock=lambda: types.SimpleNamespace(tick=lambda fps: 16),get_ticks=lambda: 600)
pygame.display=types.SimpleNamespace(set_mode=lambda mode, flags=0: DummySurface((1366,768) if mode==(0,0) else mode),set_caption=lambda title:None,flip=lambda:None)
pygame.font=types.SimpleNamespace(Font=DummyFont,match_font=lambda *args, **kwargs:None)
pygame.image=types.SimpleNamespace(load=lambda path: DummySurface((128, 128)))
pygame.transform=types.SimpleNamespace(scale=lambda surf, size: DummySurface(size))
pygame.mouse=types.SimpleNamespace(get_pos=lambda:(-100,-100))
pygame.event=types.SimpleNamespace(get=lambda:[])
pygame.draw=types.SimpleNamespace(rect=lambda *a,**k:None,
                                  circle=lambda *a,**k:None,
                                  line=lambda *a,**k:None,
                                  polygon=lambda *a,**k:None)
_pressed=set()
pygame.key=types.SimpleNamespace(set_repeat=lambda *args:None,
                                 name=lambda k:{pygame.K_q:'q',pygame.K_o:'o'}.get(k,'a'),
                                 get_pressed=lambda: _Pressed(),)
class _Pressed:
    def __getitem__(self, key): return key in _pressed

# Test shim used only by this test file; the distributed game imports real pygame.
sys.modules['pygame']=pygame
import main


class GameLogicTests(unittest.TestCase):
    def setUp(self):
        _pressed.clear()
        self.app = main.App()

    def type_keys(self, n):
        for _ in range(n):
            self.app.handle_key(types.SimpleNamespace(key=pygame.K_a))

    def test_unlock_sequence_and_primary_input(self):
        self.assertEqual([w.visible for w in (self.app.main,self.app.phrases,self.app.radar,self.app.hex)],
                         [False]*4)
        self.type_keys(1)
        self.assertTrue(self.app.main.visible)
        self.assertFalse(self.app.phrases.visible)
        self.assertTrue(self.app.main.text.startswith('root@hacksim:~$ /str'))
        self.type_keys(48)
        self.assertFalse(self.app.phrases.visible)
        self.type_keys(1)
        self.assertTrue(self.app.phrases.visible)
        self.type_keys(50)
        self.assertTrue(self.app.radar.visible)
        self.type_keys(50)
        self.assertTrue(self.app.hex.visible)
        self.assertEqual(self.app.code_pos, 150*4)

    def test_side_panel_click_never_steals_code_input(self):
        self.type_keys(150)
        before = self.app.main.text
        pos = self.app.radar.title_rect.center
        self.app.handle_mouse_down(pos)
        self.app.handle_mouse_up(pos)
        self.assertIs(self.app.windows[-1], self.app.radar)
        self.type_keys(1)
        self.assertNotEqual(before, self.app.main.text)

    def test_closing_and_reopening_side_panel(self):
        self.type_keys(50)
        cr=self.app.phrases.close_rect.center
        self.app.handle_mouse_down(cr)
        self.assertFalse(self.app.phrases.visible)
        self.assertEqual(self.app.phrases.counter,0)
        self.type_keys(50)
        self.assertTrue(self.app.phrases.visible)
        self.assertEqual(self.app.phrases.rect.x, self.app.side_rect.x)

    def test_granted_triggers_unchanged_countdown(self):
        self.type_keys(150)
        _pressed.add(pygame.K_w)
        for i in range(3):
            self.app.handle_key(types.SimpleNamespace(key=pygame.K_q))
        self.assertEqual(self.app.granted_count,3)
        self.assertEqual(self.app.launch_timer,10.)
        self.app.update(10.1)
        self.assertTrue(self.app.launched)
        self.app.update(.7)
        self.assertTrue(self.app.bsod)
        self.assertEqual(self.app.bsod_code,'NUCLEAR_LAUNCH_DETECTED')

    def test_denied_triggers_unchanged_compromise(self):
        self.type_keys(150)
        _pressed.add(pygame.K_p)
        for i in range(3):
            self.app.handle_key(types.SimpleNamespace(key=pygame.K_o))
        self.assertTrue(self.app.frozen)
        self.assertTrue(self.app.compromised_visual)
        self.assertTrue(all(w.compromised for w in self.app.windows))
        self.app.update(5.1)
        self.assertEqual(self.app.bsod_code,'SYSTEM_COMPROMISED')

    def test_escape_three_times(self):
        for _ in range(2):
            self.app.handle_key(types.SimpleNamespace(key=pygame.K_ESCAPE))
        self.assertTrue(self.app.running)
        self.app.handle_key(types.SimpleNamespace(key=pygame.K_ESCAPE))
        self.assertFalse(self.app.running)

    def test_c_terminal_is_monochrome_and_without_ide_chrome(self):
        self.type_keys(20)
        # The primary output never tokenizes keywords in different colors.
        line = 'static int x = 42; /* C code */'
        surf = self.app.main._cached_line(line)
        self.assertEqual(surf.get_size()[0], self.app.main.font.size(line)[0])
        self.assertFalse(hasattr(self.app.main, '_syntax_pieces'))

    def test_hidden_game_state_vs_visible_windows_stop_code(self):
        from bsod_screen import WINDOWS_STOP_CODES, BLUE, QR_PATH
        self.assertEqual(BLUE, (0, 120, 215))
        self.assertTrue(QR_PATH.exists())
        self.assertEqual(WINDOWS_STOP_CODES['SYSTEM_COMPROMISED'],
                         'SYSTEM_SERVICE_EXCEPTION')
        self.type_keys(150)
        self.app._show_bsod('SYSTEM_COMPROMISED')
        self.assertEqual(self.app.bsod_code, 'SYSTEM_COMPROMISED')

    def test_removed_overlay_headings_and_stats(self):
        import ui_theme
        self.assertFalse(hasattr(ui_theme, 'frame_header'))
        self.assertFalse(hasattr(ui_theme, 'frame_footer'))
        from pathlib import Path
        top = (Path(__file__).resolve().parents[1] / 'main.py').read_text()
        self.assertNotIn('frame_header(', top)
        self.assertNotIn('frame_footer(', top)

    def test_rendering_smoke_all_windows_and_endings(self):
        self.type_keys(160)
        for i in range(6): self.app.update(.4)
        self.app.draw(self.app.screen)
        self.app.access=('ACCESS GRANTED',main.GREEN)
        self.app.draw(self.app.screen)
        self.app.launch_timer=9.
        self.app.draw(self.app.screen)
        self.app.compromised_visual=True
        self.app.draw(self.app.screen)
        self.app._show_bsod('SYSTEM_COMPROMISED')
        self.app.draw(self.app.screen)


if __name__=='__main__':
    unittest.main()
