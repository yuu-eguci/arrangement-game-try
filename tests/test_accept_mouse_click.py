import pygame
import pytest
from pygame.locals import (
    K_DOWN,
    K_UP,
    KEYDOWN,
    MOUSEBUTTONDOWN,
    MOUSEMOTION,
    K_a,
    K_c,
    K_x,
    K_z,
)

import accept_mouse_click


@pytest.mark.parametrize(
    ("button", "key"), [(1, K_z), (2, K_c), (3, K_x), (4, K_UP), (5, K_DOWN)]
)
def test_mouse_buttons_become_keydown(button, key):
    event = accept_mouse_click.switch(
        pygame.event.Event(MOUSEBUTTONDOWN, button=button)
    )
    assert (event.type, event.key) == (KEYDOWN, key)


def test_keys_can_be_overridden():
    event = accept_mouse_click.switch(
        pygame.event.Event(MOUSEBUTTONDOWN, button=2), scroll_click=K_a
    )
    assert event.key == K_a


def test_other_events_pass_through():
    original = pygame.event.Event(MOUSEMOTION, pos=(1, 2))
    assert accept_mouse_click.switch(original) is original


def test_unknown_button_passes_through_with_notice(capsys):
    original = pygame.event.Event(MOUSEBUTTONDOWN, button=6)
    assert accept_mouse_click.switch(original) is original
    assert "Unknown mouse click:6" in capsys.readouterr().out


def test_converted_event_has_keydown_attributes():
    event = accept_mouse_click.switch(pygame.event.Event(MOUSEBUTTONDOWN, button=1))
    assert (event.mod, event.unicode) == (0, "")
