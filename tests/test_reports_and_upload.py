import pytest

from app.services import wykaz_raportow

from .conftest import CSV_POPRAWNY, plik_csv, pobierz_token, tekst

# ---------------------------------------------------------------- zapis raportu

def test_formularz_raportu_ma_pola_i_token(csrf_client):
    html = tekst(csrf_client.get("/raporty/nowy"))
    for nazwa in ("csrf_token", "rok", "region", "szczegoly", "uwagi"):
        assert f'name="{nazwa}"' in html
    assert "novalidate" in html


def test_poprawny_zapis_przekierowuje_303_i_pokazuje_komunikat_raz(client):
    odp = client.post("/raporty/nowy", data={"rok": "2027", "region": "PL", "uwagi": "Test"})
    assert odp.status_code == 303
    assert odp.headers["Location"].endswith("/raporty/2027")

    pierwszy = tekst(client.get("/raporty/2027"))
    assert 'class="komunikat sukces"' in pierwszy
    assert "Raport za rok 2027 zapisany" in pierwszy
    assert "Zapisane raporty: 1" in pierwszy
    assert "Raport za rok 2027 zapisany" not in tekst(client.get("/raporty/2027"))
    assert wykaz_raportow() == [{"rok": 2027, "region": "PL", "uwagi": "Test"}]


def test_zapis_za_rok_domyslny_wraca_na_adres_kanoniczny(client):
    odp = client.post("/raporty/nowy", data={"rok": "2026", "region": "DE"})
    assert odp.status_code == 303
    assert odp.headers["Location"].endswith("/raporty/")


def test_powtorzony_raport_daje_422(client):
    dane = {"rok": "2027", "region": "PL"}
    client.post("/raporty/nowy", data=dane)
    odp = client.post("/raporty/nowy", data=dane)
    assert odp.status_code == 422
    assert "Raport za ten rok i region już istnieje" in tekst(odp)
    assert len(wykaz_raportow()) == 1


@pytest.mark.parametrize(
    ("dane", "komunikat"),
    [
        ({"rok": "1900", "region": "PL"}, "Zakres 2020-2030"),
        ({"rok": "", "region": "PL"}, "Pole jest wymagane"),
        ({"rok": "2028", "region": "XX"}, "Nieprawidłowy wybór"),
        ({"rok": "2028", "region": "PL", "uwagi": "x" * 250}, "Najwyżej 200 znaków"),
    ],
)
def test_bledne_dane_zapisu_daja_422_z_komunikatem(client, dane, komunikat):
    odp = client.post("/raporty/nowy", data=dane)
    html = tekst(odp)
    assert odp.status_code == 422
    assert komunikat in html
    assert 'class="pole blad"' in html
    assert wykaz_raportow() == []


def test_po_bledzie_wartosc_wraca_do_kontrolki(client):
    html = tekst(client.post("/raporty/nowy", data={"rok": "1900", "region": "PL"}))
    assert 'value="1900"' in html


# ------------------------------------------------------------------------ CSRF

def test_zapis_z_tokenem_dziala(csrf_client):
    token = pobierz_token(csrf_client, "/raporty/nowy")
    odp = csrf_client.post("/raporty/nowy", data={"rok": "2027", "region": "PL", "csrf_token": token})
    assert odp.status_code == 303


def test_zapis_bez_tokenu_jest_odrzucony_przed_widokiem(csrf_client):
    odp = csrf_client.post("/raporty/nowy", data={"rok": "2028", "region": "PL"})
    html = tekst(odp)
    assert odp.status_code == 400
    assert "Błąd 400 · TADS" in html
    assert "<h1>400</h1>" in html
    assert "The CSRF token is missing." in html
    assert wykaz_raportow() == []


def test_nieprawidlowy_token_jest_odrzucony(csrf_client):
    pobierz_token(csrf_client, "/raporty/nowy")  # sesja z prawdziwym tokenem
    odp = csrf_client.post("/raporty/nowy", data={"rok": "2028", "region": "PL", "csrf_token": "podrobiony"})
    assert odp.status_code == 400
    assert "X-Czas-Ms" in odp.headers  # procedura after_request obejmuje tez odrzucone zadania


# ----------------------------------------------------------------- wczytanie CSV

def wyslij_plik(klient, **kwargs):
    return klient.post("/wczytaj", data=plik_csv(**kwargs), content_type="multipart/form-data")


def test_formularz_wczytania_ma_enctype_i_token(csrf_client):
    html = tekst(csrf_client.get("/wczytaj"))
    assert 'enctype="multipart/form-data"' in html
    assert 'name="csrf_token"' in html
    assert 'name="plik"' in html


def test_poprawny_plik_303_i_komunikat_raz(client):
    odp = wyslij_plik(client, nazwa="zbior.csv")
    assert odp.status_code == 303
    assert odp.headers["Location"].endswith("/wczytaj")
    assert "Wczytano 2 zamówień z pliku zbior.csv" in tekst(client.get("/wczytaj"))
    assert "Wczytano" not in tekst(client.get("/wczytaj"))


def test_nazwa_pliku_przechodzi_przez_secure_filename(client):
    wyslij_plik(client, nazwa="raport roczny (1).csv")
    assert "z pliku raport_roczny_1.csv" in tekst(client.get("/wczytaj"))


def test_brak_pliku_daje_422(client):
    odp = client.post("/wczytaj", data={}, content_type="multipart/form-data")
    assert odp.status_code == 422
    assert "Wskaż plik do wczytania" in tekst(odp)


def test_zle_rozszerzenie_daje_422(client):
    odp = wyslij_plik(client, nazwa="zbior.txt", zawartosc=b"abc", typ="text/plain")
    assert odp.status_code == 422
    assert "Dopuszczalny jest wyłącznie format CSV" in tekst(odp)


def test_zawartosc_binarna_w_pliku_csv_daje_422(client):
    odp = wyslij_plik(client, nazwa="zbior.csv", zawartosc=bytes([0xFF, 0xFE, 0x00, 0x80, 0x81]) * 4)
    assert odp.status_code == 422
    assert "Niepoprawna zawartość" in tekst(odp)


def test_plik_bez_wymaganych_kolumn_daje_422(client):
    odp = wyslij_plik(client, nazwa="brak_kolumn.csv", zawartosc=b"a,b\n1,2\n")
    html = tekst(odp)
    assert odp.status_code == 422
    assert "Niepoprawna zawartość: brak kolumn: data, koszt, przychod, region" in html


def test_limit_rozmiaru_zadania(app):
    assert app.config["MAX_CONTENT_LENGTH"] == 1024 * 1024


def test_zbyt_duzy_plik_daje_413_przed_widokiem(client):
    duzy = b"data,region,przychod,koszt\n" + b"2026-01-01,PL,1,1\n" * 120000
    odp = wyslij_plik(client, nazwa="duzy.csv", zawartosc=duzy)
    assert odp.status_code == 413
    assert "<h1>413</h1>" in tekst(odp)


def test_poprawny_plik_z_tokenem_przy_wlaczonym_csrf(csrf_client):
    token = pobierz_token(csrf_client, "/wczytaj")
    odp = csrf_client.post(
        "/wczytaj",
        data={"csrf_token": token, **plik_csv("zbior.csv", CSV_POPRAWNY)},
        content_type="multipart/form-data",
    )
    assert odp.status_code == 303
