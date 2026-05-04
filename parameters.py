from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path('.')
INSTANCE_COUNT = 10
TIME_LIMIT_MS = 10_000
TIME_LIMIT_SECONDS = TIME_LIMIT_MS / 1000
DEFAULT_TIMEOUT_SECONDS = TIME_LIMIT_SECONDS
DEFAULT_RESULTS_CSV = Path('resultados.csv')
INSTANCE_FILE_PATTERN = 'instancia_{index}.txt'
INSTANCE_DIRECTORY = Path('.')
