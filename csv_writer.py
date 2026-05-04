from __future__ import annotations

import csv
from itertools import islice
from pathlib import Path
from typing import Any, Iterable, Mapping

CSV_HEADER = ('Instância', 'Tempo(ms)', 'Solução')


def _normalise_solution(solution: Any) -> str:
    if not solution:
        return ''
    if isinstance(solution, str):
        return solution.strip()
    if isinstance(solution, (list, tuple)):
        return ' '.join(str(action).strip() for action in solution if action)
    return str(solution).strip()


def _normalise_row(
    row: Mapping[str, Any],
    fallback_id: int,
) -> dict[str, str]:
    return {
        'Instância': str(row.get('Instância') or row.get('ID', fallback_id)),
        'Tempo(ms)': str(row.get('Tempo(ms)', '')).strip(),
        'Solução': _normalise_solution(row.get('Solução', '')),
    }


def write_results_csv(
    rows: Iterable[Mapping[str, Any]],
    output_path: Path,
    expected_rows: int = 10,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalised_rows = list(islice(rows, expected_rows))
    while len(normalised_rows) < expected_rows:
        normalised_rows.append({'Instância': len(normalised_rows) + 1, 'Tempo(ms)': '', 'Solução': ''})

    with output_path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADER, delimiter=';')
        writer.writeheader()
        for index, row in enumerate(normalised_rows, start=1):
            writer.writerow(_normalise_row(row, index))
