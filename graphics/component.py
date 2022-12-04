from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from data.game import GameInstance
    from graphics.screen import Screen
    from misc.lib import Rectangle
    import pygame

from data.constants import BLACK
from graphics.graphics import Surface

class Component(ABC):
    
    def __init__(self, box: Rectangle) -> None:
        self.box = box
        self.size = (self.box.width, self.box.height)
        self.pos = list(self.box.point_lt)
        self.surface = Surface(self.size, self.pos)

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event], game_inst: GameInstance) -> None:
        pass
    
    @abstractmethod
    def render(self, screen: Screen, game_inst: GameInstance) -> None:
        pass
