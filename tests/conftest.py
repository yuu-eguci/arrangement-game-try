import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402
import pytest  # noqa: E402

import ArrangementGameTry as agt  # noqa: E402


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode(agt.SCREEN_SIZE)
    yield surface
    pygame.quit()


@pytest.fixture
def game(screen):
    return agt.Game(agt.load_images(), agt.load_sounds())
