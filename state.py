from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Tuple

try:
    from chess_pawn_mower.board import Board
except (ModuleNotFoundError, ImportError):
    from board import Board  # type: ignore

Position = Tuple[int, int]


@dataclass(frozen=True)
class PawnMowerState:
    board: Board
    remaining_black_pawns: FrozenSet[Position]
    active_piece: Optional[str] = None
    # active_origin_position: fora do hash/compare tal como move_count.
    # A origem da peca activa nao faz parte da identidade do estado --
    # apenas serve para calcular a celula vazia em _cell_at.
    # Se ficasse no hash, dois estados identicos (mesma peca, mesma posicao,
    # mesmos peoes) teriam hashes diferentes apos capturas encadeadas,
    # desactivando a deteccao de ciclos e permitindo loops infinitos.
    active_origin_position: Optional[Tuple[int, int]] = field(
        default=None, hash=False, compare=False
    )
    active_position: Optional[Tuple[int, int]] = None
    king_position: Optional[Tuple[int, int]] = None
    move_count: int = field(default=0, hash=False, compare=False)
