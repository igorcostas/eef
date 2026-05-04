from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from chess_pawn_mower.board import Board
    from chess_pawn_mower.problem import build_initial_state
    from chess_pawn_mower.state import PawnMowerState
except (ModuleNotFoundError, ImportError):
    from board import Board  # type: ignore
    from problem import build_initial_state  # type: ignore
    from state import PawnMowerState  # type: ignore

INSTANCE_FILE_PATTERN = 'instancia_{index}.txt'


@dataclass(frozen=True)
class LoadedInstance:
    index: int
    path: Path
    board: Board
    initial_state: PawnMowerState
    missing: bool = False


def iter_instance_paths(directory, count=10):
    for index in range(1, count + 1):
        yield directory / INSTANCE_FILE_PATTERN.format(index=index)


def _blank_board():
    return Board.from_line(' ' * 64)


def load_instance(path, index=None):
    missing = not path.exists()
    board = _blank_board() if missing else Board.from_line(path.read_text(encoding='utf-8'))
    return LoadedInstance(
        index=index if index is not None else 0,
        path=path,
        board=board,
        initial_state=build_initial_state(board),
        missing=missing,
    )


def load_instances(directory, count=10):
    instances = []
    for index, path in enumerate(iter_instance_paths(directory, count=count), start=1):
        instances.append(load_instance(path, index=index))
    return instances
