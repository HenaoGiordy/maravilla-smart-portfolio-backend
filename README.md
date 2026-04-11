# Maravilla Smart Portfolio - Backend

Backend en FastAPI para gestión de portafolios multiusuario, holdings, métricas de desempeño e integración con Twelve Data.

## Stack

- Python 3.13 (compatible con 3.11+)
- FastAPI + Uvicorn
- SQLAlchemy Async + PostgreSQL
- Redis (caché)
- Twelve Data API

## Arquitectura

```text
app/
	application/use_cases/
	config/
	domain/
		entities/
		ports/
		schemas.py
	infrastructure/
		external/
		cache.py
		database.py
		repositories.py
	interfaces/http/routes/
docs/
	postman/
```

## Variables de entorno

1) Copia archivo base:

```bash
cp .env.example .env
```

2) Ajusta al menos estas variables en `.env`:

```env
TWELVE_DATA_API_KEY=tu_api_key
DATABASE_URL=postgresql+asyncpg://root:root@localhost:5432/maravilla_db
REDIS_URL=redis://localhost:6379/0
```

> Si usas tus propios contenedores/credenciales, cambia `DATABASE_URL` y `REDIS_URL`.

## Levantar servicio local (paso a paso)

### 1) Entorno Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Levantar PostgreSQL y Redis

```bash
docker compose up -d
```

Si los puertos `5432` o `6379` ya están ocupados, usa servicios existentes y ajusta `.env`.

### 3) Crear esquema de base de datos

```bash
python apply_migrations.py
```

### 4) Iniciar API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

API base local: `http://127.0.0.1:8001`

## Bootstrap rápido (un solo flujo)

```bash
source .venv/bin/activate \
	&& pip install -r requirements.txt \
	&& docker compose up -d \
	&& python apply_migrations.py \
	&& uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## ¿Dónde ver los endpoints?

- Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`
- OpenAPI JSON: `http://127.0.0.1:8001/openapi.json`

## Endpoints backend disponibles

### Salud
- `GET /health`

### Mercado (Twelve Data + caché Redis)
- `GET /api/v1/market-data/price?symbol=AAPL`
- `GET /api/v1/market-data/quote?symbol=AAPL`
- `GET /api/v1/market-data/time-series?symbol=AAPL&interval=1day&outputsize=30`

### Portafolios
- `POST /api/v1/portfolios?profile_id={id}`
- `GET /api/v1/portfolios?profile_id={id}`
- `GET /api/v1/portfolios/{portfolio_id}`
- `PUT /api/v1/portfolios/{portfolio_id}`
- `DELETE /api/v1/portfolios/{portfolio_id}`

### Holdings
- `POST /api/v1/holdings?portfolio_id={id}`
- `GET /api/v1/holdings?portfolio_id={id}`
- `GET /api/v1/holdings/{holding_id}`
- `PUT /api/v1/holdings/{holding_id}`
- `DELETE /api/v1/holdings/{holding_id}`

### Performance
- `GET /api/v1/performance/{portfolio_id}`
- `GET /api/v1/performance/{portfolio_id}/holdings`

## Relación con el marco teórico de perfiles

El backend soporta la clasificación de perfil de inversionista en `investment_profiles`, con campos:

- `name`: nombre de perfil (ej. Conservador, Moderado, Agresivo)
- `risk_level`: nivel de riesgo (`low`, `medium`, `high`)
- `volatility_target`: tolerancia al riesgo
- `expected_return`: expectativa de rentabilidad

Mapeo sugerido según teoría:

- Conservador: baja rentabilidad esperada, foco en preservación de capital, horizonte corto.
- Moderado: equilibrio riesgo-retorno, horizonte corto/medio.
- Agresivo: alta volatilidad tolerada, crecimiento de capital, horizonte largo.

En holdings, los campos `asset_class` e `income_type` permiten reflejar tipos de inversión:

- Renta fija: bonos, CDT, TES (`asset_class`/`income_type` orientados a instrumentos de deuda e interés).
- Renta variable: acciones y activos volátiles (`asset_class` orientado a renta variable).

## ¿Está cumpliendo integración con frontend?

En este workspace, el frontend actual (`src/App.tsx`) está en modo base y no realiza llamadas HTTP todavía. Eso significa:

- El backend ya expone contrato listo para integración (`/api/v1/...`).
- La integración efectiva front↔back no está implementada en este código frontend actual.

Para validar integración cuando conectes el front:

1. Configura `VITE_API_BASE_URL=http://127.0.0.1:8001`.
2. Desde el front, consume los endpoints de `portfolios`, `holdings` y `performance`.
3. Verifica en Network del navegador respuestas `200/201` y payload esperado.
4. Revisa en `/docs` que el request/response coincide con lo que renderiza el front.

## Notas técnicas

- La caché en Redis se usa para precios/quotes/time-series (TTL configurable).
- El cálculo de performance invalida caché cuando cambian holdings o portafolios.
- CORS está abierto (`allow_origins=["*"]`) para desarrollo; restringir en producción.

## Recursos

- Guía de consumos Twelve Data: `docs/twelvedata-consumos.md`
- Colección Postman: `docs/postman/TwelveData.postman_collection.json`
