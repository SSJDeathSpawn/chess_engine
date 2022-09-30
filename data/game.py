from __future__ import annotations
from functools import partial
from logging import captureWarnings
from shutil import move
from typing import TYPE_CHECKING, Generator
from itertools import compress
import re
from copy import deepcopy

if TYPE_CHECKING:
    from logging import Logger

from data.consts import MoveKind, MoveTypes, PieceSide
from data.board import Board
from data.piece import Piece, letter2type, PieceTypes
from data.move import Move
from data.exceptions import InvalidFENStringException, InvalidFANStringException
from data.move_gen import MoveGenerator

from misc.utils import board_iterator, is_valid_square, sign
from logging_module.custom_logging import get_logger

class Game(object):

    def __init__(self, board: Board, side: PieceSide, castling: tuple[bool, bool, bool, bool], en_passant: str | None, half_moves: int, num_moves: int, moves: list[Move]):
       self.logger: Logger = get_logger(__name__)
       self.board: Board = board
       self.side: PieceSide = side
       self.castling: tuple[bool, bool, bool, bool] = castling
       self.en_passant: str | None = en_passant
       self.half_moves: int = half_moves
       self.num_moves: int = num_moves
       self.moves = moves
       self.materials: list[list[Piece]] = [[], []]
       self.winner: PieceSide = PieceSide.EMPTY

    def can_reveal_check(self, move_given: Move):
        game_copy: Game = deepcopy(self)
        game_copy.perfom_move(move_given)
        iter_obj: Generator[str, None, None] = board_iterator()
        other_king = Piece(piece_type=PieceTypes.KING, piece_side=game_copy.side.other())
        cur_pos: str = next(iter_obj)
        try:
            while True:
                if game_copy.board[cur_pos].side == game_copy.side:
                    move_list = list(filter(partial(lambda move, game: move.move_type == MoveTypes.CAPTURE, game=game_copy), game_copy.get_all_moves(cur_pos, proto=True, simulation_illegal=True)))
                    if move_list:
                        #[self.logger.debug(f"{move_temp} kills {game_copy.board[move_temp.end]} {other_king.side} {other_king.type}") for move_temp in move_list]
                        king_kills = list(filter(partial(lambda move, game: game.board[move.end] == other_king, game=game_copy), move_list))
                        if len(king_kills) > 0:
                            #self.logger.debug("Illegal!")
                            return True
                        #else:
                        #    self.logger.debug(f"I hereby confirm that none of {move_list} can kill the king")
                cur_pos = next(iter_obj)
        except StopIteration:
            return False

    def does_check(self, move: Move):
        self.logger.debug(f"Checking if {move} checks")
        game_copy: Game = deepcopy(self)
        game_copy.perfom_move(move)
        iter_obj: Generator[str, None, None] = board_iterator()
        cur_pos: str = next(iter_obj)
        try:
            while True:
                if game_copy.board[cur_pos].side == move.piece.side:
                    all_moves = game_copy.get_all_moves(cur_pos, proto=True)
                    move_list = list(filter(lambda move: move.move_type == MoveTypes.CAPTURE, all_moves))
                    king_kills = list(filter(partial(lambda move, game: game.board[move.end] == Piece(PieceTypes.KING, move.piece.side.other()), game=game_copy), move_list))
                    if len(king_kills) > 0:
                        return True
                cur_pos = next(iter_obj)
        except StopIteration:
            return False

    def does_mate(self, move: Move):
        self.logger.debug(f"Only checking if {move} can mate")
        if not self.does_check:
            return False
        game_copy: Game = deepcopy(self)
        game_copy.perfom_move(move)
        moves = game_copy.get_every_move()
        self.logger.debug(moves)
        return (len(moves) == 0)
    
    def make_move(self, move: Move) -> Move:
        move.is_checking = self.does_check(move)
        move.is_mating = self.does_mate(move)
        return move

    def handle_vector_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        move_list: list[Move] = []
        make_move = self.make_move if not proto else lambda x: x
        for vector in move_gen.vectors:
            c=1
            cur_pos: str = chr(ord(pos[0]) + vector[0]) + str(int(pos[1]) + vector[1])
            while is_valid_square(cur_pos) and self.board[cur_pos] == Piece.empty() and c <= move_gen.limit:
                move = make_move(Move(MoveTypes.MOVE, start=pos, piece=piece, end=cur_pos))
                move_list.append(move)
                cur_pos = chr(ord(cur_pos[0]) + vector[0]) + str(int(cur_pos[1]) + vector[1])
                c+=1

            if is_valid_square(cur_pos) and c<= move_gen.limit and piece.side.other() == self.board[cur_pos].side:
                move_list.append(make_move(Move(MoveTypes.CAPTURE, start=pos, piece=piece, end=cur_pos)))

        return move_list 

    def handle_jump_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        move_list: list[Move] = []
        make_move = self.make_move if not proto else lambda x: x
        for offset in move_gen.offsets:
            cur_pos: str = chr(ord(pos[0]) + offset[0]) + str(int(pos[1]) + offset[1])
            if is_valid_square(cur_pos):
                if self.board[cur_pos] == Piece.empty() and not move_gen.only_capture:
                    move_list.append(make_move(Move(MoveTypes.MOVE, start=pos, piece=piece, end=cur_pos)))
                elif self.board[cur_pos].side == piece.side.other() and move_gen.can_capture:
                    move_list.append(make_move(Move(MoveTypes.CAPTURE, start=pos, piece=piece, end=cur_pos)))

        return move_list

    def handle_special_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        cur_pos: str = chr(ord(pos[0]) + move_gen.offset[0]) + str(int(pos[1]) + move_gen.offset[1])
        make_move = self.make_move if not proto else lambda x: x
        match move_gen.move_type:
            case MoveTypes.PROMOTION:
                if self.board[cur_pos] != Piece.empty():
                    if self.board[cur_pos].side == piece.side.other() and move_gen.can_capture:
                        return [make_move(Move(move_gen.move_type, start=pos, piece=piece, end=cur_pos, promotion_piece=x)) for x in (PieceTypes.QUEEN, PieceTypes.BISHOP, PieceTypes.ROOK, PieceTypes.KNIGHT)]
                elif not move_gen.only_capture:
                    return [make_move(Move(move_gen.move_type, start=pos, piece=piece, end=cur_pos, promotion_piece=x)) for x in (PieceTypes.QUEEN, PieceTypes.BISHOP, PieceTypes.ROOK, PieceTypes.KNIGHT)]

            case MoveTypes.EN_PASSANT:
                if cur_pos == self.en_passant:
                    return [make_move(Move(move_gen.move_type, start=pos, piece=piece, end=cur_pos, annex=move_gen.annex))]
        return []

    def handle_complex_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        move_list: list[Move] = []
        #self.logger.debug(pos)
        #self.logger.debug([x[1](self, pos) for x in move_gen.moves_conds.items()])
        for move, cond in move_gen.moves_conds.items():
            if cond(self, pos):
                match move.move_kind:
                    case MoveKind.VECTOR:
                        move_list.extend(self.handle_vector_moves(move, pos, piece, proto))
                    case MoveKind.JUMP:
                        move_list.extend(self.handle_jump_moves(move, pos, piece, proto))
                    case MoveKind.COMPLEX:
                        move_list.extend(self.handle_complex_moves(move, pos, piece, proto))
                    case MoveKind.SPECIAL:
                        move_list.extend(self.handle_special_moves(move, pos, piece, proto))

        return move_list

    def get_all_moves(self, pos: str, proto:bool=False, simulation_illegal: bool = False) -> list[Move]:
        move_list: list[Move] = []
        piece: Piece = self.board[pos]
        match piece.type.move_gen.move_kind:
            case MoveKind.VECTOR:
                move_list = self.handle_vector_moves(piece.type.move_gen, pos, piece, proto)
            case MoveKind.JUMP:
                move_list = self.handle_jump_moves(piece.type.move_gen, pos, piece, proto)
            case MoveKind.COMPLEX:
                move_list = self.handle_complex_moves(piece.type.move_gen, pos, piece, proto)
            case MoveKind.SPECIAL:
                move_list = self.handle_special_moves(piece.type.move_gen, pos, piece, proto)

        if not simulation_illegal:
            self.logger.debug("Simulating for illegal moves")
            move_list = list(filter(partial(lambda move, game: not game.can_reveal_check(move), game=self), move_list))
        #move_list = list(filter(partial(lambda move, game: game.board[move.end].side != move.piece.side, game=self), move_list))
        return move_list

    def get_every_move(self, proto: bool = False) -> list[Move]:
        move_list: list[Move] = []
        iter_obj = board_iterator()
        cur_pos = next(iter_obj)
        self.logger.debug("Entering")
        try:
            while True:
                if self.board[cur_pos].side == self.side:
                    move_list.extend(self.get_all_moves(cur_pos, proto=True))
                cur_pos = next(iter_obj)
        except StopIteration:
            self.logger.debug("Exiting")
            return move_list            

    def perfom_move(self, move: Move):
        self.logger.debug(f"Performing {move} for simulation")
        match move.move_type:
            case MoveTypes.MOVE | MoveTypes.EN_PASSANT:
                self.board[move.start] = Piece.empty()
                self.board[move.end] = move.piece
            case MoveTypes.CAPTURE:
                piece: Piece = self.board[move.end]
                self.board[move.start] = Piece.empty()
                self.board[move.end] = move.piece
                self.materials[move.piece.side.value].append(piece)
            case MoveTypes.KING_CASTLE | MoveTypes.QUEEN_CASTLE:
                pos_rook_2_move: str = chr(ord(move.start[0]) + 3 - 7 * (move.move_type.value - MoveTypes.KING_CASTLE.value)) + move.start[1]
                self.board[move.start] = Piece.empty()
                self.board[move.end] = move.piece
                rook: Piece = self.board[pos_rook_2_move]
                self.board[pos_rook_2_move] = Piece.empty()
                self.board[chr(ord(move.end[0]) + sign(ord('e') - ord(move.end[0])))+move.end[1]] = rook
                self.castling[ 2 - move.piece.side.value * 2 + (move.move_type.value - MoveTypes.KING_CASTLE.value)] = False
            case MoveTypes.PROMOTION:
                self.board[move.start] = Piece.empty()
                if not self.board[move.end] == Piece.empty():
                    self.materials[move.piece.side.value].append(piece)
                self.board[move.end] = Piece(move.promotion_piece, move.piece.side)
        
        if move.piece.side == PieceSide.DARK:
            self.num_moves += 1
        
        if move.piece.type == PieceTypes.PAWN:
            self.half_moves = 0
        else:
            self.half_moves += 1
        
        if move.move_type != MoveTypes.GAME_OVER:
            self.side = PieceSide((self.side.value + 1) % 2)
        
        if move.annex:
            move.annex(self, move.start, move.end)

    @staticmethod
    def fromFEN(FEN: str) -> Game:
        logger: Logger = get_logger(__name__)
        board: Board = Board.empty()

        FENreg: re.Pattern[str] = re.compile(r'\s*^(((?:[rnbqkpRNBQKP1-8]+\/){7})[rnbqkpRNBQKP1-8]+)\s([b|w])\s([K|Q|k|q]{1,4})\s(-|[a-h][1-8])\s(\d+\s\d+)$')

        if FENreg.match(FEN) is None:
            raise InvalidFENStringException()

        parts: list[str] = FEN.split()

        def next_pos(cur_pos = None) -> str:
            if cur_pos is None:
                return 'a8'
            if int(cur_pos[1]) >= 1:
                if cur_pos[0] == 'h':
                    cur_pos = 'a' + str(int(cur_pos[1])-1)
                else:
                    cur_pos = chr(ord(cur_pos[0])+1) + cur_pos[1]
            return cur_pos
        
        pos = None

        for letter in parts[0]:
            if letter.isalpha():
                pos = next_pos(pos)
                board[pos] = Piece(letter2type(letter), PieceSide(int(letter.isupper())))

            elif letter.isdigit():
                num = int(letter)
                while num > 0:
                    pos = next_pos(pos)
                    num -= 1

        
        side = PieceSide(int(parts[1] == 'w'))
        castling = tuple(i in parts[2] for i in 'KQkq')
        en_passant = None if parts[3] == "-" else parts[3]
        half_moves = int(parts[4])
        moves = int(parts[5])

        return Game(board, side, castling, en_passant, half_moves, moves, [])

    def conv2FEN(self) -> str:
        FEN = ""
        empty_counter = 0
        in_line = 0
        
        def mark_dirty():
            nonlocal in_line, FEN
            if in_line == 8:
                FEN+="/"
                in_line = 0

        def next_pos(cur_pos = None) -> str:
            if cur_pos is None:
                return 'a8'
            if int(cur_pos[1]) >= 1:
                if cur_pos[0] == 'h':
                    cur_pos = 'a' + str(int(cur_pos[1])-1)
                else:
                    cur_pos = chr(ord(cur_pos[0])+1) + cur_pos[1]
            return cur_pos
        
        pos = next_pos()
        while pos != next_pos(pos):
            mark_dirty()
            piece = self.board[pos]
            if empty_counter == 8:
                in_line += empty_counter
                FEN += str(empty_counter)
                empty_counter = 0
                mark_dirty()
            if piece == Piece.empty():
                pos = next_pos(pos)
                empty_counter += 1
                continue
            elif empty_counter > 0:
                in_line += empty_counter
                FEN += str(empty_counter)
                empty_counter = 0
                mark_dirty()
            FEN += str(piece.type.letter if not piece.side.value else piece.type.letter.upper())
            in_line += 1
            pos = next_pos(pos)
        quasi_castle = ''.join(compress(list('KQkq'), self.castling))
        FEN += f" {'w' if self.side.value else 'b' } {quasi_castle if quasi_castle else '-'} {self.en_passant if self.en_passant else '-'} {self.half_moves} {self.num_moves}"
        return FEN


    def FAN2Move(self: Game, FAN: str) -> Move:
        norm_move: re.Pattern[str] = re.compile(r'(?P<Piece>[rnbkqRNBKQ])?(?P<File>[a-h])?(?P<Rank>[1-8])?(?P<Capture>[x])?(?P<Position>[a-h][1-8])(?P<KingDanger>[+#])?') 
        score_end: re.Pattern[str] = re.compile(r'(?P<White>[0-1])-(?P<Black>[0-1])')

        finding = norm_move.match(FAN)
        if finding is None:
            if FAN =='O-O':
                return Move(MoveTypes.KING_CASTLE)
            elif FAN == 'O-O-O':
                return Move(MoveTypes.QUEEN_CASTLE)
            elif score_end.match(FAN):
                return Move(MoveTypes.self_OVER)
            else:
                raise InvalidFANStringException('Unknown format.')
        
        move_dict = norm_move.groupdict()
        if move_dict['Piece']:
            piece = letter2type(move_dict['Piece'])
        else:
            piece = PieceTypes.PAWN

        pos = move_dict['Position']

        pos_gen = board_iterator()
        cur_pos = next(pos_gen)
        possible_pieces = []
        try:
            while True:
                if self.board[cur_pos] == Piece(piece, self.side):
                    move_list = self.getAllMoves(cur_pos)
                    if pos in move_list:
                        possible_pieces.append(cur_pos)
                cur_pos = next(pos_gen)
        except StopIteration:
            if len(possible_pieces) == 0:
                raise InvalidFANStringException('Invalid move.')
            elif len(possible_pieces) == 1:
                return Move(MoveTypes.CAPTURE if move_dict['Capture'] else MoveTypes.MOVE, start=possible_pieces[0], piece=Piece(piece, self.side), end=pos)
            elif len(possible_pieces) > 1:
                m_poss_pieces = []
                to_scan = ''.join([move_dict[x] if move_dict[x] else '' for x in ('File', 'Rank')])
                for place in possible_pieces:
                    if to_scan in place:
                        m_poss_pieces.append(place)

                if len(m_poss_pieces) > 1 or len(m_poss_pieces) == 0:
                    raise InvalidFANStringException('Not enough information')
                
                start = m_poss_pieces[0]
                return Move(MoveTypes.CAPTURE if move_dict['Capture'] else MoveTypes.MOVE, start=start, piece=Piece(piece, self.side), end=pos)