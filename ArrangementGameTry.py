# coding: utf-8

'''ArrangementGameTry

pygameお試し作品。
床と椅子を置ける。

========================================
バージョン1.0(2015-08-12)
    完成。
バージョン1.1(2017-09-22)
    久々に開いてdocとか書いた。
    macで開けないと面倒なので、macでも開けて簡単な動作なら見れるようにした。
    あとフォルダの名前の定数化とか。
    昔を懐かしむ意味もこめてリファクタリングはしない。
'''

import pygame, sys
from pygame.locals import *
import os
import accept_mouse_click

_IMG_FOLDER = '01_img'
_MUSIC_FOLDER = '02_music'

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption('Arrangement game')

# 画像ロード
def img(a):
    return pygame.image.load(_IMG_FOLDER + os.sep + a + '.png').convert_alpha()
base0 = img('base0')
yajirushi = img('yajirushi')
brown_floor = img('brown_floor')
green_chair = img('green_chair')

# サウンドロード
se_switch = pygame.mixer.Sound(f'{_MUSIC_FOLDER}{os.sep}switch.ogg')
se_switch2 = pygame.mixer.Sound(f'{_MUSIC_FOLDER}{os.sep}switch2.ogg')
se_switch2.set_volume(0.2)
se_switch2.set_volume(0.2)

# pygame.mixer.music.load(f'music{os.sep}cave.mp3')
# pygame.mixer.music.set_volume(0.5)
# pygame.mixer.music.play(-1)

row1 = [(0,80), (40,100), (80,120), (120,140), (160,160), (200,180), (240,200), (280,220), (320,240), (360,260)]
row2 = [(40,60), (80,80), (120,100), (160,120), (200,140), (240,160), (280,180), (320,200), (360,220), (400,240)]
row3 = [(80,40), (120,60), (160,80), (200,100), (240,120), (280,140), (320,160), (360,180), (400,200), (440,220)]
row4 = [(120,20), (160,40), (200,60), (240,80), (280,100), (320,120), (360,140), (400,160), (440,180), (480,200)]
row5 = [(160,0), (200,20), (240,40), (280,60), (320,80), (360,100), (400,120), (440,140), (480,160), (520,180)]

# 基礎を敷く
def put_base(a): # aはいちばん左上の座標
    def foo(b):
        x = a[0] + b[0]
        y = a[1] + b[1]
        return screen.blit(base0, (x,y))
    for c in range(10): foo(row1[c])
    for c in range(10): foo(row2[c])
    for c in range(10): foo(row3[c])
    for c in range(10): foo(row4[c])
    for c in range(10): foo(row5[c])

# アニメーション用画像分割320x130用
def split_320x130(img):
    img_lis = []
    for foo in range(0, 320, 80):
        surface = pygame.Surface((80,130))
        surface.blit(img, (0,0), (foo,0,80,130))
        surface.set_colorkey(surface.get_at((0,0)), RLEACCEL)
        surface.convert()
        img_lis.append(surface)
    return img_lis

