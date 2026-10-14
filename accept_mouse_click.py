#!/usr/bin/env python

"""accept_mouse_click

pygame作品がwindowsでしかキーボード入力を正しく受け取ってくれない。
そんなpygameをmacでも辛くも動かすため
マウスクリックをキー入力に化けさせる応急処置モジュール。

使用例:
    import accept_mouse_click
    ...
    for event in pygame.event.get():
        event = accept_mouse_click.switch(
            event,
            left_click=K_z,
            scroll_click=K_a
            )

ただし使用条件:
    eventのダミーを返しているので、
    typeとkey以外のパラメータ(mod, unicode は空っぽ)は使えません。

========================================
バージョン1.0(2017-09-22)
    完成。
"""

import pygame.locals as pgl


def switch(
    event,
    left_click=pgl.K_z,
    scroll_click=pgl.K_c,
    right_click=pgl.K_x,
    scroll_up=pgl.K_UP,
    scroll_down=pgl.K_DOWN,
):
    """マウスクリックをキー入力に変換します。
    デフォルトでは
        左クリック:Z
        スクロールクリック:C
        右クリック:X
        上スクロール:UP
        下スクロール:DOWN
    かえたいとこだけ指定してください。
    """

    change_table = {
        1: left_click,
        2: scroll_click,
        3: right_click,
        4: scroll_up,
        5: scroll_down,
    }

    if event.type != pgl.MOUSEBUTTONDOWN:
        return event

    if event.button not in change_table:
        print("<accept_mouse_click NOTICE> Unknown mouse click:" + str(event.button))
        return event

    return DummyEvent(pgl.KEYDOWN, change_table[event.button])


class DummyEvent:
    """eventのダミー。
    オリジナルのeventがreadonlyだったため、ダミーを作ります。
    ようはtypeの中にMOUSEBUTTONDOWN、keyの中にK_*が入ってりゃいいんだからさ!
    (mod とかを見るコードでも落ちないように、そのへんは空っぽで持っておく)
    """

    mod = 0
    unicode = ""

    def __init__(self, type_, key):
        self.type = type_
        self.key = key
