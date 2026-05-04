from __future__ import annotations

from dataclasses import replace

try:
    from search.algorithms import astar, greedy_search
    from chess_pawn_mower.board import Board
    from chess_pawn_mower.moves import WHITE_PIECES, capture_targets
    from chess_pawn_mower.state import PawnMowerState
except (ModuleNotFoundError, ImportError):
    from algorithms import astar, greedy_search  # type: ignore
    from board import Board  # type: ignore
    from moves import WHITE_PIECES, capture_targets  # type: ignore
    from state import PawnMowerState  # type: ignore

MAX_ACTIONS = 100
_MST_CACHE  = {}

KING_DELTAS = (
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
)


# ── Estado inicial ────────────────────────────────────────────────────────────

def build_initial_state(board):
    return PawnMowerState(
        board=board,
        remaining_black_pawns=frozenset(board.find('p')),
        active_piece=None,
        active_origin_position=None,
        active_position=None,
        king_position=None,
        move_count=0,
    )


# ── Objectivo ─────────────────────────────────────────────────────────────────

def is_goal(state):
    return not state.remaining_black_pawns


# ── Heurística (MST de Chebyshev) ─────────────────────────────────────────────

def _chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _all_white_positions(board):
    for row, col, symbol in board.iter_cells():
        if symbol in WHITE_PIECES:
            yield row, col, symbol


def _mst_cost(points):
    key = tuple(sorted(points))
    cached = _MST_CACHE.get(key)
    if cached is not None:
        return cached
    pts = list(key)
    if len(pts) <= 1:
        _MST_CACHE[key] = 0.0
        return 0.0
    n = len(pts)
    used = [False] * n
    dist = [float('inf')] * n
    used[0] = True
    for i in range(1, n):
        dist[i] = _chebyshev(pts[0], pts[i])
    total = 0.0
    for _ in range(n - 1):
        best_i, best_d = -1, float('inf')
        for i in range(n):
            if not used[i] and dist[i] < best_d:
                best_d, best_i = dist[i], i
        if best_i == -1:
            break
        used[best_i] = True
        total += best_d
        for i in range(n):
            if not used[i]:
                d = _chebyshev(pts[best_i], pts[i])
                if d < dist[i]:
                    dist[i] = d
    _MST_CACHE[key] = total
    return total


def heuristic(state):
    pawns = state.remaining_black_pawns
    if not pawns:
        return 0.0
    mst = _mst_cost(tuple(pawns))
    pos = (state.active_position
           if state.active_position is not None
           else state.king_position)
    if pos is not None:
        return float(mst + min(_chebyshev(pos, p) for p in pawns))
    whites = [(r, c) for r, c, _ in _all_white_positions(state.board)]
    nearest = min((_chebyshev(w, p) for w in whites for p in pawns), default=0.0)
    return float(mst + nearest + 1.0)


# ── Célula efectiva (considera estado dinâmico) ───────────────────────────────

def _cell_at(state, row, col):
    pos = (row, col)
    if state.king_position is not None and pos == state.king_position:
        return 'R'
    if state.active_piece is not None and pos == state.active_position:
        return state.active_piece
    if pos in state.remaining_black_pawns:
        return 'p'
    if (state.active_origin_position is not None
            and pos == state.active_origin_position
            and state.active_position != state.active_origin_position):
        return ' '
    return state.board.get(row, col)


# ── Transições de estado ──────────────────────────────────────────────────────

def _activate_piece(state, position, symbol):
    return replace(
        state,
        active_piece=symbol,
        active_origin_position=position,
        active_position=position,
        king_position=None,
        move_count=state.move_count + 1,
    )


def _capture_with_active(state, destination):
    return replace(
        state,
        active_position=destination,
        active_origin_position=destination,
        remaining_black_pawns=frozenset(
            p for p in state.remaining_black_pawns if p != destination
        ),
        move_count=state.move_count + 1,
    )


def _enter_king_mode(state, king_dest):
    return replace(
        state,
        active_piece=None,
        active_position=None,
        king_position=king_dest,
        move_count=state.move_count + 1,
    )


