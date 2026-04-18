from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, date

app = Flask(__name__)

# Permite requests solo desde tu dominio en produccion
# En desarrollo acepta todo
CORS(app, origins=["*"])

CAMMESA_BASE = "https://api.cammesa.com/demanda-svc/demanda"
RENOVABLES_BASE = "https://cdsrenovables.cammesa.com/exhisto/RenovablesService"

HEADERS = {
    "User-Agent": "ArgentinaEnergia/1.0",
    "Accept": "application/json",
}

def fetch(url, params=None, timeout=10):
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

@app.route("/api/demanda")
def demanda():
    """Demanda y temperatura del SADI completo en tiempo real"""
    data = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": 1002})
    return jsonify(data)

@app.route("/api/regiones")
def regiones():
    """Lista de regiones con sus IDs"""
    data = fetch(f"{CAMMESA_BASE}/RegionesDemanda")
    return jsonify(data)

@app.route("/api/demanda/<int:region_id>")
def demanda_region(region_id):
    """Demanda de una región específica"""
    data = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": region_id})
    return jsonify(data)

@app.route("/api/renovables")
def renovables():
    """Mix de generación renovable del día actual"""
    hoy = date.today().strftime("%d-%m-%Y")
    data = fetch(
        f"{RENOVABLES_BASE}/GetChartTotalTRDataSourceNew",
        {"desde": hoy, "hasta": hoy}
    )
    # Ordenar por momento
    data_sorted = sorted(data, key=lambda x: x["momento"])
    return jsonify(data_sorted)

@app.route("/api/totales")
def totales():
    """Totales de renovables"""
    data = fetch(f"{RENOVABLES_BASE}/GetTotales")
    return jsonify(data)

@app.route("/api/estado")
def estado():
    """Endpoint combinado: todo lo necesario para el dashboard en 1 request"""
    hoy = date.today().strftime("%d-%m-%Y")

    try:
        demanda = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": 1002})
    except Exception as e:
        return jsonify({"error": f"CAMMESA demanda: {str(e)}"}), 502

    try:
        renovables = fetch(
            f"{RENOVABLES_BASE}/GetChartTotalTRDataSourceNew",
            {"desde": hoy, "hasta": hoy}
        )
        renovables = sorted(renovables, key=lambda x: x["momento"])
    except Exception as e:
        renovables = []

    # IDs de regiones principales
    region_ids = [426, 425, 417, 422, 419, 418, 420, 111]
    region_names = {426:"GBA", 425:"Buenos Aires", 417:"Litoral",
                    422:"Centro", 419:"NOA", 418:"NEA", 420:"Comahue", 111:"Patagonia"}
    regiones = []
    for rid in region_ids:
        try:
            d = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": rid})
            ultimo = next((p for p in reversed(d) if p.get("demHoy")), None)
            if ultimo:
                regiones.append({
                    "id": rid,
                    "nombre": region_names.get(rid, str(rid)),
                    "demHoy": ultimo["demHoy"],
                    "fecha": ultimo["fecha"]
                })
        except:
            pass

    return jsonify({
        "demanda": demanda,
        "renovables": renovables,
        "regiones": regiones,
        "generado": datetime.now().isoformat()
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
