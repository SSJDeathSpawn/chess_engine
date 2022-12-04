from __future__ import annotations
from functools import partial
from typing import TYPE_CHECKING, Generator, Optional
from itertools import compress
import re
from copy import deepcopy

from loguru import logger

if TYPE_CHECKING:
    pass

from engine.consts import MoveKind, MoveTypes, PieceSide
from engine.board import Board
from engine.piece import Piece, letter2type, PieceTypes
from engine.move import Move
from engine.exceptions import InvalidFENStringException, InvalidPGNStringException
from engine.move_gen import MoveGenerator

from misc.utils import board_iterator, is_valid_square, sign

class Game(object):
    """Holds all the data and the actions relating the progress of the game."""

    def __init__(self, board: Board, side: PieceSide, castling: tuple[bool, bool, bool, bool], en_passant: str | None, half_moves: int, num_moves: int, moves: list[Move]):
       self.board: Board = board
       self.side: PieceSide = side
       self.castling: tuple[bool, bool, bool, bool] = castling
       self.en_passant: str | None = en_passant
       self.half_moves: int = half_moves
       self.num_moves: int = num_moves
       self.moves = moves
       self.materials: list[list[Piece]] = [[], []]
       self.winner: PieceSide = PieceSide.EMPTY

    def can_reveal_check(self, move_given: Move) -> bool:
        """
        Return `True` if the given move is illegal by manner of revealing a line of attack between the enemy and the king.

        Parameters:
        - `move_given`: the move which is to be checked.
        """

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

    def does_check(self, move: Move) -> bool:
        """
        Returns `True` if the move provided reveals a line of attack between the piece moved and the enemy king.

        Paramters:
        - `move`: The move to check.
        """
        
        logger.debug(f"Checking if {move} checks")
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
        """
        Returns `True` if the move provided reveals a line of attack between the piece moved and the enemy king in such a way that there is no legal moves on the enemy's side.

        Parameters:
        - `move`: The move to check.
        """
        
        logger.debug(f"Only checking if {move} can mate")
        if not self.does_check:
            return False
        game_copy: Game = deepcopy(self)
        game_copy.perfom_move(move)
        moves = game_copy.get_every_move()
        logger.debug(moves)
        return (len(moves) == 0)
    
    def make_move(self, move: Move) -> Move:
        """
        Formats and returns a non prototype move to include whether the move performs a check or a mate.

        Paramters:
        - `move`: The move to add information to.
        """
        
        move.is_checking = self.does_check(move)
        move.is_mating = self.does_mate(move)
        return move

    def handle_vector_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        """
        Generates all possible moves from a vector type move generator object.
        
        Parameters:
        - `move_gen`: The vector type move_generator.
        - `pos`: The position of the piece whose move generator is provided.
        - `piece`: The piece itself whose position and move generator is given.
        - `proto`: A boolean value linked to whether this move is for simulation or for actual play.
        """
        
        move_list: list[Move] = []
        make_move = self.make_move if not proto else lambda x: x
        for vector in move_gen.vectors:
            c=1
            cur_pos: str = chr(ord(pos[0]) + vector[0]) + str(int(pos[1]) + vector[1])
            while is_valid_square(cur_pos) and self.board[cur_pos] == Piece.empty() and c <= move_gen.limit:
                move = make_move(Move(MoveTypes.MOVE, pos, piece, cur_pos))
                move_list.append(move)
                cur_pos = chr(ord(cur_pos[0]) + vector[0]) + str(int(cur_pos[1]) + vector[1])
                c+=1

            if is_valid_square(cur_pos) and c<= move_gen.limit and piece.side.other() == self.board[cur_pos].side:
                move_list.append(make_move(Move(MoveTypes.CAPTURE, pos, piece, cur_pos)))

        return move_list 

    def handle_jump_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        """
        Generates all possible moves from a jump type move generator object.
        
        Parameters:
        - `move_gen`: The jump type move_generator.
        - `pos`: The position of the piece whose move generator is provided.
        - `piece`: The piece itself whose position and move generator is given.
        - `proto`: A boolean value linked to whether this move is for simulation or for actual play.
        """

        move_list: list[Move] = []
        make_move = self.make_move if not proto else lambda x: x
        for offset in move_gen.offsets:
            cur_pos: str = chr(ord(pos[0]) + offset[0]) + str(int(pos[1]) + offset[1])
            if is_valid_square(cur_pos):
                if self.board[cur_pos] == Piece.empty() and not move_gen.only_capture:
                    move_list.append(make_move(Move(MoveTypes.MOVE, pos, piece, cur_pos)))
                elif self.board[cur_pos].side == piece.side.other() and move_gen.can_capture:
                    move_list.append(make_move(Move(MoveTypes.CAPTURE, pos, piece, cur_pos)))

        return move_list

    def handle_special_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        """
        Generates all possible moves from a special type move generator object.
        
        Parameters:
        - `move_gen`: The vector_type move_generator.
        - `pos`: The position of the piece whose move generator is provided.
        - `piece`: The piece itself whose position and move generator is given.
        - `proto`: A boolean value linked to whether this move is for simulation or for actual play.
        """

        cur_pos: str = chr(ord(pos[0]) + move_gen.offset[0]) + str(int(pos[1]) + move_gen.offset[1])
        make_move = self.make_move if not proto else lambda x: x
        match move_gen.move_type:
            case MoveTypes.PROMOTION:
                if self.board[cur_pos] != Piece.empty():
                    if self.board[cur_pos].side == piece.side.other() and move_gen.can_capture:
                        return [make_move(Move(move_gen.move_type, pos, piece, cur_pos, promotion_piece=x)) for x in (PieceTypes.QUEEN, PieceTypes.BISHOP, PieceTypes.ROOK, PieceTypes.KNIGHT)]
                elif not move_gen.only_capture:
                    return [make_move(Move(move_gen.move_type, pos, piece, cur_pos, promotion_piece=x)) for x in (PieceTypes.QUEEN, PieceTypes.BISHOP, PieceTypes.ROOK, PieceTypes.KNIGHT)]

            case MoveTypes.EN_PASSANT:
                if cur_pos == self.en_passant:
                    return [make_move(Move(move_gen.move_type, pos, piece, cur_pos, annex=move_gen.annex))]
        return []

    def handle_complex_moves(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        """
        Generates all possible moves from a complex type move generator object.
        
        Parameters:
        - `move_gen`: The vector_type move_generator.
        - `pos`: The position of the piece whose move generator is provided.
        - `piece`: The piece itself whose position and move generator is given.
        - `proto`: A boolean value linked to whether this move is for simulation or for actual play.
        """

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

    def handle_move(self, move_gen: MoveGenerator, pos: str, piece: Piece, proto:bool=False) -> list[Move]:
        """
        General purpose move generation from a move_generator. Use this when unsure of move generator kind.

        Parameters:
        - `move_gen`: The move generator from which to generate moves from.
        - `pos`: Starting position of the piece from which these moves will generated from.
        - `piece`:  The piece whose move is begin generated.
        - `proto`: Whether this is for simuation or for actual play.
        
        """

        match move_gen.move_kind:
            case MoveKind.VECTOR:
                move_list = self.handle_vector_moves(move_gen, pos, piece, proto)
            case MoveKind.JUMP:
                move_list = self.handle_jump_moves(move_gen, pos, piece, proto)
            case MoveKind.COMPLEX:
                move_list = self.handle_complex_moves(move_gen, pos, piece, proto)
            case MoveKind.SPECIAL:
                move_list = self.handle_special_moves(move_gen, pos, piece, proto)
        return move_list

    def get_all_moves(self, pos: str, proto:bool=False, simulation_illegal: bool = False) -> list[Move]:
        """
        Get all possible moves for a piece in a game that may or may not be legal based on arguments passed.

        Parameters:
        - `pos`: The position of the piece whose moves you want.
        - `proto`: Is it to be used in simulation?
        - `simulation_illegal`: Is it to be used for checking whether a move is illegal?
        """
        
        piece: Piece = self.board[pos]
        move_list = self.handle_move(piece.type.move_gen, pos, piece, proto)

        if not simulation_illegal:
            move_list = list(filter(partial(lambda move, game: not game.can_reveal_check(move), game=self), move_list))
        #move_list = list(filter(partial(lambda move, game: game.board[move.end].side != move.piece.side, game=self), move_list))
        return move_list

    def get_every_move(self, proto: bool = False) -> list[Move]:
        """
        Gets all moves possible on the board that isn't illegal.

        Parameters:
        - `proto`: Is it to be used for simulation?
        """
        
        move_list: list[Move] = []
        iter_obj = board_iterator()
        cur_pos = next(iter_obj)
        logger.debug("Entering")
        try:
            while True:
                if self.board[cur_pos].side == self.side:
                    move_list.extend(self.get_all_moves(cur_pos, proto=True))
                cur_pos = next(iter_obj)
        except StopIteration:
            logger.debug("Exiting")
            return move_list            

    def perfom_move(self, move: Move):
        """
        Simulate the movement of a piece according to the type of piece and type of move and store it's data.

        Parameters:
        - `move`: The move that it should perform.
        """
        
        logger.debug(f"Performing {move} for simulation")
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
                self.castling = self.castling[ :3 - move.piece.side.value * 2 + (move.move_type.value - MoveTypes.KING_CASTLE.value)]+(False,) + self.castling[4 - move.piece.side.value * 2 + (move.move_type.value - MoveTypes.KING_CASTLE.value):]
            case MoveTypes.PROMOTION:
                self.board[move.start] = Piece.empty()
                if not self.board[move.end] == Piece.empty():
                    self.materials[move.piece.side.value].append(self.board[move.end])
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
        """
        Get a game instance from a FEN string with all it's values

        Parameters:
        - `FEN`: The Forsyth-Edward notated string of the game
        """
        
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
                board[pos] = Piece((PieceTypes)(letter2type(letter)), PieceSide(int(letter.isupper())))

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
        """
        Converts the data of the game into FEN string to be used for storage.
        """
        
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

    def PGN2Move(self: Game, PGN: str) -> Optional[Move]:
        """
        Convert a PGN to a form of data usable by the game object.
        """ 
        
        norm_move: re.Pattern[str] = re.compile(r'(?P<Piece>[RNBKQ])?(?P<File>[a-h])?(?P<Rank>[1-8])?(?P<Capture>[x])?(?P<Position>[a-h][1-8])(?P<KingDanger>[+#])?') 
        score_end: re.Pattern[str] = re.compile(r'(?P<White>[0-1])-(?P<Black>[0-1])')

        finding: re.Match | None = norm_move.match(PGN)
        if finding is None:
            if PGN =='O-O':
                match self.side:
                    case PieceSide.LIGHT:
                        return Move(MoveTypes.KING_CASTLE, 'e1', Piece(PieceTypes.KING, PieceSide.LIGHT), 'g1')
                    case PieceSide.DARK:
                        return Move(MoveTypes.KING_CASTLE, 'e8', Piece(PieceTypes.KING, PieceSide.DARK), 'g8')
            elif PGN == 'O-O-O':
                match self.side:
                    case PieceSide.LIGHT:
                        return Move(MoveTypes.QUEEN_CASTLE, 'e1', Piece(PieceTypes.KING, PieceSide.LIGHT), 'b1')
                    case PieceSide.DARK:
                        return Move(MoveTypes.QUEEN_CASTLE, 'e8', Piece(PieceTypes.KING, PieceSide.DARK), 'b8')
            elif score_end.match(PGN):
                return None
            else:
                raise InvalidPGNStringException('Unknown format.')
        else:
            move_dict = finding.groupdict()
            if move_dict['Piece']:
                piece = (PieceTypes)(letter2type(move_dict['Piece']))
            else:
                piece = PieceTypes.PAWN

            logger.debug(piece)

            pos = move_dict['Position']

            pos_gen = board_iterator()
            cur_pos = next(pos_gen)
            possible_pieces = []
            try:
                while True:
                    if self.board[cur_pos] == Piece(piece, self.side):
                        move_list = self.get_all_moves(cur_pos)
                        if pos in map(lambda x: x.end, move_list):
                            possible_pieces.append(cur_pos)
                    cur_pos = next(pos_gen)
            except StopIteration:
                if len(possible_pieces) == 0:
                    raise InvalidPGNStringException('Invalid move.')
                elif len(possible_pieces) == 1:
                    return Move(MoveTypes.CAPTURE if move_dict['Capture'] else MoveTypes.MOVE, possible_pieces[0], Piece(piece, self.side), pos)
                elif len(possible_pieces) > 1:
                    m_poss_pieces = []
                    to_scan = ''.join([move_dict[x] if move_dict[x] else '' for x in ('File', 'Rank')])
                    for place in possible_pieces:
                        if to_scan in place:
                            m_poss_pieces.append(place)

                    if len(m_poss_pieces) > 1 or len(m_poss_pieces) == 0:
                        raise InvalidPGNStringException('Not enough information')
                    
                    start ,= m_poss_pieces
                    return Move(MoveTypes.CAPTURE if move_dict['Capture'] else MoveTypes.MOVE, start, Piece(piece, self.side), pos)