"""The original generator-based Matrix rain, with a softer cyan/green palette.

Spawn rates, cascade physics, update cadence and character ranges match the
original project. This stays a background rather than a separate input mode.
"""
import random
import pygame
from fonts import mono_font

BG = (2, 7, 12)
GREEN = (41, 176, 106)
DIM_GREEN = (18, 70, 62)
WHITE = (154, 250, 223)
MAX_CASCADES = 300
MAX_COLS = 20
FRAME_DELAY = 0.04
MAX_SPEED = 5

def _getchars(start, end):
    return [chr(i) for i in range(start, end)]

CHARS = (_getchars(33, 127) +
         _getchars(913, 930) + _getchars(931, 938) +
         _getchars(945, 970) + _getchars(1040, 1104))

class Matrix:
    def __init__(self, app):
        self.app = app
        self.font = mono_font(16)
        self.char_w = self.font.size('0')[0] or 1
        self.char_h = self.font.get_linesize() or 1
        self.cols = max(1, app.W//self.char_w)
        self.rows = max(1, app.H//self.char_h)
        self.buffer = pygame.Surface((app.W, app.H))
        self.cascades = set()
        self.timer = 0.
        self._char_cache = {}
        self.reset()

    def reset(self):
        self.buffer.fill(BG)
        self.cascades.clear()
        self.timer = 0.

    def _put_char(self, char, col, row, color):
        key = (char, color)
        surf = self._char_cache.get(key)
        if surf is None:
            surf = pygame.Surface((self.char_w,self.char_h))
            surf.fill(BG)
            surf.blit(self.font.render(char,True,color),(0,0))
            self._char_cache[key] = surf
        self.buffer.blit(surf,(col*self.char_w,row*self.char_h))

    def _erase_char(self,col,row):
        self.buffer.fill(BG,(col*self.char_w,row*self.char_h,self.char_w,self.char_h))

    def _pareto(self,limit):
        scale = self.rows//2
        number = (random.paretovariate(1.16)-1)*scale
        return max(0,limit-number)

    @staticmethod
    def _update_line(speed,counter,line):
        counter += 1
        if counter >= speed:
            line += 1
            counter = 0
        return counter,line

    def _cascade(self,col):
        speed = random.randrange(1,MAX_SPEED)
        espeed = random.randrange(1,MAX_SPEED)
        line = counter = ecounter = 0
        oldline = eline = -1
        erasing = False
        bright = True
        limit = self._pareto(self.rows)
        while True:
            counter,line = self._update_line(speed,counter,line)
            if bright and random.randrange(10*speed)<1:
                bright = False
            if line>1 and line<=limit and oldline!=line:
                self._put_char(random.choice(CHARS),col,line-1,GREEN if bright else DIM_GREEN)
            if line < limit:
                self._put_char(random.choice(CHARS),col,line,WHITE if line>1 else GREEN)
            if erasing:
                ecounter,eline = self._update_line(espeed,ecounter,eline)
                self._erase_char(col,eline)
            else:
                erasing = random.randrange(line+1)>self.rows/2
                eline = 0
            yield
            oldline = line
            if eline >= limit:
                self._erase_char(col,oldline)
                return

    def _add_new(self):
        if random.randrange(MAX_CASCADES+1)>len(self.cascades):
            col=random.randrange(self.cols)
            for k in range(random.randrange(MAX_COLS)):
                self.cascades.add(self._cascade((col+k)%self.cols))
            return True
        return False

    def update(self,dt):
        self.timer+=dt
        while self.timer>=FRAME_DELAY:
            self.timer-=FRAME_DELAY
            while self._add_new():
                pass
            stopped=set()
            for c in list(self.cascades):
                try:
                    next(c)
                except StopIteration:
                    stopped.add(c)
            self.cascades.difference_update(stopped)

    def draw(self,surface):
        surface.blit(self.buffer,(0,0))
