# ArgentinaEnergía — Backend

Proxy API que consume CAMMESA y sirve los datos al frontend.

## Endpoints

| Endpoint | Descripción |
|---|---|
| `GET /api/estado` | Todo el dashboard en 1 request (recomendado) |
| `GET /api/demanda` | Curva de demanda SADI del día |
| `GET /api/renovables` | Mix renovable del día |
| `GET /api/regiones` | Lista de regiones |
| `GET /api/demanda/{id}` | Demanda de una región específica |
| `GET /health` | Health check |

## Deploy en Railway (gratis)

1. Crear cuenta en railway.app
2. New Project → Deploy from GitHub repo
3. Subir estos archivos a un repo de GitHub
4. Railway detecta el Procfile y deploya solo
5. En Settings → Domains → Generate Domain
6. Copiar la URL generada (ej: argentina-energia-backend.up.railway.app)

## Deploy en Render (alternativa gratis)

1. Crear cuenta en render.com
2. New → Web Service → conectar repo GitHub
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Free tier → Create Web Service

## Uso local (para testear)

```bash
pip install -r requirements.txt
python app.py
# Servidor en http://localhost:5000
```

Probar: http://localhost:5000/api/demanda
