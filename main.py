from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter

try:
    from chess_pawn_mower.problem import solution_string, solve_board
except (ModuleNotFoundError, ImportError):
    from problem import solution_string, solve_board  # type: ignore

try:
    from io_utils.instances import load_instances
except (ModuleNotFoundError, ImportError):
    from instances import load_instances  # type: ignore

try:
    from io_utils.csv_writer import write_results_csv
except (ModuleNotFoundError, ImportError):
    from csv_writer import write_results_csv  # type: ignore

DEFAULT_DIR = Path('.')
DEFAULT_CSV = Path('resultados.csv')


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instances-dir', type=Path, default=DEFAULT_DIR)
    parser.add_argument('--output', type=Path, default=DEFAULT_CSV)
    return parser


def run_batch(instances_dir, output):
    rows = []
    resolved = 0

    for loaded in load_instances(instances_dir, count=10):
        start = perf_counter()
        node = solve_board(loaded.board, time_limit_ms=10000)
        elapsed_ms = int((perf_counter() - start) * 1000)
        sol = solution_string(node)
        acoes = len(sol.split()) if sol else 0

        if sol:
            resolved += 1

        print('Instancia {} ... {} acoes={} tempo={}ms'.format(
            loaded.index,
            'com solucao' if sol else 'sem solucao',
            acoes,
            elapsed_ms,
        ))

        rows.append({
            'Instância': loaded.index,
            'Tempo(ms)': elapsed_ms,
            'Solução': sol,
        })

    print()
    print('===== INICIO CSV =====')
    print('Instância;Tempo(ms);Solução')
    for row in rows:
        print('{};{};{}'.format(row['Instância'], row['Tempo(ms)'], row['Solução']))

    write_results_csv(rows, output, expected_rows=10)
    print('Resolvidas: {}/10 -> {} gravado.'.format(resolved, output))
    return rows


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_batch(args.instances_dir, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())