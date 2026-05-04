from __future__ import annotations

from collections.abc import Iterable
from typing import Callable, List, Optional, Tuple

try:
    from chess_pawn_mower.board import Board
except (ModuleNotFoundError, ImportError):
    from board import Board  # type: ignore

Position = Tuple[int, int]

ROOK_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
BISHOP_DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
KNIGHT_DELTAS = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
KING_DELTAS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)
WHITE_PIECES = {'P', 'T', 'B', 'C', 'D', 'R'}
ACTIVATABLE_PIECES = {'P', 'T', 'B', 'C', 'D'}


def is_white_piece(symbol):  # type: (str) -> bool
    return symbol in WHITE_PIECES


def is_black_pawn(symbol):  # type: (str) -> bool
    return symbol == 'p'


def _line_capture_moves(board, origin, directions, cell_at=None):
    cell_at = cell_at or board.get
    row, col = origin
    targets = []
    for d_row, d_col in directions:
        current_row, current_col = row + d_row, col + d_col
        while board.in_bounds(current_row, current_col):
            cell = cell_at(current_row, current_col)
            if cell == ' ':
                current_row += d_row
                current_col += d_col
                continue
            if is_black_pawn(cell):
                targets.append((current_row, current_col))
            break
    return targets


def rook_captures(board, origin, cell_at=None):
    return _line_capture_moves(board, origin, ROOK_DIRECTIONS, cell_at)


def bishop_captures(board, origin, cell_at=None):
    return _line_capture_moves(board, origin, BISHOP_DIRECTIONS, cell_at)


def queen_captures(board, origin, cell_at=None):
    return rook_captures(board, origin, cell_at) + bishop_captures(board, origin, cell_at)


def knight_captures(board, origin, cell_at=None):
    cell_at = cell_at or board.get
    row, col = origin
    targets = []
    for d_row, d_col in KNIGHT_DELTAS:
        next_row, next_col = row + d_row, col + d_col
        if board.in_bounds(next_row, next_col) and is_black_pawn(cell_at(next_row, next_col)):
            targets.append((next_row, next_col))
    return targets


def king_captures(board, origin, cell_at=None):
    cell_at = cell_at or board.get
    row, col = origin
    targets = []
    for d_row, d_col in KING_DELTAS:
        next_row, next_col = row + d_row, col + d_col
        if board.in_bounds(next_row, next_col) and is_black_pawn(cell_at(next_row, next_col)):
            targets.append((next_row, next_col))
    return targets


def pawn_captures(board, origin, cell_at=None):
    cell_at = cell_at or board.get
    row, col = origin
    targets = []
    for d_col in (-1, 1):
        next_row, next_col = row + 1, col + d_col
        if board.in_bounds(next_row, next_col) and is_black_pawn(cell_at(next_row, next_col)):
            targets.append((next_row, next_col))
    return targets


def capture_targets(board, origin, piece, cell_at=None):
    if piece == 'T':
        return rook_captures(board, origin, cell_at)
    elif piece == 'B':
        return bishop_captures(board, origin, cell_at)
    elif piece == 'C':
        return knight_captures(board, origin, cell_at)
    elif piece == 'D':
        return queen_captures(board, origin, cell_at)
    elif piece == 'R':
        return king_captures(board, origin, cell_at)
    elif piece == 'P':
        return pawn_captures(board, origin, cell_at)
    else:
        return []


def king_step_targets(board, origin, cell_at=None):
    """Devolve apenas casas VAZIAS adjacentes ao rei (1 passo).
    Casas com peões pretos ou peças brancas são excluídas —
    o rei só se pode mover para casas livres.
    """
    cell_at = cell_at or board.get
    row, col = origin
    targets = []
    for d_row, d_col in KING_DELTAS:
        next_row, next_col = row + d_row, col + d_col
        if not board.in_bounds(next_row, next_col):
            continue
        cell = cell_at(next_row, next_col)
        # Só casas completamente vazias são destinos válidos do rei
        if cell == ' ':
            targets.append((next_row, next_col))
    return targets
