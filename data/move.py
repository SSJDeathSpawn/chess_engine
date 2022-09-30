from __future__ import annotations
from typing import TYPE_CHECKING, Callable


if TYPE_CHECKING:
    from data.game import Game
    from data.piece import Piece

from data.consts import MoveTypes
from data.piece import PieceTypes, letter2type

class Move(object):

    def __init__(self, move_type: MoveTypes, /, start: str=None, piece: Piece=None, end: str=None, is_checking: bool=False, is_mating: bool=False, promotion_piece: PieceTypes=None, annex: Callable[[Game, str, str], None]= lambda game, start_pos, end_pos: None):
        self.move_type = move_type
        self.annex = annex
        self.start: str = start
        self.piece: Piece = piece
        self.end: str = end
        self.is_checking = is_checking
        self.is_mating = is_mating
        self.promotion_piece = promotion_piece

    def __str__(self) -> str:
        s = self.move_type.name + " " + self.piece.side.name + " " + letter2type(self.piece.type.letter).name +  " " + self.start + " -> " + self.end + " "
        match self.move_type:
            case MoveTypes.MOVE | MoveTypes.CAPTURE:
                s += "Check:" + ("Yes" if self.is_checking else "No") + " Mate:" + ("Yes" if self.is_mating else "No")
            case MoveTypes.PROMOTION:
                s += "Promote to:" + self.promotion_piece.name
        return s
                

    def __repr__(self) -> str:
        return self.__str__()