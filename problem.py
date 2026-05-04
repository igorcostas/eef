from __future__ import annotations

from dataclasses import replace

try:
    from search.algorithms import astar, greedy_search
    from chess_pawn_mower.board import Board
    from chess_pawn_mower.moves import WHITE_PIECES, capture_targets, king_step_targets
    from chess_pawn_mower.state import PawnMowerState
except (ModuleNotFoundError, ImportError):
    from algorithms import astar, greedy_search  # type: ignore
    from board import Board  # type: ignore
    from moves import WHITE_PIECES, capture_targets, king_step_targets  # type: ignore
    from state import PawnMowerState  # type: ignore

MAX_ACTIONS = 100
_MST_CACHE = {}
_NEAREST_CACHE = {}
KING_DELTAS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


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


def is_goal(state):
    return not state.remaining_black_pawns


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
        best_i = -1
        best_d = float('inf')
        for i in range(n):
            if not used[i] and dist[i] < best_d:
                best_d = dist[i]
                best_i = i
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


def _nearest_pawn_distance(state):
    key = (state.active_position, state.king_position, state.remaining_black_pawns)
    cached = _NEAREST_CACHE.get(key)
    if cached is not None:
        return cached
    pawns = state.remaining_black_pawns
    if not pawns:
        _NEAREST_CACHE[key] = 0
        return 0
    pos = state.active_position if state.active_position is not None else state.king_position
    if pos is not None:
        value = min(_chebyshev(pos, p) for p in pawns)
    else:
        whites = [(r, c) for r, c, _ in _all_white_positions(state.board)]
        value = min((_chebyshev(w, p) for w in whites for p in pawns), default=0)
    _NEAREST_CACHE[key] = value
    return value


def heuristic(state):
    pawns = tuple(state.remaining_black_pawns)
    if not pawns:
        return 0.0
    mst = _mst_cost(pawns)
    pos = state.active_position if state.active_position is not None else state.king_position
    if pos is not None:
        return mst + min(_chebyshev(pos, p) for p in pawns)
    whites = [(r, c) for r, c, _ in _all_white_positions(state.board)]
    nearest = min((_chebyshev(w, p) for w in whites for p in pawns), default=0.0)
    return mst + nearest + 1.0


def _cell_at(state, row, col):
    position = (row, col)
    if position == state.king_position:
        return 'R'
    if position == state.active_position and state.active_piece is not None:
        return state.active_piece
    if position in state.remaining_black_pawns:
        return 'p'
    if position == state.active_origin_position and state.active_position != state.active_origin_position:
        return ' '
    return state.board.get(row, col)


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
        remaining_black_pawns=frozenset(p for p in state.remaining_black_pawns if p != destination),
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


def _succ_key(item):
    action, nxt, _ = item
    return (
        len(nxt.remaining_black_pawns),
        _nearest_pawn_distance(nxt),
        nxt.move_count,
        action,
    )


def successors(state):
    if state.move_count >= MAX_ACTIONS or is_goal(state):
        return []

    board = state.board
    results = []

    if state.active_piece is None and state.active_position is None and state.king_position is None:
        whites = list(_all_white_positions(board))
        whites.sort(key=lambda t: min((_chebyshev((t[0], t[1]), p) for p in state.remaining_black_pawns), default=0))
        for row, col, symbol in whites:
            sq = Board.index_to_square(row, col)
            results.append((sq, _activate_piece(state, (row, col), symbol), 1.0))
        return results

    if state.king_position is not None:
        row, col = state.king_position
        for d_row, d_col in KING_DELTAS:
            nr, nc = row + d_row, col + d_col
            if not board.in_bounds(nr, nc):
                continue
            cell = _cell_at(state, nr, nc)
            sq = Board.index_to_square(nr, nc)
            if cell == ' ':
                results.append((sq, _move_king_step(state, (nr, nc)), 1.0))
            elif cell in WHITE_PIECES and cell != 'R':
                results.append((sq, _activate_piece(state, (nr, nc), cell), 1.0))
        results.sort(key=_succ_key)
        return results

    if state.active_piece is None or state.active_position is None:
        return []

    captures = []
    for row, col in capture_targets(board, state.active_position, state.active_piece, cell_at=lambda r, c: _cell_at(state, r, c)):
        if (row, col) in state.remaining_black_pawns:
            sq = Board.index_to_square(row, col)
            captures.append((sq, _capture_with_active(state, (row, col)), 1.0))
    if captures:
        captures.sort(key=_succ_key)
        return captures

    king_results = []
    for row, col in king_step_targets(board, state.active_position, cell_at=lambda r, c: _cell_at(state, r, c)):
        if _cell_at(state, row, col) == ' ':
            sq = Board.index_to_square(row, col)
            king_results.append((sq, _enter_king_mode(state, (row, col)), 1.0))
    king_results.sort(key=_succ_key)
    return king_results


def solve_board(board, time_limit_ms):
    initial_state = build_initial_state(board)
    if time_limit_ms is None:
        greedy_time = None
        astar_time = None
    else:
        greedy_time = max(1, int(time_limit_ms * 0.7))
        astar_time = max(1, time_limit_ms - greedy_time)

    node = greedy_search(initial_state, is_goal=is_goal, successors=successors, heuristic=heuristic, time_limit_ms=greedy_time, max_nodes=3_000_000)
    if node is not None:
        return node
    return astar(initial_state, is_goal=is_goal, successors=successors, heuristic=heuristic, time_limit_ms=astar_time, max_nodes=1_500_000)


def solution_string(node):
    if node is None:
        return ''
    return ' '.join(str(step.action) for step in node.path()[1:] if step.action is not None)
