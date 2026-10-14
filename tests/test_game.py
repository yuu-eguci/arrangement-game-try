from pathlib import Path

import pygame
import pytest
from pygame.locals import K_DOWN, K_LEFT, K_RIGHT, K_UP, K_a, K_c, K_x, K_z

import ArrangementGameTry as agt

GOLDEN = Path(__file__).parent / "golden" / "original.png"


@pytest.mark.parametrize(
    ("pos", "key", "expected"),
    [
        ((1, 1), K_RIGHT, (2, 1)),
        ((10, 1), K_RIGHT, (1, 1)),
        ((2, 1), K_LEFT, (1, 1)),
        ((1, 3), K_LEFT, (10, 3)),
        ((1, 1), K_UP, (1, 2)),
        ((1, 5), K_UP, (1, 1)),
        ((1, 2), K_DOWN, (1, 1)),
        ((4, 1), K_DOWN, (4, 5)),
    ],
)
def test_move_cursor_wraps_inside_the_10x5_floor(pos, key, expected):
    assert agt.move_cursor(pos, key) == expected


def test_next_roll_cycles_1_to_4():
    assert [agt.next_roll(r) for r in (1, 2, 3, 4)] == [2, 3, 4, 1]


def test_z_puts_floor_and_a_puts_chair_with_current_roll(game):
    game.handle_key(K_c)
    game.handle_key(K_z)
    game.handle_key(K_a)
    assert game.floors == {(1, 1): "brown_floor2"}
    assert game.chairs == {(1, 1): "green_chair2"}


def test_x_removes_chair_first_then_floor(game):
    game.handle_key(K_z)
    game.handle_key(K_a)
    game.handle_key(K_x)
    assert game.chairs == {}
    assert game.floors == {(1, 1): "brown_floor1"}
    game.handle_key(K_x)
    assert game.floors == {}


def test_left_from_first_column_wraps_and_x_does_not_crash(game):
    # 2019 版はここで矢印が 0 列目に行き、X で KeyError になって落ちていた
    game.handle_key(K_LEFT)
    assert game.cursor == (10, 1)
    game.handle_key(K_z)
    game.handle_key(K_x)
    game.handle_key(K_x)
    assert game.floors == {}


def test_draw_matches_what_the_2019_original_drew(game, screen):
    """tests/golden/original.png は commit e815bd4 の ArrangementGameTry.py を
    dummy ドライバで動かし、1 フレームに 1 キーずつ下の順で押して
    45 フレーム目を保存したもの。
    """
    keys = (
        "z right c z right c z right c z c up a right c a right c a right c a c "
        "up up z a left a x down a down c a down a"
    )
    for name in keys.split():
        game.handle_key(pygame.key.key_code(name))
    game.frame = 45
    game.draw(screen)
    golden = pygame.image.load(GOLDEN).convert()
    assert screen.get_size() == golden.get_size()
    assert pygame.image.tobytes(screen, "RGB") == pygame.image.tobytes(golden, "RGB")


def test_assets_load_even_from_another_directory(screen, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert set(agt.load_images()) >= {
        "base0",
        "yajirushi",
        "brown_floor",
        "green_chair",
    }
    assert set(agt.load_sounds()) == {"switch", "switch2"}


@pytest.mark.parametrize(
    "event",
    [
        pygame.event.Event(pygame.QUIT),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F4, mod=pygame.KMOD_LALT),
    ],
)
def test_main_returns_on_quit_or_alt_f4(monkeypatch, event):
    monkeypatch.setattr(pygame.event, "get", lambda: [event])
    agt.main()
    assert not pygame.get_init()
