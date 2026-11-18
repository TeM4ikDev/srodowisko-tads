import re
from datetime import date

import pytest

from .conftest import tekst

KOMUNIKAT_POMINIECIA = "Kryteria zawężenia zostały pominięte"


def tytul(html):
    return re.search(r"<title>([^<]*)</title>", html).group(1).strip()


def aktywne(html):
    return re.findall(r'<a[^>]*class="aktywna"[^>]*>\s*(\w+)\s*</a>', html)


def test_strona_glowna(client):
    assert tekst(client.get("/")) == "Panel wskaźników"


def test_panel_regionu_pl(client):
    odp = client.get("/kpi?region=PL")
    html = tekst(odp)
    assert odp.status_code == 200
    assert tytul(html) == "Wskaźniki: PL · TADS"
    assert html.count('class="kafelek"') == 4
    assert "26,4%" in html
    assert "37 900,00 zł" in html


def test_panel_bez_filtra_pokazuje_wszystkie_dane(client):
    html = tekst(client.get("/kpi"))
    assert "<h1>Wskaźniki: wszystkie</h1>" in html
    assert "24,6%" in html
    assert KOMUNIKAT_POMINIECIA not in html


def test_panel_filtr_regionu_i_roku_zachowuje_wartosci(client):
    html = tekst(client.get("/kpi?region=DE&rok=2026"))
    assert "<h1>Wskaźniki: DE</h1>" in html
    assert re.search(r'<option selected value="DE">', html)
    assert 'value="2026"' in html


def test_panel_rok_bez_zamowien_nie_zglasza_wyjatku(client):
    html = tekst(client.get("/kpi?rok=2025"))
    assert "0,0%" in html
    assert KOMUNIKAT_POMINIECIA not in html


@pytest.mark.parametrize(
    ("adres", "komunikat_pola"),
    [("/kpi?region=XX", "Nieprawidłowy wybór"), ("/kpi?rok=1900", "Zakres 2020-2030")],
)
def test_bledne_kryteria_nie_przerywaja_widoku(client, adres, komunikat_pola):
    odp = client.get(adres)
    html = tekst(odp)
    assert odp.status_code == 200
    assert KOMUNIKAT_POMINIECIA in html
    assert komunikat_pola in html
    assert "24,6%" in html  # pokazane sa wszystkie dane
    assert 'class="komunikat ostrzezenie"' in html


def test_komunikat_flash_wyswietlany_raz(client):
    assert KOMUNIKAT_POMINIECIA in tekst(client.get("/kpi?region=XX"))
    assert KOMUNIKAT_POMINIECIA not in tekst(client.get("/kpi"))


def test_formularz_filtra_jest_get_bez_tokenu(client):
    html = tekst(client.get("/kpi"))
    assert '<form method="get"' in html
    assert "csrf_token" not in html


def test_panel_regionu_nie_ma_formularza_filtra(client):
    html = tekst(client.get("/regiony/DE"))
    assert "<h1>Wskaźniki: DE</h1>" in html
    assert "<form" not in html


def test_nawigacja_ma_wszystkie_regiony_i_wyrozniony_aktywny(client):
    html = tekst(client.get("/kpi"))
    for kod in ("CZ", "DE", "PL"):
        assert f'href="/regiony/{kod}"' in html
    assert aktywne(tekst(client.get("/regiony/DE"))) == ["DE"]
    assert aktywne(tekst(client.get("/kpi?region=PL"))) == ["PL"]


def test_oceny_regionow_z_makra(client):
    assert re.findall(r'class="ocena (\w+)"', tekst(client.get("/kpi"))) == ["niska", "norma", "wysoka"]


def test_stopka_i_data_z_procesora_kontekstu(client):
    html = tekst(client.get("/kpi"))
    assert str(date.today().year) in re.search(r"<footer>(.*?)</footer>", html, re.DOTALL).group(1)
    assert date.today().strftime("%d.%m.%Y") in html
    assert "Regiony w zbiorze: 3 (CZ, DE, PL)" in html


def test_arkusz_stylow_jest_serwowany(client):
    odp = client.get("/static/styles.css")
    assert (odp.status_code, odp.mimetype) == (200, "text/css")


@pytest.mark.parametrize("adres", ["/regiony/pl", "/regiony/POL", "/regiony/XX"])
def test_nieprawidlowy_kod_regionu_daje_404(client, adres):
    assert client.get(adres).status_code == 404


def test_naglowek_czasu_w_kazdej_odpowiedzi(client):
    for adres in ("/", "/kpi", "/nie-ma-takiego-adresu", "/api/kpi?region=XX"):
        assert "X-Czas-Ms" in client.get(adres).headers


def test_stary_panel_przekierowuje_trwale(client):
    odp = client.get("/stary-panel")
    assert odp.status_code == 301
    assert odp.headers["Location"].endswith("/kpi")


def test_raport_domyslny_i_adres_kanoniczny(client):
    assert "Raport 2026" in tekst(client.get("/raporty/"))
    odp = client.get("/raporty/2026")
    assert odp.status_code == 308
    assert odp.headers["Location"].endswith("/raporty/")


@pytest.mark.parametrize("rok", ["2031", "2019", "abc", "-1"])
def test_rok_raportu_poza_wzorcem_daje_404(client, rok):
    assert client.get(f"/raporty/{rok}").status_code == 404


def test_konwerter_regionu_buduje_wielkie_litery(app):
    with app.test_request_context():
        from flask import url_for

        assert url_for("panel.region", kod="de") == "/regiony/DE"
