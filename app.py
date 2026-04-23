from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app, origins=["*"])

CAMMESA_BASE = "https://api.cammesa.com/demanda-svc/demanda"
RENOVABLES_BASE = "https://cdsrenovables.cammesa.com/exhisto/RenovablesService"
HEADERS = {"User-Agent": "ArgentinaEnergia/1.0", "Accept": "application/json"}

def fetch(url, params=None, timeout=12):
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

def fetch_region(rid, name):
    try:
        d = fetch(f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": rid})
        ul = next((p for p in reversed(d) if p.get("demHoy")), None)
        if ul:
            return {
                "id": rid, "nombre": name,
                "demHoy": ul["demHoy"],
                "demAyer": ul.get("demAyer"),
                "fecha": ul["fecha"]
            }
    except:
        pass
    return None

@app.route("/api/estado")
def estado():
    hoy = date.today().strftime("%d-%m-%Y")

    # Fetch demanda + renovables in parallel with regions
    REGIONS = {426:"GBA", 425:"Buenos Aires", 417:"Litoral",
                422:"Centro", 419:"NOA", 418:"NEA",
                420:"Comahue", 429:"Cuyo", 111:"Patagonia"}

    demanda, renovables = [], []

    with ThreadPoolExecutor(max_workers=12) as ex:
        # Main SADI demand
        f_dem = ex.submit(fetch, f"{CAMMESA_BASE}/ObtieneDemandaYTemperaturaRegion", {"id_region": 1002})
        # Renovables
        f_ren = ex.submit(fetch,
            f"{RENOVABLES_BASE}/GetChartTotalTRDataSourceNew",
            {"desde": hoy, "hasta": hoy})
        # All regions in parallel
        region_futures = {
            ex.submit(fetch_region, rid, name): rid
            for rid, name in REGIONS.items()
        }

        try:
            demanda = f_dem.result(timeout=15)
        except Exception as e:
            return jsonify({"error": f"CAMMESA demanda: {e}"}), 502

        try:
            raw = f_ren.result(timeout=15)
            renovables = sorted(raw, key=lambda x: x["momento"])
        except:
            renovables = []

        regiones = []
        for f in as_completed(region_futures, timeout=15):
            result = f.result()
            if result:
                regiones.append(result)

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
