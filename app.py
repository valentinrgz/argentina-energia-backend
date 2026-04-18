from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, date

app = Flask(__name__)
CORS(app, origins=["*"])

CAMMESA_BASE = "https://api.cammesa.com/demanda-svc/demanda"
RENOVABLES_BASE = "https://cdsrenovables.cammesa.com/exhisto/RenovablesService"
HEADERS = {"User-Agent": "ArgentinaEnergia/1.0", "Accept": "application/json"}

def fetch(url, params=None, timeout=10):
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

@app.route("/api/estado")
def estado():
    hoy = date.today().strftime("%d-%m-%Y")
    try:
        demanda = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": 1002})
    except Exception as e:
        return jsonify({"error": f"CAMMESA demanda: {str(e)}"}), 502

    try:
        renovables = sorted(
            fetch(f"{RENOVABLES_BASE}/GetChartTotalTRDataSourceNew", {"desde": hoy, "hasta": hoy}),
            key=lambda x: x["momento"]
        )
    except:
        renovables = []

    # Incluye Cuyo (429)
    region_ids   = [426, 425, 417, 422, 419, 418, 420, 429, 111]
    region_names = {426:"GBA", 425:"Buenos Aires", 417:"Litoral",
                    422:"Centro", 419:"NOA", 418:"NEA",
                    420:"Comahue", 429:"Cuyo", 111:"Patagonia"}
    regiones = []
    for rid in region_ids:
        try:
            d = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": rid})
            ul = next((p for p in reversed(d) if p.get("demHoy")), None)
            if ul:
                regiones.append({
                    "id": rid,
                    "nombre": region_names[rid],
                    "demHoy": ul["demHoy"],
                    "demAyer": ul.get("demAyer"),
                    "fecha": ul["fecha"]
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
