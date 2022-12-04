from __future__ import annotations
import sys
import warnings

from loguru import logger

from data import GameInstance
from data.options import Options
from data.screens import MainGameScreen
from engine import Game
from graphics import Surface

if __name__ == "__main__":

    warnings.resetwarnings()
    logging_format: str = "<green>{time:h:m:s A}</green> | <blue>{name}</blue> [<cyan>{level}</cyan>] | <green>{line}</green> - {message}"
    logger.remove()
    logger.add(sink=sys.stdout, colorize=True, format=logging_format, level='DEBUG')
    logger.add(sink='logs/app.log', mode='w', colorize=False, format=logging_format, level='DEBUG')

    logger.debug("Game started")
    simul_game: Game = Game.fromFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    options = Options()
    game = GameInstance(simul_game, options)
    game.screens.push(MainGameScreen(Surface((1920, 1080), [0,0]), game.graphics, game.options))
    game.main_loop()