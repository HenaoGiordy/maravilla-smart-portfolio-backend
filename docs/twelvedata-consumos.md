# Consumos Twelve Data (Backend)

Este documento resume los consumos habilitados actualmente desde el backend.

## Base URL externa

`https://api.twelvedata.com`

## Endpoints de backend expuestos

Base local: `http://127.0.0.1:8000/api/v1/market-data`

### 1) Precio puntual

- Endpoint backend: `GET /price`
- Query params:
  - `symbol` (requerido), ejemplo: `AAPL`
- Consumo Twelve Data:
  - `GET /price?symbol={symbol}&apikey={api_key}`

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/v1/market-data/price?symbol=AAPL"
```

Respuesta esperada:

```json
{
  "symbol": "AAPL",
  "price": 198.42
}
```

### 2) Quote completo

- Endpoint backend: `GET /quote`
- Query params:
  - `symbol` (requerido)
- Consumo Twelve Data:
  - `GET /quote?symbol={symbol}&apikey={api_key}`

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/v1/market-data/quote?symbol=AAPL"
```

Respuesta (campos principales):

```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "currency": "USD",
  "open": 197.12,
  "high": 199.01,
  "low": 196.75,
  "close": 198.42,
  "volume": 41234567,
  "change": 1.3,
  "percent_change": 0.66
}
```

### 3) Serie de tiempo (OHLCV)

- Endpoint backend: `GET /time-series`
- Query params:
  - `symbol` (requerido)
  - `interval` (opcional, default `1day`)
  - `outputsize` (opcional, default `30`, min `1`, max `5000`)
- Consumo Twelve Data:
  - `GET /time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={api_key}`

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/v1/market-data/time-series?symbol=AAPL&interval=1day&outputsize=5"
```

Respuesta esperada:

```json
{
  "meta": {
    "symbol": "AAPL",
    "interval": "1day",
    "currency": "USD"
  },
  "values": [
    {
      "datetime": "2026-04-08",
      "open": "197.12",
      "high": "199.01",
      "low": "196.75",
      "close": "198.42",
      "volume": "41234567"
    }
  ]
}
```

## Manejo de errores

- Si Twelve Data responde `status=error`, el backend devuelve `400` con `detail`.
- Si Twelve Data no está disponible (timeout/red), el backend devuelve `503`.
- Si hay error HTTP upstream, el backend propaga el código HTTP recibido.
