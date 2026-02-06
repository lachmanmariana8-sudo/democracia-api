# Democrac.IA Backend API

FastAPI backend for the Democrac.IA electoral observation platform.

## Endpoints

- `GET /` - Health check
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/elections` - Active elections
- `GET /api/observations/latest` - Latest observations
- `GET /api/reports` - MOEP reports

## Deploy

```bash
pip install -r requirements.txt
uvicorn moe_api_server:app --host 0.0.0.0 --port 8000
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Server port (default: 8000)
