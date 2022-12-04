from __future__ import annotations
from typing import TYPE_CHECKING

from loguru import logger
from itertools import chain
import pygame

if TYPE_CHECKING:
    from graphics.screen import Screen
    from data.game import GameInstance
    from graphics.graphics import PygameAbstraction

from engine.piece import PieceSide
from graphics.graphics import Surface
from data.constants import BLACK
from graphics.constants import IBM_FNT_PT_FACTOR
from misc.lib import Rectangle
from graphics.text import Text
from graphics.component import Component

class BoardComponent(Component):

    def __init__(self, box: Rectangle) -> None:
        super().__init__(box)
        self.points = self.generate_points_inside()
        self.boxes = self.generate_boxes()

    def generate_points_inside(self) -> list[list[tuple[int, int]]]:
        amt: int = int(self.size[0]/8)
        points: list[list[tuple[int, int]]] = [[(amt*x, amt*y) for x in range(9)] for y in range(9)]
        return points

    def generate_boxes(self) -> list[list[Rectangle]]:
        boxes: list[list[Rectangle]] = []
        for m in range(8):
            boxes_1: list[Rectangle] = []
            for n in range(8):
                boxes_1.append(Rectangle(self.points[n][m],self.points[n+1][m+1]))
            boxes.append(boxes_1)
        return boxes

    def clear(self) -> None:
        self.surface.fill(BLACK)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        pass

    def render(self, screen: Screen, game_inst: GameInstance) -> None:
        screen.pygame_access.draw_lines((255,255,255,255), [(0,0), (self.size[0], 0), self.size, (0, self.size[1])], width=10, closed=True, surface=self.surface)
        for point in self.points:
            screen.pygame_access.draw_line((255,255,255,255), point[0], point[1],width=10, surface=self.surface)
        for n, line in enumerate(self.boxes):
            for m, box in enumerate(line):
                if (n+m)%2==0:
                    screen.pygame_access.draw_rect(
                        (255,255,255,255), 
                        self.boxes[n][m].x, 
                        self.boxes[n][m].y, 
                        self.boxes[n][m].width,
                        self.boxes[n][m].height,
                        surface=self.surface
                    )
        for index, piece in enumerate(game_inst.simul_game.board.pieces):
            if piece.type:
                self.fit_in_centre(screen.pygame_access, piece.type.image_name + ('_b' if piece.side == PieceSide.DARK else '_w') + '.png', self.boxes[index%8][7-index//8], 0.8)

    def fit_in_centre(self, pygame_access: PygameAbstraction, image_name: str, box: Rectangle, scale:float):
        width_new = int(box.width*scale)
        height_new = int(box.height*scale)
        point_new = tuple(map(int, (box.point_lt[0]+box.width*(1-scale)/2, box.point_lt[1]+box.height*(1-scale)/2)))
        pygame_access.blit_image(point_new, image_name, width=width_new, height=height_new, surface=self.surface)


class TerminalComponent(Component):

    def __init__(self, box: Rectangle) -> None:
        super().__init__(box)
        self.scroll = 0
        self.raw_text = ''
        self.command = ''
        self.font_size = 20
        self.text = Text(self.raw_text, (255,255,255), 'regular', self.font_size, (3,3), box.width, box.height, (3,3))
        self.max_lines: int = int(box.height//self.font_size*IBM_FNT_PT_FACTOR[1])-1
        self.command_text = Text(self.raw_text, (255,255,255), 'regular', self.font_size, (3,self.size[1]-int(self.font_size*IBM_FNT_PT_FACTOR[1])-5), box.width, box.height, (3,0))
        self.scroll_area = Surface((box.width, box.height-int(self.font_size*IBM_FNT_PT_FACTOR[1])-5), [0,0])

    def clear(self) -> None:
        self.surface.fill(BLACK)
        self.scroll_area.fill(BLACK)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.TEXTINPUT:
                self.command += event.text
                self.command_text.update_text(self.command)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.raw_text += self.command + '\n'
                    self.command = ''
                    self.text.update_text(self.raw_text)
                    self.command_text.update_text(self.command)
                if event.key == pygame.K_BACKSPACE:
                    self.command = self.command[:-1]
                    self.command_text.update_text(self.command)

    def render(self, screen: Screen, game_inst: GameInstance) -> None:
        if self.scroll > max(0, len(self.raw_text.split('\n'))-self.max_lines):
            self.scroll = len(self.raw_text.split('\n')) - self.max_lines
        for section in self.text.processed:
            screen.pygame_access.render_text(section.style, self.text.font_size, section.text, (*section.color,255), section.pos, surface=self.scroll_area)

        for section in self.command_text.processed:
            screen.pygame_access.render_text(section.style, self.text.font_size, section.text, (*section.color,255), section.pos, surface=self.surface)

        self.surface.blit(self.scroll_area, self.scroll_area.pos)
        screen.pygame_access.draw_rect((255,255,255,255), 0, 0, self.size[0], self.size[1], width=3, surface=self.surface)
        screen.pygame_access.draw_line((255,255,255,255),(0,self.size[1]-int(self.font_size*IBM_FNT_PT_FACTOR[1])-5), (self.size[0], self.size[1]-int(self.font_size*IBM_FNT_PT_FACTOR[1])-5), width=3, surface=self.surface)
