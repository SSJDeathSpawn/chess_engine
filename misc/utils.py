from __future__ import annotations
from itertools import chain
from typing import TYPE_CHECKING
import re
import math

if TYPE_CHECKING:
    from typing import Generator
    from data.consts import PieceType

def board_iterator() -> Generator[str, None, None]:
    files: list[str] = [chr(i) for i in range(ord('a'), ord('i'))]
    ranks: list[str] = [str(i) for i in range(1,9)]
    for rank in ranks:
        for file in files:
            yield file + rank

def mini_chain(l: list) -> list:
    return list(chain(*l))

def is_valid_square(pos: str) -> bool:
    prog: re.Pattern[str] = re.compile('^([a-h])([1-8])$')
    return bool(prog.match(pos))

sign = lambda x: math.copysign(1, x)