from datetime import date

import pytest

from app.filters import data_pl, liczba, procent, zl

TWARDA = " "


@pytest.mark.parametrize(
    ("wartosc", "miejsca", "oczekiwane"),
    [
        (3, 0, "3"),
        (1234567.5, 1, f"1{TWARDA}234{TWARDA}567,5"),
        (0, 2, "0,00"),
    ],
)
def test_liczba(wartosc, miejsca, oczekiwane):
    assert liczba(wartosc, miejsca) == oczekiwane


def test_zl_uzywa_twardych_spacji():
    assert zl(37900) == f"37{TWARDA}900,00{TWARDA}zł"


def test_procent():
    assert procent(0.2639) == "26,4%"
    assert procent(0.2639, 2) == "26,39%"
    assert procent(0.0) == "0,0%"


def test_data_pl_przyjmuje_date_i_tekst():
    assert data_pl(date(2026, 1, 8)) == "08.01.2026"
    assert data_pl("2026-01-08") == "08.01.2026"


def test_filtry_zarejestrowane_w_aplikacji(app):
    for nazwa in ("liczba", "zl", "procent", "data_pl"):
        assert nazwa in app.jinja_env.filters
