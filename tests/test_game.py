import json
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


def test_game_runs_silently_without_audio_device(screen):
    pygame.mixer.quit()  # サウンドデバイスがなくて mixer が立ち上がらなかったとき
    game = agt.Game(agt.load_images(), agt.load_sounds())
    game.handle_key(K_z)
    game.handle_key(K_RIGHT)
    assert game.floors == {(1, 1): "brown_floor1"}


def test_floor_pixels_do_not_depend_on_placement_order(screen):
    images = agt.load_images()
    pictures = []
    for order in ([(2, 1), (1, 1), (1, 2)], [(1, 2), (1, 1), (2, 1)]):
        game = agt.Game(images, agt.load_sounds())
        for pos in order:
            game.floors[pos] = "brown_floor2"
        game.draw(screen)
        pictures.append(pygame.image.tobytes(screen, "RGB"))
    assert pictures[0] == pictures[1]


def test_middle_click_puts_chair_through_main_loop(monkeypatch):
    games = []
    real_game = agt.Game
    monkeypatch.setattr(
        agt, "Game", lambda *a: games.append(real_game(*a)) or games[-1]
    )
    events = [
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, pos=(0, 0)),
        pygame.event.Event(pygame.QUIT),
    ]
    monkeypatch.setattr(pygame.event, "get", lambda: events)
    agt.main()
    assert games[0].chairs == {(1, 1): "green_chair1"}


def test_next_item_preview_follows_c_and_leaves_the_grid_alone(game, screen):
    def preview_and_rest():
        game.draw(screen)
        before = pygame.image.tobytes(screen, "RGB")
        game.draw_next_item(screen)
        after = pygame.image.tobytes(screen, "RGB")
        corner = pygame.image.tobytes(screen.subsurface(agt.NEXT_ITEM_RECT), "RGB")
        screen.fill((0, 0, 0), agt.NEXT_ITEM_RECT)
        rest = pygame.image.tobytes(screen, "RGB")
        game.draw(screen)
        screen.fill((0, 0, 0), agt.NEXT_ITEM_RECT)
        return before != after, corner, rest == pygame.image.tobytes(screen, "RGB")

    previews = []
    for _ in range(5):
        changed, corner, grid_untouched = preview_and_rest()
        assert changed
        assert grid_untouched
        previews.append(corner)
        game.handle_key(K_c)
    assert len(set(previews[:4])) == 4
    assert previews[4] == previews[0]


def test_main_sets_key_repeat_and_chair_icon(monkeypatch):
    icons = []
    real_set_icon = pygame.display.set_icon
    monkeypatch.setattr(
        pygame.display,
        "set_icon",
        lambda s: icons.append(s.get_size()) or real_set_icon(s),
    )
    repeats = []

    def get():
        repeats.append(pygame.key.get_repeat())
        return [pygame.event.Event(pygame.QUIT)]

    monkeypatch.setattr(pygame.event, "get", get)
    agt.main()
    assert repeats == [(300, 80)]
    assert icons == [(76, 76)]


@pytest.fixture
def layout_file(tmp_path, monkeypatch):
    path = tmp_path / "layout.json"
    monkeypatch.setattr(agt, "LAYOUT_FILE", path)
    return path


def test_s_saves_and_l_loads_the_layout(game, layout_file):
    game.handle_key(K_z)
    game.handle_key(K_c)
    game.handle_key(K_a)
    game.handle_key(pygame.K_s)
    saved = (dict(game.floors), dict(game.chairs))
    game.handle_key(K_x)
    game.handle_key(K_x)
    game.handle_key(pygame.K_l)
    assert (game.floors, game.chairs) == saved
    assert json.loads(layout_file.read_text()) == {
        "floors": {"1,1": "brown_floor1"},
        "chairs": {"1,1": "green_chair2"},
    }


@pytest.mark.parametrize(
    "content",
    [
        None,
        "not json",
        "[]",
        '{"floors": {"0,1": "brown_floor1"}, "chairs": {}}',
        '{"floors": {"1,1": "green_chair1"}, "chairs": {}}',
        '{"floors": {}, "chairs": {"1,1": "green_chair5"}}',
        '{"floors": {"a,b": "brown_floor1"}, "chairs": {}}',
    ],
)
def test_l_ignores_missing_or_broken_layout(game, screen, layout_file, content):
    if content is not None:
        layout_file.write_text(content)
    game.handle_key(K_z)
    game.handle_key(pygame.K_l)
    assert game.floors == {(1, 1): "brown_floor1"}
    game.draw(screen)


def test_p_saves_a_screenshot(monkeypatch, tmp_path):
    monkeypatch.setattr(agt, "SCREENSHOT_FOLDER", tmp_path)
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z, mod=0),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, mod=0),
        pygame.event.Event(pygame.QUIT),
    ]
    monkeypatch.setattr(pygame.event, "get", lambda: events)
    agt.main()
    (shot,) = tmp_path.glob("screenshot-*.png")
    pygame.init()
    assert pygame.image.load(shot).get_size() == agt.SCREEN_SIZE


def test_screenshot_failure_does_not_crash(screen, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(agt, "SCREENSHOT_FOLDER", tmp_path / "missing")
    agt.save_screenshot(screen)
    assert "Could not save screenshot" in capsys.readouterr().out


def test_save_failure_does_not_crash(game, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(agt, "LAYOUT_FILE", tmp_path / "missing" / "layout.json")
    game.handle_key(pygame.K_s)
    assert "Could not save layout" in capsys.readouterr().out
