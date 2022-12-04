from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Type

import pygame
from loguru import logger

if TYPE_CHECKING:
    from data.game import GameInstance

from misc.utils import generate_id
from graphics.stack import ScreenStack
from graphics.constants import DEFAULT_REGULAR_FONT, DEFAULT_ITALIC_FONT, DEFAULT_BOLD_FONT, DEFAULT_BOLDITALIC_FONT
from data.constants import BLACK


class Surface(pygame.surface.Surface):
    """Adds ID and pos attributes to the pygame Surface class"""

    def __init__(self, size: tuple[int, int], pos: list[int]) -> None:
        
        super().__init__(size, pygame.SRCALPHA)

        self.ID: str = f'SURFACE-{generate_id()}'
        self.pos: list[int] = pos

    def copy(self) -> Surface:
        """Returns a copy of the surface"""
        
        new = Surface(self.get_size(), self.pos)
        new.ID = self.ID
        new.blit(self, (0, 0))

        return new

class PygameAbstraction(object):
    """Acts as an easy-to-use anchor between my code and pygame's code"""

    def __init__(self, width: int, height: int, caption: str, fullscreen: bool = True):
        pygame.init()

        self.width: int = width
        self.height: int = height
        self.caption: str = caption
        self.image_path = 'assets/sprites/'
        self.fonts: dict[str, str] = {
            'regular': DEFAULT_REGULAR_FONT,
            'italic': DEFAULT_ITALIC_FONT,
            'bold': DEFAULT_BOLD_FONT,
            'bolditalic': DEFAULT_BOLDITALIC_FONT,
        }

        self.window: pygame.surface.Surface = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN if fullscreen else 0)

        pygame.display.set_caption(self.caption)
    
    # Main

    def render_everything(self, game_inst: GameInstance, screen_stack: ScreenStack) -> None:
        """Called on every iteration of the Game Loop"""

        self.window.fill(BLACK)

        for screen in screen_stack:
            screen.clear()
            screen.render(game_inst)
            self.window.blit(screen.surface, screen.surface.pos)

        pygame.display.update()

    # Shapes

    def draw_line(self, color: tuple[int, int, int, int], start: tuple[int, int], end: tuple[int, int], width: int = 1, surface: Optional[pygame.surface.Surface] = None) -> pygame.rect.Rect:
        """Draws a line of given width (default 1) on a surface (default main window surface)"""

        if surface is None:
            surface = self.window

        return pygame.draw.line(surface, color, start, end, width)

    def draw_lines(self, color: tuple[int, int, int, int], points: list[tuple[int, int]], width: int = 1, closed: bool = False, surface: Optional[pygame.surface.Surface] = None) -> pygame.rect.Rect:
        """Draws multiple lines on the screen with given width (default 1) connecting all the points in the given sequence on a surface (default main window surface)"""

        if not surface:
            surface = self.window

        return pygame.draw.lines(surface, color, closed, points, width)

    def draw_circle(self, color: tuple[int, int, int, int], center: tuple[int, int], radius: int, quadrants: int = 0b1111, width: int = 0, surface: Optional[pygame.surface.Surface] = None) -> pygame.rect.Rect:
        """Draws the specified quadrants of the circle (default 0b1111) on a surface (default main window surface)"""

        if not surface:
            surface = self.window

        new_quadrants = [bool(quadrants & 0b1000), bool(quadrants & 0b100), bool(quadrants & 0b10), bool(quadrants & 0b1)]

        return pygame.draw.circle(surface, color, center, radius, width, *new_quadrants)

    def draw_rect(self, color: tuple[int, int, int, int], rect_x: int, rect_y: int, rect_width: int, rect_height: int, width: int = 0, surface: Optional[pygame.surface.Surface] = None) -> pygame.rect.Rect:
        """Draws a rectangle with given dimensions on a surface (default main window surface)"""

        if not surface:
            surface = self.window

        return pygame.draw.rect(surface, color, pygame.Rect(rect_x, rect_y, rect_width, rect_height), width)

    def draw_polygon(self, color: tuple[int, int, int, int], points: list[tuple[int, int]], width: int = 0, surface: Optional[pygame.surface.Surface] = None) -> pygame.rect.Rect:
        """Draws a polygon using the given points on a surface (defualt main window surface)"""

        if not surface:
            surface = self.window

        return pygame.draw.polygon(surface, color, points, width)

    # Images

    def convert_to_pygame_image(self, name: str) -> Optional[pygame.surface.Surface]:
        """Loads and returns a pygame image with given name"""

        try:
            image = pygame.image.load(f'{self.image_path}{name}')
        except FileNotFoundError:
            logger.error(f'Invalid image file path {self.image_path}{name}. Ignoring load request')
            return

        return image

    def blit_image(self, pos: tuple[int, int], image_name: str, width: int = 0, height: int = 0, surface: Optional[pygame.surface.Surface] = None) -> Optional[pygame.rect.Rect]:  # type: ignore
        """Blits an image to a surface (default main window surface)"""

        if not surface:
            surface: pygame.surface.Surface = self.window

        image = self.convert_to_pygame_image(image_name)

        if not image:
            logger.error('No image file found. Ignoring blit request')
            return

        image_size = (
            width if width > 0 else int(image.get_width()),
            height if height > 0 else int(image.get_height())
        )

        image = pygame.transform.scale(image, image_size)

        return surface.blit(image, pos)

    def render_text(self, font_type: str, size: int, text: str, color: tuple[int, int, int, int], pos: tuple[int, int], background: Optional[tuple[int, int, int, int]] = None, surface: Optional[pygame.surface.Surface] = None) -> Optional[pygame.rect.Rect]:
        """Renders text on a surface (default main window surface)"""

        if not surface:
            surface = self.window

        try:
            font = pygame.font.Font(self.fonts[font_type], size)
        except KeyError:
            logger.error(f'Invalid font type {font_type}. Ignoring render request')
            return

        text_surf = font.render(text, True, color, background)

        return surface.blit(text_surf, pos)