from __future__ import annotations
from typing import TYPE_CHECKING

from loguru import logger
import pygame

if TYPE_CHECKING:
    from graphics.graphics import PygameAbstraction
    from data.game import GameInstance
    from data.options import Options

from graphics.screen import Screen
from data.components.main_game_comps import BoardComponent, TerminalComponent
from data.constants import BLACK
from graphics.constants import CODE_FORMATTING
from misc.lib import Rectangle

class MainGameScreen(Screen):
    
    def __init__(self, surface: pygame.surface.Surface, pygame_access: PygameAbstraction, options: Options) -> None:
        super().__init__(surface,pygame_access, options)
        self.options = options
        # Generate Board Component with the specification of 0.05 of resolution as starting x, 0.1 as starting y, 0.4 as ending x and to make it square
        self.board_comp = BoardComponent(self.generate_rectangle(0.05, 0.1, 0.4, 0))
        self.terminal_comp = TerminalComponent(self.generate_rectangle(0.45, 0.15, 0.73, 0.65))
        self.components = [self.board_comp, self.terminal_comp]
    
    def generate_rectangle(self, start_x:float, start_y:float, amt:float, amt_new:float) -> Rectangle:
        return Rectangle(*[
                tuple(map(int, x)) for x in [
                    (start_x*self.options.resolution[0], start_y*self.options.resolution[1]), 
                    (amt*self.options.resolution[0], 
                        ((amt - start_x)*self.options.resolution[0] + start_y*self.options.resolution[1] if amt_new ==0 else amt_new*self.options.resolution[1])
                    )
                ]
            ])

    def clear(self):
        self.surface.fill(BLACK)
        for comp in self.components:
            comp.clear()

    def handle_events(self, events: list[pygame.event.Event], game_inst: GameInstance):
        for event in events:
            if event.type == pygame.TEXTINPUT:
                self.terminal_comp.command += event.text
                self.terminal_comp.command_text.update_text(self.terminal_comp.command)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SLASH:
                    logger.debug(game_inst.simul_game.side)
                if event.key == pygame.K_RETURN:
                    temp = game_inst.play_move(self.terminal_comp.command)
                    logger.debug(temp)
                    if not temp:
                        self.terminal_comp.raw_text += "Invalid move\n"
                    else:
                        self.terminal_comp.raw_text += f"{CODE_FORMATTING['GREEN']}{self.terminal_comp.command}{CODE_FORMATTING['COLOR_RESET']}\n"
                    self.terminal_comp.command = ''
                    self.terminal_comp.text.update_text(self.terminal_comp.raw_text)
                    self.terminal_comp.command_text.update_text(self.terminal_comp.command)
                if event.key == pygame.K_BACKSPACE:
                    self.terminal_comp.command = self.terminal_comp.command[:-1]
                    self.terminal_comp.command_text.update_text(self.terminal_comp.command)


    def render(self, game_inst: GameInstance):
        for comp in self.components:
            comp.render(self, game_inst)
            self.surface.blit(comp.surface, comp.pos)