from flask import abort, request


def parametr_int(nazwa, minimum, maksimum):
    """Zwraca parametr zapytania jako liczbe z przedzialu; w razie bledu przerywa zadanie."""
    wartosc = request.args.get(nazwa)
    if wartosc is None:
        abort(400, description=f"Brak parametru {nazwa}")
    try:
        liczba = int(wartosc)
    except ValueError:
        abort(400, description=f"Parametr {nazwa} nie jest liczba")
    if not minimum <= liczba <= maksimum:
        abort(422, description=f"Parametr {nazwa} poza zakresem {minimum}-{maksimum}")
    return liczba
