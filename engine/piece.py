from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from enum import Enum

from itertools import product
from loguru import logger

if TYPE_CHECKING:
    from engine.simul_game import Game

from engine.consts import PieceSide, PieceType
from engine.move_gen import MoveGenerator
from engine.consts import MoveTypes

from misc.utils import mini_chain, is_valid_square



def disable_castling(game: Game, start_pos: str, end_pos: str) -> None:
    """Small function to disable the ability to castle if the rook or king has moved"""
    offset: int = game.board[start_pos].side.value * -2
    if start_pos[0] == 'a':
        game.castling = game.castling[:4+offset] + (False,) + game.castling[5+offset:]
    elif start_pos[0] == 'h':
        game.castling = game.castling[:3+offset] + (False,) + game.castling[4+offset:]
    else:
        s_index = 2 + offset
        game.castling = game.castling[:s_index+1] + (False, False) + game.castling[s_index+2:]

def remove_pawn(game: Game, start_pos: str, end_pos: str):
    """Removal of pawn after performing an en-passant"""
    pawn_pos = end_pos[0] + str(int(end_pos[1]))
    opp_pawn_piece = game.board[pawn_pos] 
    game.materials[opp_pawn_piece.side.other().value].append(opp_pawn_piece)
    game.board[pawn_pos] = Piece.empty()

king = MoveGenerator.complex_move({
    MoveGenerator.vector_move(list(product(range(-1,2), range(-1,2))), 1): lambda game, pos: True,
    MoveGenerator.special_move((2,0), MoveTypes.KING_CASTLE, False, annex=disable_castling): lambda game, pos: (game.board[pos].side == PieceSide.LIGHT and game.castling[0]) or (game.board[pos].side == PieceSide.DARK and game.castling[2]),
    MoveGenerator.special_move((-3,0), MoveTypes.QUEEN_CASTLE, False, annex=disable_castling): lambda game, pos: (game.board[pos].side == PieceSide.LIGHT and game.castling[1]) or (game.board[pos].side == PieceSide.DARK and game.castling[3])
})
queen = MoveGenerator.vector_move(list(product(range(-1,2), range(-1,2))), 8)
# [(1, 0), (-1, 0), (0, 1), (0, -1)]
rook = MoveGenerator.vector_move(mini_chain([[(x, 0), (0, x)] for x in (-1,1)]), 8)
bishop = MoveGenerator.vector_move(mini_chain([[(x, x), (x, -x)] for x in (-1,1)]), 8)
knight = MoveGenerator.jump_move(list(zip((-1,1,2,2,1,-1,-2,-2), (2,2,1,-1,-2,-2,-1,1))), True)

pawn_move_dict = {
    MoveGenerator.jump_move([(0,1)], False): lambda game, pos: game.board[pos].side == PieceSide.LIGHT and int(pos[1]) != 7,
    MoveGenerator.jump_move([(0,-1)], False): lambda game, pos: game.board[pos].side == PieceSide.DARK and int(pos[1]) != 2,
    MoveGenerator.special_move((0,1), MoveTypes.PROMOTION, False) : lambda game, pos: game.board[pos].side == PieceSide.LIGHT and int(pos[1]) == 7,
    MoveGenerator.special_move((0,-1), MoveTypes.PROMOTION, False) : lambda game, pos: game.board[pos].side == PieceSide.DARK and int(pos[1]) == 2,
    MoveGenerator.jump_move([(0,2)], False): lambda game, pos: game.board[pos].side == PieceSide.LIGHT and int(pos[1]) == 2,
    MoveGenerator.jump_move([(0,-2)], False): lambda game, pos: game.board[pos].side == PieceSide.DARK and int(pos[1]) == 7,
}
pawn_move_dict.update({
    MoveGenerator.jump_move([(x,1)], True, True): lambda game, pos: game.board[pos].side == PieceSide.LIGHT for x in (-1,1)
})

pawn_move_dict.update ({
    MoveGenerator.special_move((x,1), MoveTypes.PROMOTION, True, only_capture=True): lambda game, pos: game.board[pos].side == PieceSide.LIGHT and int(pos[1]) == 7 and game.board[chr(ord(pos[0])+x)+str(int(pos[1])+1)].side == PieceSide.DARK for x in (-1,1)
})

pawn_move_dict.update({
    MoveGenerator.jump_move([(x,-1)], True, True): lambda game, pos: game.board[pos].side == PieceSide.DARK for x in (-1,1)
})

pawn_move_dict.update ({
    MoveGenerator.special_move((x,-1), MoveTypes.PROMOTION, True, only_capture=True): lambda game, pos: game.board[pos].side == PieceSide.DARK and int(pos[1]) == 2 and game.board[chr(ord(pos[0])+x)+str(int(pos[1])-1)].side == PieceSide.LIGHT for x in (-1,1)
})

pawn_move_dict.update({
    MoveGenerator.special_move((x,1), MoveTypes.EN_PASSANT, True, annex=remove_pawn): lambda game, pos: game.board[pos].side == PieceSide.LIGHT for x in (-1,1)
})

pawn_move_dict.update({
    MoveGenerator.special_move((x,-1), MoveTypes.EN_PASSANT, True, annex=remove_pawn): lambda game, pos: game.board[pos].side == PieceSide.DARK for x in (-1,1)
})

pawn = MoveGenerator.complex_move(pawn_move_dict)

class PieceTypes(Enum):
    """The different classe of pieces common to both sides"""
    EMPTY = None
    ROOK = PieceType(letter='r', move_gen=rook, image_name='rook')
    KNIGHT = PieceType(letter='n', move_gen=knight, image_name='knight')
    KING = PieceType(letter='k', move_gen=king, image_name='king')
    QUEEN = PieceType(letter='q', move_gen=queen, image_name='queen')
    BISHOP = PieceType(letter='b', move_gen=bishop, image_name='bishop')
    PAWN = PieceType(letter='p', move_gen=pawn, image_name='pawn')


def letter2type(letter: str) -> Optional[PieceTypes]:
    """Returns the type of piece from it's encoding letter in both FEN and PGN"""
    actual = letter.lower()
    for type in PieceTypes:
        if type.value is not None:
            if type.value.letter == actual:
                return type

class Piece:

    def __init__(self, piece_type: PieceTypes, piece_side: PieceSide):
        self.type: PieceType = piece_type.value
        self.side: PieceSide = piece_side

    @staticmethod
    def empty():
        return Piece(PieceTypes.EMPTY, PieceSide.EMPTY)
    
    @staticmethod
    def is_empty(piece: Piece | None):
        return piece == None or (piece.type == PieceTypes.EMPTY and piece.side == PieceSide.EMPTY)
    
    def __eq__(self, other: Piece) -> bool:
        if self.type is None or other.type is None: 
            return (self.type == other.type and self.side == other.side)
        else:
            return (self.type.letter == other.type.letter and self.side == other.side)
    
    def __ne__(self, other: Piece) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        if self.side and self.type:
            return self.side.name + " " + (PieceTypes)(letter2type(self.type.letter)).name
        else:
            return "EMPTY"

    def __repr__(self) -> str:
        return self.__str__()