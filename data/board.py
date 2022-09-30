from __future__ import annotations
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from logging import Logger

from data.exceptions import InvalidSquareException
from data.piece import Piece
from misc.utils import is_valid_square

from logging_module.custom_logging import get_logger

class Board(object):

    def __init__(self, pieces: list[Piece]):
        self.logger: Logger = get_logger(__name__)
        self.pieces: Piece = pieces

    def __getitem__(self, key) -> Piece:
        if not is_valid_square(key):
            raise InvalidSquareException(f"{key} is not a valid square!")
        index = (ord(key[0]) - ord('a')) + (int(key[1])-1) * 8
        return self.pieces[index]

    def __setitem__(self, key, obj) -> None:
        if not is_valid_square(key):
            raise InvalidSquareException()
        if type(obj) != Piece:
            raise ValueError("Not a Piece object")
        index = (ord(key[0]) - ord('a')) + (int(key[1]) - 1) * 8
        self.pieces[index] = obj

    @staticmethod
    def empty() -> Board:
        return Board([Piece.empty()]*64)