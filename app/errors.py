from flask import jsonify, request
from werkzeug.exceptions import HTTPException


def zarejestruj_obsluge_bledow(app):
    @app.errorhandler(HTTPException)
    def obsluga_bledu(blad):
        if request.path.startswith("/api"):
            return jsonify(blad=blad.description, kod=blad.code), blad.code
        # opis nie trafia do HTML: moze zawierac wartosc z adresu, ktorej nie zweryfikowano
        return f"<h1>{blad.code}</h1><p>Żądanie nie mogło zostać zrealizowane</p>", blad.code
