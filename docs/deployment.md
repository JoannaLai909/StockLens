# StockLens Deployment

## Recommended Cloud Layout

Use Vercel for the Next.js frontend, and host the FastAPI API, PostgreSQL database, and ETL job outside Vercel.

```text
Vercel Next.js frontend
  -> FastAPI API on Render / Railway / Fly.io / VPS
  -> PostgreSQL on Neon / Supabase / Railway
  -> Scheduled ETL job updates PostgreSQL
```

## Vercel Frontend

Import this repository into Vercel. The root `vercel.json` points Vercel at the `frontend` app.

If you prefer configuring it manually in the Vercel UI, set:

```text
Install Command: cd frontend && npm ci
Build Command: cd frontend && npm run build
Output Directory: frontend/.next
```

Set these Vercel environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-stocklens-api.example.com
API_INTERNAL_URL=https://your-stocklens-api.example.com
```

The frontend fetches API data with `cache: "no-store"`, so each page request asks the API for fresh data. The displayed data is as fresh as the latest successful ETL run in the database.

## FastAPI Backend

Deploy the `api` service to a Python-capable host. Use Python 3.12, then run:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set backend environment variables:

```env
DATABASE_URL=postgresql://stock_user:your_password_here@your-cloud-db-host:5432/stockdb
DB_HOST=your-cloud-db-host
DB_PORT=5432
DB_NAME=stockdb
DB_USER=stock_user
DB_PASSWORD=your_password_here
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

If `DATABASE_URL` is set, the API and ETL use it instead of the separate DB variables.

## PostgreSQL

Create a managed PostgreSQL database and apply:

```bash
psql "$DATABASE_URL" -f db/stock_schema.sql
```

## ETL Schedule

Run the ETL after market data is available. For Taiwan market data, a daily schedule after market close is usually enough.

The ETL job needs the same database variables as the API, plus `FINMIND_TOKEN` if you use one.

```env
DB_HOST=your-cloud-db-host
DB_PORT=5432
DB_NAME=stockdb
DB_USER=stock_user
DB_PASSWORD=your_password_here
FINMIND_TOKEN=
```

## Freshness Check

After deployment:

```text
https://your-api-domain/health
https://your-vercel-domain/health
```

The `/health` page shows whether stock prices, factors, and cluster data are current.
