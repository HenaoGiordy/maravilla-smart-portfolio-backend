# Maravilla Smart Portfolio - Backend

Backend en Python para consumir Twelve Data y exponer endpoints listos para integrar con otros servicios.

## Stack

- Python 3.11+
- FastAPI
- httpx
- uvicorn

## Estructura de carpetas

```text
app/
	application/
		use_cases/
	config/
	domain/
		entities/
		ports/
	infrastructure/
		external/
	interfaces/
		http/
			routes/
docs/
	postman/
```

## Configuración

1. Crea tu entorno virtual e instala dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Crea `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

3. Ajusta tu API key de Twelve Data en `.env`:

```env
TWELVE_DATA_API_KEY=tu_api_key
```

## Ejecutar local

```bash
uvicorn app.main:app --reload
```

Base local: `http://127.0.0.1:8000`

## Endpoints disponibles

- `GET /health`
- `GET /api/v1/market-data/price?symbol=AAPL`
- `GET /api/v1/market-data/quote?symbol=AAPL`
- `GET /api/v1/market-data/time-series?symbol=AAPL&interval=1day&outputsize=30`

## Documentación de consumos

- Guía de consumos: `docs/twelvedata-consumos.md`
- Colección Postman: `docs/postman/TwelveData.postman_collection.json`
