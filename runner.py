#!/usr/bin/env python3
"""
runner.py  —  Executa todos os algoritmos sobre as 10 instâncias,
              escreve resultados.csv e mostra feedback formatado no terminal.

Uso:
    python runner.py                        # instâncias em ./  , CSV em ./resultados.csv
    python runner.py --instances-dir pasta  --output saida.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from time import perf_counter
from typing import Optional

# ──────────────────────────────────────────────────────────────
#  Importa os módulos do teu projecto
# ──────────────────────────────────────────────────────────────
from chess_pawn_mower.problem import solution_string, solve_board
from config.parameters import (
    DEFAULT_RESULTS_CSV,
    INSTANCE_COUNT,
    INSTANCE_DIRECTORY,
    TIME_LIMIT_MS,
)
from io_utils.instances import load_instances

# ──────────────────────────────────────────────────────────────
#  Escrita do CSV
# ──────────────────────────────────────────────────────────────
CSV_HEADER = ("Instância", "Algoritmo", "Custo", "Tempo(ms)", "Solução")


def escrever_csv(
    rows: list[dict],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, delimiter=";")
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "Instância": r["instancia"],
                    "Algoritmo": r["algoritmo"],
                    "Custo":     r["custo"],
                    "Tempo(ms)": r["tempo_ms"],
                    "Solução":   r["solucao"],
                }
            )
    print(f"\n✅  CSV escrito em: {output_path}  ({len(rows)} linhas)")


# ──────────────────────────────────────────────────────────────
#  Feedback no terminal
# ──────────────────────────────────────────────────────────────
def mostrar_feedback(
    nome: str,
    rows: list[dict],
    melhor_custo_global: Optional[int] = None,
    pior_custo_global:   Optional[int] = None,
    melhor_tempo_global: Optional[int] = None,
) -> None:
    """
    rows  →  lista de dicts com chaves:
             instancia (int), resolvido (bool), custo (int), tempo_ms (int)

    Exemplo de output:
    ├─ 🎯 Soluções:10 📄 Instâncias: 10.
    ├─ 📄 :1 🎯 💰 4 ⏱ 44
    ...
    ├─ ⚖ 66.6% (🎯 100.0% 💰 0.0% ⏱ 99.7%)
    """
    SEP       = "─" * 58
    n_inst    = len(rows)
    n_sol     = sum(1 for r in rows if r["resolvido"])
    custo_tot = sum(r["custo"] for r in rows if r["resolvido"])
    tempo_tot = sum(r["tempo_ms"] for r in rows)

    print(f"\n{SEP}")
    print(f"  {nome}")
    print(f"{SEP}")

    # ── Cabeçalho ────────────────────────────────────────────
    print(f"├─ 🎯 Soluções:{n_sol} 📄 Instâncias: {n_inst}.")

    # ── Detalhe por instância ─────────────────────────────────
    for r in rows:
        ico = "🎯" if r["resolvido"] else "❌"
        print(f"├─ 📄 :{r['instancia']} {ico} 💰 {r['custo']} ⏱ {r['tempo_ms']}")

    # ── Rodapé ────────────────────────────────────────────────
    custo_vals = [r["custo"] for r in rows if r["resolvido"]]
    melhor_c   = min(custo_vals) if custo_vals else 0
    pior_c     = max(custo_vals) if custo_vals else 0

    print(f"├─ 🎯 Válidas:{n_sol} 📄 Instâncias: {n_inst}.")
    print(f"├─ 💰 Melhor:{melhor_c} 💰 Pior: {pior_c}.")
    print(f"├─ ⏱ Tempo(ms):{tempo_tot}.")

    # ── Percentagens ─────────────────────────────────────────
    perc_sol = (n_sol / n_inst * 100) if n_inst > 0 else 0.0

    # % custo  (100% = melhor global, 0% = pior global)
    if (
        melhor_custo_global is not None
        and pior_custo_global is not None
        and pior_custo_global != melhor_custo_global
    ):
        perc_custo = max(
            0.0,
            (1 - (custo_tot - melhor_custo_global)
               / (pior_custo_global - melhor_custo_global)) * 100,
        )
    else:
        perc_custo = 0.0   # sem referência comparativa

    # % tempo  (100% = algoritmo mais rápido)
    if melhor_tempo_global is not None and tempo_tot > 0:
        perc_tempo = min(100.0, melhor_tempo_global / tempo_tot * 100)
    else:
        perc_tempo = 0.0   # sem referência comparativa

    score = (perc_sol + perc_custo + perc_tempo) / 3
    print(
        f"├─ ⚖ {score:.1f}% "
        f"(🎯 {perc_sol:.1f}% "
        f"💰 {perc_custo:.1f}% "
        f"⏱ {perc_tempo:.1f}%)"
    )
    print(f"{SEP}\n")


# ──────────────────────────────────────────────────────────────
#  Execução do batch
# ──────────────────────────────────────────────────────────────
def run_batch(
    instances_dir: Path,
    nome_algoritmo: str = "Peões de Xadrez — A*",
) -> tuple[list[dict], list[dict]]:
    """
    Retorna:
        rows_feedback  →  para mostrar_feedback()
        rows_csv       →  para escrever_csv()
    """
    rows_feedback: list[dict] = []
    rows_csv:      list[dict] = []

    for loaded in load_instances(instances_dir, count=INSTANCE_COUNT):
        t0   = perf_counter()
        node = solve_board(loaded.board, time_limit_ms=TIME_LIMIT_MS)
        elapsed_ms = int((perf_counter() - t0) * 1000)

        sol_str   = solution_string(node) if node else ""
        resolvido = bool(node)
        # custo = número de movimentos (comprimento da solução)
        custo     = len(sol_str.split()) if sol_str else 0

        rows_feedback.append(
            {
                "instancia": loaded.index,
                "resolvido": resolvido,
                "custo":     custo,
                "tempo_ms":  elapsed_ms,
            }
        )
        rows_csv.append(
            {
                "instancia": loaded.index,
                "algoritmo": nome_algoritmo,
                "custo":     custo,
                "tempo_ms":  elapsed_ms,
                "solucao":   sol_str,
            }
        )

    return rows_feedback, rows_csv


# ──────────────────────────────────────────────────────────────
#  Argparse + Main
# ──────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="runner",
        description="Executa o batch, escreve resultados.csv e mostra feedback.",
    )
    p.add_argument(
        "--instances-dir",
        type=Path,
        default=INSTANCE_DIRECTORY,
        help="Diretório com instancia_1.txt … instancia_10.txt",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_CSV,
        help="Caminho do ficheiro resultados.csv",
    )
    p.add_argument(
        "--algoritmo",
        type=str,
        default="Peões de Xadrez — A*",
        help="Nome do algoritmo (usado no CSV e no feedback)",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    rows_fb, rows_csv = run_batch(
        instances_dir=args.instances_dir,
        nome_algoritmo=args.algoritmo,
    )

    # ── Escreve CSV ───────────────────────────────────────────
    escrever_csv(rows_csv, args.output)

    # ── Mostra feedback ───────────────────────────────────────
    # Referências para % custo e % tempo:
    # Preenche com os valores reais do melhor algoritmo quando
    # comparares mais do que um. Por agora sem referência → 0%.
    mostrar_feedback(
        nome=args.algoritmo,
        rows=rows_fb,
        melhor_custo_global=None,   # ex.: 1212 quando tiveres referência
        pior_custo_global=None,
        melhor_tempo_global=None,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
