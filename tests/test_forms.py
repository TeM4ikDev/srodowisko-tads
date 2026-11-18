import pytest
from werkzeug.datastructures import MultiDict

from app.forms import FiltrForm, FormularzBazowy, RaportForm

REGIONY = [("CZ", "CZ"), ("DE", "DE"), ("PL", "PL")]


def filtr(app, **dane):
    with app.test_request_context():
        f = FiltrForm(MultiDict(dane))
        f.region.choices = [("", "wszystkie"), *REGIONY]
        f.validate()
        return f


def raport(app, istniejace=(), **dane):
    with app.test_request_context():
        f = RaportForm(formdata=MultiDict(dane), istniejace=istniejace)
        f.region.choices = REGIONY
        f.validate()
        return f


def test_formularz_bazowy_ma_polskie_komunikaty():
    assert FormularzBazowy.Meta.locales == ["pl"]


def test_filtr_nie_ma_tokenu_csrf(app):
    assert "csrf_token" not in filtr(app)._fields


def test_filtr_pusty_jest_poprawny(app):
    assert filtr(app).errors == {}


def test_filtr_poprawne_dane(app):
    f = filtr(app, region="DE", rok="2026")
    assert f.errors == {}
    assert (f.region.data, f.rok.data) == ("DE", 2026)


@pytest.mark.parametrize("rok", ["1900", "2031"])
def test_filtr_rok_poza_zakresem(app, rok):
    assert filtr(app, rok=rok).errors == {"rok": ["Zakres 2020-2030"]}


def test_filtr_nieznany_region(app):
    assert filtr(app, region="XX").errors == {"region": ["Nieprawidłowy wybór"]}


def test_filtr_rok_nie_liczba_daje_dwa_komunikaty(app):
    bledy = filtr(app, rok="abc").errors["rok"]
    assert "Zakres 2020-2030" in bledy
    assert len(bledy) == 2


def test_raport_poprawny(app):
    assert raport(app, rok="2027", region="PL", uwagi="Test").errors == {}


def test_raport_rok_zero_jest_liczba_a_nie_brakiem(app):
    # InputRequired (nie DataRequired): 0 to wartosc, odrzucona dopiero przez zakres
    assert raport(app, rok="0", region="PL").errors == {"rok": ["Zakres 2020-2030"]}


def test_raport_wymaga_roku(app):
    assert "Pole jest wymagane" in raport(app, rok="", region="PL").errors["rok"]


def test_raport_region_spoza_wykazu(app):
    assert raport(app, rok="2027", region="XX").errors == {"region": ["Nieprawidłowy wybór"]}


def test_raport_uwagi_najwyzej_200_znakow(app):
    assert raport(app, rok="2027", region="PL", uwagi="x" * 201).errors == {"uwagi": ["Najwyżej 200 znaków"]}
    assert raport(app, rok="2027", region="PL", uwagi="x" * 200).errors == {}


def test_raport_walidator_wlasny_odrzuca_powtorzona_pare(app):
    f = raport(app, istniejace={(2027, "PL")}, rok="2027", region="PL")
    assert f.errors == {"rok": ["Raport za ten rok i region już istnieje"]}


def test_raport_ten_sam_rok_inny_region_jest_dozwolony(app):
    assert raport(app, istniejace={(2027, "PL")}, rok="2027", region="DE").errors == {}
