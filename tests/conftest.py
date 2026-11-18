import io
import re

import pytest

from app import create_app, services

SCIEZKA_DANYCH = "dane/zamowienia.csv"
CSV_POPRAWNY = b"data,region,przychod,koszt\n2026-01-08,PL,1,1\n2026-01-09,DE,2,1\n"


@pytest.fixture
def app():
    """Aplikacja testowa: wlasny klucz, bez CSRF, pusty magazyn raportow."""
    app = create_app("rozwojowa")
    app.config.update(SECRET_KEY="klucz-testowy", WTF_CSRF_ENABLED=False)
    services._RAPORTY.clear()
    yield app
    services._RAPORTY.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_client(app):
    """Klient aplikacji z wlaczona ochrona CSRF."""
    app.config["WTF_CSRF_ENABLED"] = True
    return app.test_client()


def tekst(odpowiedz):
    return odpowiedz.get_data(as_text=True)


def pobierz_token(klient, adres):
    dopasowanie = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', tekst(klient.get(adres)))
    assert dopasowanie, f"brak tokenu CSRF w {adres}"
    return dopasowanie.group(1)


def plik_csv(nazwa, zawartosc=CSV_POPRAWNY, typ="text/csv"):
    return {"plik": (io.BytesIO(zawartosc), nazwa, typ)}
