import io
from pathlib import Path

import pytest

from app import services
from app.services import (
    dostepne_regiony,
    policz_wskazniki,
    raporty_roku,
    wczytaj_zbior,
    wykaz_raportow,
    zapisz_raport,
    zestawienie_regionow,
)

from .conftest import SCIEZKA_DANYCH


def test_dostepne_regiony_sa_posortowane():
    assert dostepne_regiony(SCIEZKA_DANYCH) == ["CZ", "DE", "PL"]


@pytest.mark.parametrize(
    ("region", "zamowienia", "przychod", "koszt", "marza"),
    [
        ("PL", 3, 37900.0, 27900.0, 0.2639),
        ("DE", 3, 56650.0, 42650.0, 0.2471),
        ("CZ", 2, 14300.0, 11550.0, 0.1923),
        (None, 8, 108850.0, 82100.0, 0.2458),
    ],
)
def test_policz_wskazniki_zgodne_z_wartosciami_odniesienia(region, zamowienia, przychod, koszt, marza):
    w = policz_wskazniki(SCIEZKA_DANYCH, region)
    assert w == {
        "region": region,
        "liczba_zamowien": zamowienia,
        "przychod": przychod,
        "koszt": koszt,
        "marza": marza,
    }


def test_nieznany_region_daje_marze_zero_bez_wyjatku():
    w = policz_wskazniki(SCIEZKA_DANYCH, "XX")
    assert (w["liczba_zamowien"], w["marza"]) == (0, 0.0)


def test_filtr_roku_zaweza_zamowienia():
    assert policz_wskazniki(SCIEZKA_DANYCH, "DE", 2026)["liczba_zamowien"] == 3
    pusty = policz_wskazniki(SCIEZKA_DANYCH, None, 2025)
    assert (pusty["liczba_zamowien"], pusty["marza"]) == (0, 0.0)


def test_zestawienie_regionow_w_kolejnosci_alfabetycznej():
    assert [w["region"] for w in zestawienie_regionow(SCIEZKA_DANYCH)] == ["CZ", "DE", "PL"]


def test_modul_uslug_nie_importuje_flaska():
    zrodlo = Path(services.__file__).read_text(encoding="utf-8")
    assert "flask" not in zrodlo.lower()


def test_magazyn_raportow(app):
    zapisz_raport(2027, "PL", "uwaga")
    zapisz_raport(2027, "DE")
    zapisz_raport(2028, "CZ")
    assert [r["region"] for r in raporty_roku(2027)] == ["PL", "DE"]
    assert raporty_roku(2027)[0]["uwagi"] == "uwaga"
    assert raporty_roku(2027)[1]["uwagi"] == ""
    assert len(wykaz_raportow()) == 3


def test_wczytaj_zbior_zlicza_wiersze_bez_naglowka():
    assert wczytaj_zbior(io.BytesIO(b"data,region,przychod,koszt\n2026-01-08,PL,1,1\n")) == 1


def test_wczytaj_zbior_wylicza_brakujace_kolumny_alfabetycznie():
    with pytest.raises(ValueError, match="brak kolumn: data, koszt, przychod, region"):
        wczytaj_zbior(io.BytesIO(b"a,b\n1,2\n"))


def test_wczytaj_zbior_odrzuca_bajty_niebedace_utf8():
    with pytest.raises(ValueError):
        wczytaj_zbior(io.BytesIO(bytes([0xFF, 0xFE, 0x00, 0x80])))


def test_wczytaj_zbior_pusty_plik():
    with pytest.raises(ValueError, match="brak kolumn"):
        wczytaj_zbior(io.BytesIO(b""))
