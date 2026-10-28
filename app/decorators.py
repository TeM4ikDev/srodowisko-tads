from functools import wraps

from flask import abort, request


def wymagany_parametr(nazwa):
    """Odrzuca zadanie bez wskazanego parametru zapytania kodem 400."""

    def dekorator(widok):
        @wraps(widok)
        def opakowany(*args, **kwargs):
            if nazwa not in request.args:
                abort(400, description=f"Brak parametru {nazwa}")
            return widok(*args, **kwargs)

        return opakowany

    return dekorator
