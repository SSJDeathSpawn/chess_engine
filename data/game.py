from __future__ import annotations
from typing import TYPE_CHECKING

import pygame
from loguru import logger

from graphics.stack import ScreenStack
from graphics.graphics import PygameAbstraction
from data.options import Options
from engine.exceptions import InvalidPGNStringException
from engine.move import Move

if TYPE_CHECKING:
    from engine.simul_game import Game

class GameInstance(object):
    
    def __init__(self, simul_game:Game, options: Options):

        self.simul_game = simul_game
        self.options = options
        self.graphics: PygameAbstraction = PygameAbstraction(*self.options.resolution, "Chess", fullscreen=options.fullscreen)
        self.screens: ScreenStack = ScreenStack()
        self.running = True

    def events_handler(self):
        for event in self.events:
            
            if event.type == pygame.QUIT:
                self.running = False
                break

    def play_move(self, PGN: str) -> bool:
        try:
            move = self.simul_game.PGN2Move(PGN)
            assert isinstance(move, Move)
            logger.debug(move)
            self.simul_game.perfom_move(move)
            return True
        except InvalidPGNStringException as e:
            logger.warning("Invalid PGN Exception")
            return False

    def main_loop(self):

        while self.running:
            self.events = []
            events = pygame.event.get()
            for event in events:
                if event not in self.events:
                    self.events.append(event)
            
            self.events_handler()
            self.screens.get_top().handle_events(self.events, self)

            self.graphics.render_everything(self, self.screens)
