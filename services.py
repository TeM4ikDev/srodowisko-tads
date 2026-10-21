"""Warstwa uslug: obliczenia wskaznikow niezalezne od frameworka webowego."""

import csv


def wczytaj_zamowienia(sciezka):
    """Zwraca liste zamowien; kolumny przychod i koszt przeksztalcone na float."""
    with open(sciezka, encoding="utf-8", newline="") as plik:
        return [
            {**wiersz, "przychod": float(wiersz["przychod"]), "koszt": float(wiersz["koszt"])}
            for wiersz in csv.DictReader(plik)
        ]


def dostepne_regiony(sciezka):
    """Zwraca posortowana liste kodow regionow wystepujacych w zbiorze."""
    return sorted({z["region"] for z in wczytaj_zamowienia(sciezka)})


def policz_wskazniki(sciezka, region=None):
    """Zwraca wskazniki dla regionu albo dla calego zbioru, gdy region jest None."""
    zamowienia = [
        z for z in wczytaj_zamowienia(sciezka) if region is None or z["region"] == region
    ]
    przychod = round(sum(z["przychod"] for z in zamowienia), 2)
    koszt = round(sum(z["koszt"] for z in zamowienia), 2)
    marza = round((przychod - koszt) / przychod, 4) if przychod else 0.0
    return {
        "region": region,
        "liczba_zamowien": len(zamowienia),
        "przychod": przychod,
        "koszt": koszt,
        "marza": marza,
    }
