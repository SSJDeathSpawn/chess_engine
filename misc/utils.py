from __future__ import annotations
from itertools import chain
from typing import TYPE_CHECKING
import re, math, json, string, random

if TYPE_CHECKING:
    from typing import Generator
    from engine.consts import PieceType

def board_iterator() -> Generator[str, None, None]:
    """Returns a generator that progressively scans through the chess board"""
    files: list[str] = [chr(i) for i in range(ord('a'), ord('i'))]
    ranks: list[str] = [str(i) for i in range(1,9)]
    for rank in ranks:
        for file in files:
            yield file + rank

def mini_chain(l: list) -> list:
    """Compacts a list of lists to a single list. In other words, makes a list of lists into a flat list"""
    return list(chain(*l))

def is_valid_square(pos: str) -> bool:
    """Checks if a given file and rank actually exist on a chess board."""
    prog: re.Pattern[str] = re.compile('^([a-h])([1-8])$')
    return bool(prog.match(pos))

sign = lambda x: (int)(math.copysign(1, x))

def generate_id(length:int=6):
    """Generates an ID and stores it in temp/generated_ids.json for later retreival and use"""
    with open("temp/generated_ids.json", "r") as f:
        generated = json.load(f)

    gen = "".join(random.choices(string.ascii_uppercase, k=length))
    
    while gen in generated:
        gen = ''.join(random.choices(string.ascii_uppercase, k=length))

    generated.append(gen)
    
    return gen