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
        lambda s: icons.append(pygame.image.tobytes(s, "RGBA")) or real_set_icon(s),
    )
    repeats = []

    def get():
        repeats.append(pygame.key.get_repeat())
        return [pygame.event.Event(pygame.QUIT)]

    monkeypatch.setattr(pygame.event, "get", get)
    agt.main()
    assert repeats == [(300, 80)]
    chair = pygame.image.load(Path(agt.__file__).parent / "01_img" / "green_chair.png")
    assert icons == [pygame.image.tobytes(chair.subsurface((3, 38, 76, 76)), "RGBA")]


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
    game.handle_key(K_RIGHT)
    game.handle_key(K_a)
    game.sounds = {"switch": SoundSpy(), "switch2": SoundSpy()}
    game.handle_key(pygame.K_l)
    assert (game.floors, game.chairs) == saved
    assert game.sounds["switch"].plays == 1
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
        '{"floors": {" 2,1": "brown_floor1"}, "chairs": {}}',
        '{"floors": {"1_0,5": "brown_floor1"}, "chairs": {}}',
        '{"floors": {"\uff12,\uff11": "brown_floor1"}, "chairs": {}}',
        '{"floors": {"2,1": "brown_floor1", "2,1": "brown_floor2"}, "chairs": {}}',
        pytest.param("[" * 200000, id="deeply-nested"),
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
    screen = pygame.display.set_mode(agt.SCREEN_SIZE)
    expected = agt.Game(agt.load_images(), agt.load_sounds())
    expected.frame = 1
    expected.draw(screen)
    expected.draw_next_item(screen)
    picture = pygame.image.load(shot)
    assert pygame.image.tobytes(picture, "RGB") == pygame.image.tobytes(screen, "RGB")
    pygame.quit()


def test_screenshots_in_the_same_second_do_not_overwrite(screen, monkeypatch, tmp_path):
    monkeypatch.setattr(agt, "SCREENSHOT_FOLDER", tmp_path)
    assert agt.save_screenshot(screen)
    assert agt.save_screenshot(screen)
    assert len(list(tmp_path.glob("screenshot-*.png"))) == 2


def test_screenshot_failure_does_not_crash(screen, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(agt, "SCREENSHOT_FOLDER", tmp_path / "missing")
    agt.save_screenshot(screen)
    assert "Could not save screenshot" in capsys.readouterr().out


def test_save_failure_does_not_crash(game, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(agt, "LAYOUT_FILE", tmp_path / "missing" / "layout.json")
    game.handle_key(pygame.K_s)
    assert "Could not save layout" in capsys.readouterr().out


class SoundSpy:
    def __init__(self):
        self.plays = 0

    def play(self):
        self.plays += 1


def run_main(monkeypatch, frames):
    """frames の 1 要素が 1 フレーム分のイベント。最後に QUIT を足して main を回す。"""
    games = []
    real_game = agt.Game
    monkeypatch.setattr(
        agt, "Game", lambda *a: games.append(real_game(*a)) or games[-1]
    )
    queue = [*frames, [pygame.event.Event(pygame.QUIT)]]
    monkeypatch.setattr(pygame.event, "get", lambda: queue.pop(0))
    agt.main()
    return games[0], queue


def keydown(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)


def test_holding_a_key_repeats_only_arrows(monkeypatch, layout_file):
    saves = []
    monkeypatch.setattr(agt.Game, "save", lambda self: saves.append(1))
    repeat_s = [keydown(pygame.K_s), keydown(pygame.K_s), keydown(pygame.K_s)]
    repeat_right = [keydown(K_RIGHT), keydown(K_RIGHT)]
    repeat_x = [keydown(K_x), keydown(K_x)]
    game, _ = run_main(
        monkeypatch,
        [
            [keydown(K_z), keydown(K_a), *repeat_x],
            [*repeat_s, *repeat_right],
            [
                pygame.event.Event(pygame.KEYUP, key=pygame.K_s, mod=0),
                keydown(pygame.K_s),
            ],
        ],
    )
    assert len(saves) == 2
    assert game.cursor == (3, 1)
    assert game.floors == {(1, 1): "brown_floor1"}


def test_mouse_clicks_are_never_treated_as_held_keys(monkeypatch):
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=4, pos=(0, 0))
    game, _ = run_main(monkeypatch, [[click, click]])
    assert game.cursor == (1, 3)


def test_f4_without_alt_does_not_quit(monkeypatch):
    _, queue = run_main(monkeypatch, [[keydown(pygame.K_F4)], []])
    assert queue == []


def test_next_item_preview_includes_the_floor(game, screen):
    floor = game.brown_floor[0]
    chair = game.green_chair[0]
    point = next(
        (x, y)
        for y in range(30, 130)
        for x in range(80)
        if floor.get_at((x, y)) != floor.get_colorkey()
        and chair.get_at((x, y)) == chair.get_colorkey()
    )
    game.draw_next_item(screen)
    on_screen = (agt.NEXT_ITEM_POS[0] + point[0], agt.NEXT_ITEM_POS[1] + point[1])
    assert screen.get_at(on_screen) == floor.get_at(point)


def test_save_leaves_no_temporary_file(game, layout_file):
    game.handle_key(K_z)
    game.handle_key(pygame.K_s)
    assert [p.name for p in layout_file.parent.iterdir()] == ["layout.json"]


def test_failed_save_keeps_the_previous_layout(game, layout_file, monkeypatch):
    layout_file.write_text('{"floors": {}, "chairs": {}}')

    def broken_dumps(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(agt.Path, "write_text", lambda self, text: broken_dumps())
    game.handle_key(K_z)
    game.handle_key(pygame.K_s)
    assert layout_file.read_text() == '{"floors": {}, "chairs": {}}'


def test_backspace_undoes_board_changes_one_by_one(game, layout_file):
    game.handle_key(K_z)
    game.handle_key(K_a)
    game.handle_key(K_RIGHT)
    game.handle_key(K_z)
    game.handle_key(K_x)  # (2,1) の床を剥がす
    game.handle_key(K_x)  # なにもないので変化なし → undo の対象にしない
    game.handle_key(pygame.K_BACKSPACE)
    assert game.floors == {(1, 1): "brown_floor1", (2, 1): "brown_floor1"}
    game.handle_key(pygame.K_BACKSPACE)
    game.handle_key(pygame.K_BACKSPACE)
    assert (game.floors, game.chairs) == ({(1, 1): "brown_floor1"}, {})
    game.handle_key(pygame.K_BACKSPACE)
    game.handle_key(pygame.K_BACKSPACE)  # もう戻せないときは何もしない
    assert (game.floors, game.chairs) == ({}, {})
    assert game.cursor == (2, 1)


def test_backspace_undoes_load(game, layout_file):
    layout_file.write_text('{"floors": {"5,5": "brown_floor2"}, "chairs": {}}')
    game.handle_key(K_z)
    game.handle_key(pygame.K_l)
    game.handle_key(pygame.K_BACKSPACE)
    assert game.floors == {(1, 1): "brown_floor1"}