def yajirushi_anime(yaji_pos, frame):
    clock.tick(60)
    images = split_320x130(yajirushi)
    return screen.blit(images[frame // 6 % 4], yaji_pos)

def coordinates(a): # 1,3 とか書くと row1[2] を返してくれる
    b = eval('row' + str(a[1]))[a[0] - 1]
    return (b[0]+base_pos[0], b[1]+base_pos[1])

# 50マス(フロア)すべてに変数を割り振る 奥義・変数自動生成!
dic_50square = {}
for foo in range(1, 11): # x軸
    for bar in range(1, 6): # y軸
        dic_50square['50square[' + str(foo) + ', ' + str(bar) + ']'] = ''

# 50マス(表層)すべてに変数を割り振る
dic_50square1 = {}
for foo in range(1, 11):
    for bar in range(1, 6):
        dic_50square1['50square1[' + str(foo) + ', ' + str(bar) + ']'] = ''

def fill_50square(foo, bar):# 50square(フロア)の変数に格納されてる文字列に対応した絵を blit し続ける
    images_brown_floor = split_320x130(brown_floor)
    baz = '50square[' + str(foo) + ', ' + str(bar) + ']'
    # --- none ---------------------------
    if dic_50square[baz] == '':
        pass
    # --- brown floor --------------------
    elif dic_50square[baz] == 'brown_floor1' or dic_50square[baz] == 'brown_floor3':
        return screen.blit(images_brown_floor[0], coordinates((foo, bar)))
    elif dic_50square[baz] == 'brown_floor2' or dic_50square[baz] == 'brown_floor4':
        return screen.blit(images_brown_floor[1], coordinates((foo, bar)))

def fill_50square1(foo, bar):# 50square1(表層)の変数に格納されてる文字列に対応した絵を blit し続ける
    images_green_chair = split_320x130(green_chair)
    baz = '50square1[' + str(foo) + ', ' + str(bar) + ']'
    # --- none ---------------------------
    if dic_50square1['50square1[' + str(foo) + ', ' + str(bar) + ']'] == '':
        pass
    # --- green chair --------------------
    elif dic_50square1[baz] == 'green_chair1':
        return screen.blit(images_green_chair[0], coordinates((foo, bar)))
    elif dic_50square1[baz] == 'green_chair2':
        return screen.blit(images_green_chair[1], coordinates((foo, bar)))
    elif dic_50square1[baz] == 'green_chair3':
        return screen.blit(images_green_chair[2], coordinates((foo, bar)))
    elif dic_50square1[baz] == 'green_chair4':
        return screen.blit(images_green_chair[3], coordinates((foo, bar)))

# --- Function koko made ----------------------------------------------------------------------------------

clock = pygame.time.Clock()
base_pos = (20,60)
yaji_pos = [1, 1]
frame = 0
roll = 1
menu = 1
while True:
    screen.fill((230,230,230))
    put_base(base_pos)
    frame += 1
    for bar in range(1, 6):
        for foo in range(1, 11):
            fill_50square(foo, bar)
    for bar in range(1, 11):
        for foo in [5, 4, 3, 2, 1]:
            fill_50square1(bar, foo)
    yajirushi_anime(coordinates(yaji_pos), frame)
    for event in pygame.event.get():

        # macに対応。
        event = accept_mouse_click.switch(event, scroll_click=K_a)

        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_F4 and bool(event.mod & KMOD_ALT)):
            sys.exit()
        if not menu % 2: # --- menuが偶数のとき、menuが出てほかは反応しなくなる -------------------
            if event.type == KEYDOWN:
                pass
        if event.type == KEYDOWN:
            # --- yaji_pos を上下左右で切り替える -------------
            if event.key == K_UP:
                if yaji_pos[1] == 5: yaji_pos[1] = 1
                else: yaji_pos[1] += 1
                se_switch2.play()
            elif event.key == K_DOWN:
                if yaji_pos[1] == 1: yaji_pos[1] = 5
                else: yaji_pos[1] -= 1
                se_switch2.play()
            elif event.key == K_LEFT:
                if yaji_pos[0] == 0: yaji_pos[0] = 10
                else: yaji_pos[0] -= 1
                se_switch2.play()
            elif event.key == K_RIGHT:
                if yaji_pos[0] == 10: yaji_pos[0] = 1
                else: yaji_pos[0] += 1
                se_switch2.play()
            # --- Zでアイテムを張る Xでアイテムを剥がす Cでアイテムの向きを変える
            elif event.key == K_z:
                dic_50square['50square' + str(yaji_pos)] = 'brown_floor' + str(roll)
                se_switch.play()
            elif event.key == K_a:
                dic_50square1['50square1' + str(yaji_pos)] = 'green_chair' + str(roll)
                se_switch.play()
            elif event.key == K_x:
                if dic_50square1['50square1' + str(yaji_pos)] != '':
                    dic_50square1['50square1' + str(yaji_pos)] = ''
                else: dic_50square['50square' + str(yaji_pos)] = ''
                se_switch.play()
            elif event.key == K_c:
                if roll == 4: roll = 1
                else: roll += 1
    pygame.display.update()
