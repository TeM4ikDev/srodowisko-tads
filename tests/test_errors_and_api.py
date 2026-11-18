import pytest
from flask import abort

from app.services import zapisz_raport

from .conftest import tekst


def test_api_kpi_zwraca_surowe_wartosci(client):
    odp = client.get("/api/kpi?region=PL")
    assert odp.status_code == 200
    assert odp.get_json() == {
        "region": "PL",
        "liczba_zamowien": 3,
        "przychod": 37900.0,
        "koszt": 27900.0,
        "marza": 0.2639,
    }


@pytest.mark.parametrize("prefiks", ["/api", "/api/v2"])
def test_interfejs_dostepny_pod_obu_przedrostkach(client, prefiks):
    zapisz_raport(2027, "PL")
    odp = client.get(f"{prefiks}/raporty?rok=2027")
    assert odp.status_code == 200
    assert odp.get_json()["rok"] == 2027
    assert odp.get_json()["raporty"][0]["region"] == "PL"


def test_blueprinty_zarejestrowane(app):
    assert sorted(app.blueprints) == ["api", "api_v2", "panel"]


def test_punkt_koncowy_zachowuje_nazwe_mimo_dekoratora(app):
    assert app.view_functions["api.raporty"].__name__ == "raporty"


@pytest.mark.parametrize(
    ("adres", "kod", "opis"),
    [
        ("/api/raporty", 400, "Brak parametru rok"),
        ("/api/raporty?rok=abc", 400, "Parametr rok nie jest liczba"),
        ("/api/raporty?rok=2040", 422, "Parametr rok poza zakresem 2020-2030"),
        ("/api/kpi?region=XX", 404, "Nieznany region: XX"),
    ],
)
def test_bledy_api_to_dokument_json(client, adres, kod, opis):
    odp = client.get(adres)
    assert odp.status_code == kod
    assert odp.mimetype == "application/json"
    assert odp.get_json() == {"blad": opis, "kod": kod}


def test_blad_poza_api_to_strona_z_szablonu(client):
    odp = client.get("/regiony/XX")
    html = tekst(odp)
    assert odp.status_code == 404
    assert "<title>Błąd 404 · TADS</title>" in html or "Błąd 404 · TADS" in html
    assert "<h1>404</h1>" in html
    assert "<p>Nieznany region: XX</p>" in html
    assert "<nav>" in html and "<footer>" in html


def test_adres_bez_trasy_nie_powoduje_wyjatku(client):
    odp = client.get("/nie-ma-takiego-adresu")
    assert odp.status_code == 404
    assert "<nav>" in tekst(odp)


def test_opis_bledu_w_stronie_html_jest_escapowany(app):
    @app.get("/test-xss")
    def test_xss():
        abort(400, description="<script>alert(1)</script>")

    odp = app.test_client().get("/test-xss")
    html = tekst(odp)
    assert odp.status_code == 400
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>" not in html


def test_opis_bledu_w_json_to_surowy_tekst(client):
    assert client.get("/api/kpi?region=<script>").get_json()["blad"] == "Nieznany region: <script>"


def test_przekierowanie_nie_jest_zamieniane_na_blad(client):
    odp = client.get("/raporty/2026")
    assert odp.status_code == 308
    assert "<h1>308</h1>" not in tekst(odp)
