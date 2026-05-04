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
    active_origin_position: Optional[Tuple[int, int]] = None
    active_position: Optional[Tuple[int, int]] = None
    king_position: Optional[Tuple[int, int]] = None
    # move_count fora do hash: nao faz parte da identidade do estado.
    # O A* usa best_g para evitar ciclos — visited_positions foi REMOVIDO
    # porque causava pruning incorreto: estados com menos visited (mais
    # liberdade) eram descartados a favor de estados com custo menor mas
    # mais visited (menos liberdade), bloqueando solucoes validas.
    move_count: int = field(default=0, hash=False, compare=False)
