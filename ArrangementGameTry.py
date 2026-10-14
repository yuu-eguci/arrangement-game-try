"""ArrangementGameTry

pygameお試し作品。
床と椅子を置ける。
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pygame
from pygame.locals import (
    K_BACKSPACE,
    K_DOWN,
    K_F4,
    K_LEFT,
    K_RIGHT,
    K_UP,
    KEYDOWN,
    KEYUP,
    KMOD_ALT,
    MOUSEBUTTONDOWN,
    QUIT,
    RLEACCEL,
    K_a,
    K_c,
    K_l,
    K_p,
    K_s,
    K_x,
    K_z,
)

import accept_mouse_click

_HERE = Path(__file__).resolve().parent
_IMG_FOLDER = _HERE / "01_img"
_MUSIC_FOLDER = _HERE / "02_music"
LAYOUT_FILE = _HERE / "layout.json"
SCREENSHOT_FOLDER = _HERE

SCREEN_SIZE = (640, 480)
COLUMNS = 10
ROWS = 5
base_pos = (20, 60)
ARROWS = (K_UP, K_DOWN, K_LEFT, K_RIGHT)
NEXT_ITEM_POS = (10, -30)  # 左上に次に置くアイテムを見せる
NEXT_ITEM_RECT = pygame.Rect(10, 0, 80, 100)
UNDO_LIMIT = 500


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


def square_at(
    pos,
):  # クリックした場所のマス。ひし形は絵の (40, 102) を中心に横 80 縦 40
    for x in range(1, COLUMNS + 1):
        for y in range(1, ROWS + 1):
            left, top = coordinates((x, y))
            if abs(pos[0] - left - 40) / 40 + abs(pos[1] - top - 102) / 20 <= 1:
                return (x, y)
    return None


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


def _no_duplicate_keys(pairs):  # 同じマスが 2 回書いてある JSON は受け付けない
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("duplicate key")
    return dict(pairs)


# {"1,1": "brown_floor1"} を {(1, 1): "brown_floor1"} に戻す
def read_layer(layer, item):
    if not isinstance(layer, dict):
        raise ValueError(layer)
    squares = {}
    for key, name in layer.items():
        if not re.fullmatch(r"[1-9][0-9]?,[1-9][0-9]?", key):
            raise ValueError(key)
        x, y = (int(n) for n in key.split(","))
        if not (1 <= x <= COLUMNS and 1 <= y <= ROWS):
            raise ValueError(key)
        if name not in [f"{item}{roll}" for roll in range(1, 5)]:
            raise ValueError(name)
        squares[(x, y)] = name
    return squares


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
        self.history = []  # Backspace で戻すための、変える前の床と椅子と矢印の場所

    def handle_key(self, key):
        if key == K_BACKSPACE:
            self.undo()
            return
        before = (dict(self.floors), dict(self.chairs))
        if key in ARROWS:
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
        elif key == K_s:
            self.save()
        elif key == K_l:
            self.load()
        if (self.floors, self.chairs) != before:
            self.history.append((*before, self.cursor))
            del self.history[:-UNDO_LIMIT]

    def undo(self):
        if self.history:
            self.floors, self.chairs, self.cursor = self.history.pop()
            self.sounds["switch"].play()

    # ディクショナリをそのまま JSON にしまっておく
    def save(self):
        layout = {
            "floors": {f"{x},{y}": name for (x, y), name in self.floors.items()},
            "chairs": {f"{x},{y}": name for (x, y), name in self.chairs.items()},
        }
        try:
            LAYOUT_FILE.write_text(json.dumps(layout, indent=2) + "\n")
        except OSError as error:
            print(f"Could not save layout: {error}")
            return
        self.sounds["switch"].play()

    def load(self):
        try:
            layout = json.loads(
                LAYOUT_FILE.read_text(), object_pairs_hook=_no_duplicate_keys
            )
            floors = read_layer(layout["floors"], "brown_floor")
            chairs = read_layer(layout["chairs"], "green_chair")
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
            print(f"Could not load layout: {error}")
            return
        self.floors, self.chairs = floors, chairs
        self.sounds["switch"].play()

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

    def draw_next_item(self, screen):  # C で向きを変えたらここに出る
        screen.blit(self.brown_floor[(self.roll - 1) % 2], NEXT_ITEM_POS)
        screen.blit(self.green_chair[self.roll - 1], NEXT_ITEM_POS)


def save_screenshot(screen):
    stem = f"screenshot-{datetime.now():%Y%m%d-%H%M%S}"
    path = SCREENSHOT_FOLDER / f"{stem}.png"
    number = 1
    while path.exists():  # 同じ秒に撮っても上書きしない
        number += 1
        path = SCREENSHOT_FOLDER / f"{stem}-{number}.png"
    try:
        pygame.image.save(screen, path)
    except (OSError, pygame.error) as error:
        print(f"Could not save screenshot: {error}")
        return False
    return True


def main():
    pygame.init()
    pygame.display.set_icon(
        pygame.image.load(_IMG_FOLDER / "green_chair.png").subsurface((3, 38, 76, 76))
    )
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.key.set_repeat(300, 80)
    pygame.display.set_caption("Arrangement game")
    game = Game(load_images(), load_sounds())
    clock = pygame.time.Clock()
    held = set()  # 押しっぱなしで繰り返すのは矢印だけにする
    while True:
        game.frame += 1
        game.draw(screen)
        game.draw_next_item(screen)
        for event in pygame.event.get():
            if event.type == KEYUP:
                held.discard(event.key)
            elif event.type == KEYDOWN:
                if event.key in held and event.key not in ARROWS:
                    continue
                held.add(event.key)
            # クリックしたマスがあれば、矢印をそこへ動かしてから Z / A / X にする
            if event.type == MOUSEBUTTONDOWN and event.button in (1, 2, 3):
                game.cursor = square_at(event.pos) or game.cursor
            # macに対応。
            event = accept_mouse_click.switch(event, scroll_click=K_a)

            if event.type == QUIT or (
                event.type == KEYDOWN and event.key == K_F4 and event.mod & KMOD_ALT
            ):
                pygame.quit()
                return
            if event.type == KEYDOWN and event.key == K_p:
                if save_screenshot(screen):
                    game.sounds["switch"].play()
            elif event.type == KEYDOWN:
                game.handle_key(event.key)
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
