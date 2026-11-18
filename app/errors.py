from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException


def zarejestruj_obsluge_bledow(app):
    @app.errorhandler(HTTPException)
    def obsluga_bledu(blad):
        if request.path.startswith("/api"):
            return jsonify(blad=blad.description, kod=blad.code), blad.code
        # opis moze zawierac wartosc z adresu: escapowanie automatyczne szablonu czyni ja bezpieczna
        return render_template("errors/error.html", kod=blad.code, opis=blad.description), blad.code
