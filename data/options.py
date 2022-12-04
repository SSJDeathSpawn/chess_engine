from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from data.constants import STARTING_RESOLUTION

class Options(object):

    def __init__(self, **kwargs) -> None:
        self.resolution: tuple[int, int] = kwargs.get("resolution", STARTING_RESOLUTION)
        self.fullscreen: bool = kwargs.get("fullscreen", True)
