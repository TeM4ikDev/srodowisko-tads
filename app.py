from flask import Flask, abort, jsonify, request

from services import dostepne_regiony, policz_wskazniki

SCIEZKA_DANYCH = "dane/zamowienia.csv"

app = Flask(__name__)


def wskazniki_z_zadania():
    """Sprawdza parametr region wzgledem wykazu i zwraca wskazniki z warstwy uslug."""
    region = request.args.get("region")
    if region is not None and region not in dostepne_regiony(SCIEZKA_DANYCH):
        abort(404, description=f"Nieznany region: {region}")
    return policz_wskazniki(SCIEZKA_DANYCH, region)


@app.get("/")
def index():
    return "Panel wskaźników"


@app.get("/kpi")
def kpi():
    w = wskazniki_z_zadania()
    return f"<h1>Wskaźniki: {w['region'] or 'wszystkie regiony'}</h1><p>Marża: {w['marza']:.2%}</p>"


@app.get("/api/kpi")
def api_kpi():
    return jsonify(wskazniki_z_zadania())
