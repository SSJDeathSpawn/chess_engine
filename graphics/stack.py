from __future__ import annotations
from typing import Any, TYPE_CHECKING, Iterator
from collections.abc import Iterable

from graphics.screen import Screen

if TYPE_CHECKING:
    pass

class ScreenStack(Iterable):

    def __init__(self) -> None:
        self.internal_list: list[Screen] = []

    def __iter__(self) -> Iterator:
        return self.internal_list.__iter__()
    
    def get_top(self) -> Screen:
        return self.internal_list[-1]
    
    def get_bottom(self) -> Screen:
        return self.internal_list[0]

    def push(self, obj: Screen) -> None:
        self.internal_list.append(obj)
    
    def pop(self) -> Screen:
        return self.internal_list.pop()