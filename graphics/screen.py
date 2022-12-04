from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from graphics.graphics import PygameAbstraction
    from graphics.graphics import Surface
    from data.game import GameInstance
    import pygame

from data.constants import BLACK
from data.options import Options

class Screen(ABC):
    
    def __init__(self, surface: pygame.surface.Surface, pygame_access: PygameAbstraction, options: Options) -> None:
        self.pygame_access = pygame_access
        self.surface = surface

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event], game_inst: GameInstance) -> None:
        pass
    
    @abstractmethod
    def render(self, game_inst: GameInstance) -> None:
        pass
