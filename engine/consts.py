from typing import TYPE_CHECKING
from enum import Enum
from collections import namedtuple

if TYPE_CHECKING:
    pass

PieceType = namedtuple('PieceType', ['letter', 'move_gen', 'image_name'])


class PieceSide(Enum):
    """Which side of the board does the piece belong to"""
    EMPTY = None
    DARK = 0
    LIGHT = 1
    def other(self):
        if self == PieceSide.DARK or self == PieceSide.LIGHT:
            return PieceSide(int(not bool(self.value)))
        return PieceSide.EMPTY

class MoveTypes(Enum):
    """Easy recognition for which type of move the piece is performing"""
    GAME_OVER = -1
    MOVE = 0
    CAPTURE = 1
    EN_PASSANT=2
    KING_CASTLE = 3
    QUEEN_CASTLE = 4
    PROMOTION = 5

class MoveKind(Enum):
    """The different kind of move patterns."""
    VECTOR=1
    JUMP=2
    COMPLEX=3
    SPECIAL=4