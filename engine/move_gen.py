from __future__ import annotations
from typing import TYPE_CHECKING, Callable
from itertools import product

if TYPE_CHECKING:
    from engine.simul_game import Game

from engine.consts import MoveKind, MoveTypes, PieceSide
from misc.utils import mini_chain


# def move_generator(func):
    # def wrap(pos, *args, **kwargs):
        # if not is_valid_square(pos):
            # raise InvalidSquareException()
        # func(pos, *args, **kwargs)
    # return wrap

# def vertical(pos: str):
    # return [pos[0] + str(i) for i in range(1,8)]

# def horizontal(pos: str):
    # return [chr(i) + pos[1] for i in range(ord('a'), ord('i'))]

# def diagonal(pos: str):
    # return list(filter(is_valid_square, [chr(ord(pos[0]) + i) + str(pos[1] + i) for i in range(-8,9)] + [chr(ord(pos[0]) - i) + str(pos[1] + i) for i in range(-8,9)]))

# def adjacent(pos: str):
    # l = zip(range(-1,2), range(-1, 2))
    # return list(filter(is_valid_square, [chr(ord(pos[0])+x) + str(int(pos[1])+y) for x,y in l]))

# def l_shape(pos: str):
    # l = zip((-1,1,2,2,1,-1,-2,-2), (2,2,1,-1,-2,-2,-1,1))
    # return list(filter(is_valid_square, [chr(ord(pos[0]+x)) + str(int(pos[1])+y) for x,y in l]))

# @move_generator
# def rook(pos: str):
    # return vertical(pos) + horizontal(pos)

# @move_generator
# def bishop(pos: str):
    # return diagonal(pos)

# @move_generator
# def queen(pos: str):
    # return vertical(pos) + horizontal(pos) + diagonal(pos)

# @move_generator
# def king(pos:str):
    # return adjacent(pos)

# @move_generator
# def knight(pos: str):
    # return l_shape(pos)

# @move_generator
# def pawn(pos:str, side: PieceSide, lower_occ: bool, upper_occ: bool):
    # l = [chr(ord(pos[0]) + i)+ str(int(pos[1]) - 1 + 2 * side.value) for i in {0, -1 * lower_occ, 1 * upper_occ}]
    # if (int(pos[1]),side) in ((2, PieceSide.LIGHT), (7, PieceSide.DARK)):
        # l.append(pos[0] + str(int(pos[1]) - 2 + 4 * side.value))
    # return l

class MoveGenerator(object):

    def __init__(self) -> None:
        self.move_kind: MoveKind
        self.vectors: list[tuple[int, int]]
        self.limit: int
        self.offsets: list[tuple[int, int]]
        self.can_capture: bool
        self.only_capture: bool
        self.moves_conds: dict[MoveGenerator, Callable[[Game, str], bool]]
        self.offset: tuple[int, int]
        self.move_type: MoveTypes
        self.extra_info: dict
        self.annex: Callable[[Game, str, str], None]

    @staticmethod
    def vector_move(vectors: list[tuple[int, int]], limit: int) -> MoveGenerator:
        """To handle vector type move generators"""
        self = MoveGenerator()
        self.move_kind = MoveKind.VECTOR
        self.vectors = vectors
        self.limit = limit
        return self

    @staticmethod
    def jump_move(offsets: list[tuple[int, int]], can_capture: bool, only_capture: bool=False) -> MoveGenerator:
        """To handle jump type move generators"""
        self = MoveGenerator()
        self.move_kind = MoveKind.JUMP
        self.offsets = offsets
        self.can_capture = can_capture
        self.only_capture = only_capture
        return self

    @staticmethod
    def complex_move(moves_conds: dict[MoveGenerator, Callable[[Game, str], bool]]) -> MoveGenerator:
        """To handle complex type move generators"""
        self = MoveGenerator()
        self.move_kind = MoveKind.COMPLEX
        self.moves_conds = moves_conds
        return self

    @staticmethod
    def special_move(offset: tuple[int, int], move_type: MoveTypes, can_capture: bool, only_capture: bool=False, extra_info: dict = {}, annex: Callable[[Game, str, str], None]=lambda game, start_pos, end_pos: None) -> MoveGenerator:
        """To handle special type move generators"""
        self = MoveGenerator()
        self.move_kind = MoveKind.SPECIAL
        self.offset = offset
        self.move_type = move_type
        self.can_capture = can_capture
        self.only_capture = only_capture
        self.extra_info = extra_info
        self.annex = annex
        return self

    def __str__(self) -> str:
        s = self.move_kind.name + " "
        match self.move_kind:
            case MoveKind.VECTOR:
                s += str(self.vectors) + " of " + str(self.limit)
            case MoveKind.JUMP:
                s += str(self.offsets) + " can" + ("" if self.can_capture else "not") + " capture"  
            case MoveKind.COMPLEX:
                s += str(self.moves_conds)
            case MoveKind.SPECIAL:
                s += self.move_type.name + " " + str(self.offset) + " can" + ("" if self.can_capture else "not") + " capture"
        return s

    def __repr__(self) -> str:
        return self.__str__()