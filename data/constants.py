from __future__ import annotations
from typing import TYPE_CHECKING
from pygame.surface import Surface

if TYPE_CHECKING:
    pass

BLACK: tuple[int, int, int, int] = (0,0,0,255)
STARTING_RESOLUTION = (1920, 1080)
empty_surface = Surface((1,1))