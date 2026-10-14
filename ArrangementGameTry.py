"""ArrangementGameTry

pygameお試し作品。
床と椅子を置ける。
"""

from pathlib import Path

import pygame
from pygame.locals import (
    K_DOWN,
    K_F4,
    K_LEFT,
    K_RIGHT,
    K_UP,
    KEYDOWN,
    KMOD_ALT,
    QUIT,
    RLEACCEL,
    K_a,
    K_c,
    K_x,
    K_z,
)

import accept_mouse_click

_HERE = Path(__file__).resolve().parent
_IMG_FOLDER = _HERE / "01_img"
_MUSIC_FOLDER = _HERE / "02_music"

SCREEN_SIZE = (640, 480)
COLUMNS = 10
ROWS = 5
base_pos = (20, 60)


# 画像ロード
def load_images():
    return {
        name: pygame.image.load(_IMG_FOLDER / f"{name}.png").convert_alpha()
        for name in ("base0", "yajirushi", "brown_floor", "green_chair")
    }


class _SilentSound:  # サウンドデバイスがないときの代役
    def play(self):
        pass

    def set_volume(self, volume):
        pass


# サウンドロード
def load_sounds():
    sounds = {
        name: pygame.mixer.Sound(_MUSIC_FOLDER / f"{name}.ogg")
        if pygame.mixer.get_init()
        else _SilentSound()
        for name in ("switch", "switch2")
    }
    sounds["switch2"].set_volume(0.2)
    return sounds


# アニメーション用画像分割320x130用
def split_320x130(img):
    img_lis = []
    for foo in range(0, 320, 80):
        surface = pygame.Surface((80, 130))
        surface.blit(img, (0, 0), (foo, 0, 80, 130))
        surface.set_colorkey(surface.get_at((0, 0)), RLEACCEL)
        img_lis.append(surface)
    return img_lis


def coordinates(a):  # (1, 3) とか書くと 1 列目 3 行目のマスの左上座標を返してくれる
    x, y = a
    return (
        40 * (x - 1) + 40 * (y - 1) + base_pos[0],
        80 + 20 * (x - 1) - 20 * (y - 1) + base_pos[1],
    )


def move_cursor(pos, key):  # 矢印を上下左右で動かす 端まで行くと反対側へ
    x, y = pos
    if key == K_UP:
        y = y % ROWS + 1
    elif key == K_DOWN:
        y = (y - 2) % ROWS + 1
    elif key == K_LEFT:
        x = (x - 2) % COLUMNS + 1
    elif key == K_RIGHT:
        x = x % COLUMNS + 1
    return (x, y)


def next_roll(roll):
    return roll % 4 + 1


class Game:
    def __init__(self, images, sounds):
        self.base0 = images["base0"]
        self.yajirushi = split_320x130(images["yajirushi"])
        self.brown_floor = split_320x130(images["brown_floor"])
        self.green_chair = split_320x130(images["green_chair"])
        self.sounds = sounds
        # 50マス(フロア)と50マス(表層) ディクショナリにはアイテムがあるマスだけ入る
        self.floors = {}
        self.chairs = {}
        self.cursor = (1, 1)
        self.roll = 1
        self.frame = 0

    def handle_key(self, key):
        if key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
            self.cursor = move_cursor(self.cursor, key)
            self.sounds["switch2"].play()
        # --- Zでアイテムを張る Xでアイテムを剥がす Cでアイテムの向きを変える
        elif key == K_z:
            self.floors[self.cursor] = f"brown_floor{self.roll}"
            self.sounds["switch"].play()
        elif key == K_a:
            self.chairs[self.cursor] = f"green_chair{self.roll}"
            self.sounds["switch"].play()
        elif key == K_x:
            if self.cursor in self.chairs:
                del self.chairs[self.cursor]
            else:
                self.floors.pop(self.cursor, None)
            self.sounds["switch"].play()
        elif key == K_c:
            self.roll = next_roll(self.roll)

    def draw(self, screen):
        screen.fill((230, 230, 230))
        # 基礎を敷く
        for y in range(1, ROWS + 1):
            for x in range(1, COLUMNS + 1):
                screen.blit(self.base0, coordinates((x, y)))
        # 床の絵は 1,3 と 2,4 が同じ向き
        for y in range(1, ROWS + 1):
            for x in range(1, COLUMNS + 1):
                if (x, y) in self.floors:
                    image = self.brown_floor[(int(self.floors[(x, y)][-1]) - 1) % 2]
                    screen.blit(image, coordinates((x, y)))
        # 椅子は奥から順に描く
        for x in range(1, COLUMNS + 1):
            for y in range(ROWS, 0, -1):
                if (x, y) in self.chairs:
                    image = self.green_chair[int(self.chairs[(x, y)][-1]) - 1]
                    screen.blit(image, coordinates((x, y)))
        screen.blit(self.yajirushi[self.frame // 6 % 4], coordinates(self.cursor))


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Arrangement game")
    game = Game(load_images(), load_sounds())
    clock = pygame.time.Clock()
    while True:
        game.frame += 1
        game.draw(screen)
        for event in pygame.event.get():
            # macに対応。
            event = accept_mouse_click.switch(event, scroll_click=K_a)

            if event.type == QUIT or (
                event.type == KEYDOWN and event.key == K_F4 and event.mod & KMOD_ALT
            ):
                pygame.quit()
                return
            if event.type == KEYDOWN:
                game.handle_key(event.key)
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
