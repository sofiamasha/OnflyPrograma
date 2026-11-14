"""Testes adicionais para requisitos não cobertos pela suíte fornecida."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import BASE, COLUMNS, PROJECT_ROOT, SRC_DIR, run_cli


def run_invalid_cli(
    tmp_path: Path,
    *,
    currency: str = "BRL",
    corrupt_file: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Executa o CLI com arquivos controlados para validar erros de entrada."""
    input_path = tmp_path / "reservas.csv"
    rates_path = tmp_path / "rates.csv"
    output_path = tmp_path / "report.json"

    if corrupt_file == "input":
        input_path.write_bytes(b"\xff")
    else:
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({**BASE, "currency": currency})

    if corrupt_file == "rates":
        rates_path.write_bytes(b"\xff")
    else:
        rates_path.write_text("currency,rate_to_brl\nBRL,1.000000\n", encoding="utf-8")

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "onfly_report",
            "--input",
            str(input_path),
            "--rates",
            str(rates_path),
            "--output",
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_reads_more_than_two_hundred_reservations(tmp_path):
    """A leitura processa o arquivo inteiro, sem um limite artificial de linhas."""
    rows = [{"reservation_id": f"R-{number}"} for number in range(201)]

    report = run_cli(tmp_path, rows)

    assert report["summary"]["total_reservations"] == 201


def test_top_hotels_breaks_amount_ties_by_hotel_id(tmp_path):
    """Empates de valor usam hotel_id crescente sem inverter o critério secundário."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H02", "hotel_name": "Hotel B", "amount": "100.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "hotel_name": "Hotel A", "amount": "100.00"},
            {"reservation_id": "R-3", "hotel_id": "H00", "hotel_name": "Hotel C", "amount": "50.00"},
        ],
        top=3,
    )

    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01", "H02", "H00"]


def test_missing_exchange_rate_is_invalid_input(tmp_path):
    """Moeda sem taxa é entrada inválida e retorna o código documentado."""
    process = run_invalid_cli(tmp_path, currency="USD")

    assert process.returncode == 2
    assert "falha ao ler a entrada" in process.stderr


@pytest.mark.parametrize("corrupt_file", ["input", "rates"])
def test_invalid_utf8_is_invalid_input(tmp_path, corrupt_file):
    """CSV fora de UTF-8 é entrada inválida, tanto nas reservas quanto nas taxas."""
    process = run_invalid_cli(tmp_path, corrupt_file=corrupt_file)

    assert process.returncode == 2
    assert "falha ao ler a entrada" in process.stderr


def test_money_keeps_decimal_precision(tmp_path):
    """Valores monetários não passam por float durante a conversão."""
    report = run_cli(tmp_path, [{"amount": "9999999999999999.99"}])

    assert report["summary"]["total_amount_brl"] == "9999999999999999.99"


def test_money_is_summed_before_rounding(tmp_path):
    """Parcelas fracionárias são somadas exatamente e arredondadas apenas no relatório."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "amount": "0.005"},
            {"reservation_id": "R-2", "amount": "0.005"},
        ],
    )

    assert report["summary"]["total_amount_brl"] == "0.01"
    assert report["summary"]["average_nightly_rate_brl"] == "0.01"


def test_average_is_zero_without_confirmed_room_nights(tmp_path):
    """Sem noites faturáveis, total e média são zero e não há agregações."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "CANCELLED"},
            {"reservation_id": "R-2", "status": "NO_SHOW"},
        ],
    )

    assert report["summary"]["total_room_nights"] == 0
    assert report["summary"]["total_amount_brl"] == "0.00"
    assert report["summary"]["average_nightly_rate_brl"] == "0.00"
    assert report["by_month"] == []
    assert report["top_hotels"] == []