def _move_king_step(state, destination):
    return replace(state, king_position=destination, move_count=state.move_count + 1)


# ── Ordenação dos sucessores ───────────────────────────────────────────────────

def _succ_key(item):
    _, nxt, _ = item
    return heuristic(nxt)


# ── Sucessores ────────────────────────────────────────────────────────────────

def successors(state):
    if state.move_count >= MAX_ACTIONS or is_goal(state):
        return []

    board = state.board

    # ── MODO 0: activar uma peça branca do tabuleiro ──────────────────────────
    if state.active_piece is None and state.king_position is None:
        results = []
        for row, col, symbol in _all_white_positions(board):
            sq = Board.index_to_square(row, col)
            results.append((sq, _activate_piece(state, (row, col), symbol), 1.0))
        results.sort(key=_succ_key)
        return results

    # ── MODO 2: drone em modo rei ─────────────────────────────────────────────
    if state.king_position is not None:
        results = []
        row_k, col_k = state.king_position
        for d_row, d_col in KING_DELTAS:
            nr, nc = row_k + d_row, col_k + d_col
            if not board.in_bounds(nr, nc):
                continue
            dest = (nr, nc)
            cell = _cell_at(state, nr, nc)
            sq   = Board.index_to_square(nr, nc)
            if cell == ' ':
                results.append((sq, _move_king_step(state, dest), 1.0))
            elif cell in WHITE_PIECES:
                results.append((sq, _activate_piece(state, dest, cell), 1.0))
        results.sort(key=_succ_key)
        return results

    # ── MODO 1: peça activa tenta capturar ────────────────────────────────────
    if state.active_piece is None or state.active_position is None:
        return []

    cell_fn = lambda r, c: _cell_at(state, r, c)
    apos = state.active_position

    captures = []
    for row, col in capture_targets(board, apos, state.active_piece, cell_at=cell_fn):
        dest = (row, col)
        if dest in state.remaining_black_pawns:
            sq = Board.index_to_square(row, col)
            captures.append((sq, _capture_with_active(state, dest), 1.0))

    if captures:
        captures.sort(key=_succ_key)
        return captures

    # Sem capturas: sair para modo rei — APENAS casas vazias adjacentes.
    # Activar peça branca adjacente requer SEMPRE 2 acções separadas:
    # (1) _enter_king_mode para a casa da peça  → Modo 2
    # (2) _activate_piece a partir do Modo 2    → Modo 1
    # Fazer em 1 acção seria fisicamente inválido e geraria soluções falsas.
    exit_results = []
    row_a, col_a = apos
    for d_row, d_col in KING_DELTAS:
        nr, nc = row_a + d_row, col_a + d_col
        if not board.in_bounds(nr, nc):
            continue
        if _cell_at(state, nr, nc) == ' ':
            sq = Board.index_to_square(nr, nc)
            exit_results.append((sq, _enter_king_mode(state, (nr, nc)), 1.0))

    exit_results.sort(key=_succ_key)
    return exit_results


# ── Resolução ─────────────────────────────────────────────────────────────────

def solve_board(board, time_limit_ms):
    initial_state = build_initial_state(board)
    if time_limit_ms is None:
        greedy_time = astar_time = None
    else:
        greedy_time = max(1, int(time_limit_ms * 0.85))
        astar_time  = max(1, time_limit_ms - greedy_time)

    # Fase 1: greedy — resolve instâncias possíveis rapidamente
    node = greedy_search(
        initial_state,
        is_goal=is_goal,
        successors=successors,
        heuristic=heuristic,
        time_limit_ms=greedy_time,
        max_nodes=8_000_000,
    )
    if node is not None:
        return node

    # Fase 2: A* exaustivo — prova impossibilidade (fila vazia) ou acha solução
    return astar(
        initial_state,
        is_goal=is_goal,
        successors=successors,
        heuristic=heuristic,
        time_limit_ms=astar_time,
        max_nodes=2_000_000,
    )


# ── Solução em string ─────────────────────────────────────────────────────────

def solution_string(node):
    if node is None:
        return ''
    return ' '.join(
        str(step.action) for step in node.path()[1:] if step.action is not None
    )
