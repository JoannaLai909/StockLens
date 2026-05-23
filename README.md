# StockLens

A Taiwan stock analysis system that fetches price data via ETL, computes quantitative factors, and visualizes results in a dashboard.

## Project Structure

```
StockLens/
├── schema.sql        # PostgreSQL schema (tables + views)
├── stock_list.py     # Stock list with industry categories
├── etl.py            # FinMind ETL: fetch, clean, and load price data
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── .gitignore
```

## Team

| Branch | Member | Responsibility |
|--------|--------|----------------|
| `feature/member-a-etl` | Member A | Data engineering: schema, ETL, stock list |
| `feature/member-b-factors` | Member B | Factor calculation: returns, volatility, health score, K-means clustering |
| `feature/member-c-dashboard` | Member C | Dashboard: data visualization |

---

## Getting Started

### 1. Clone and install dependencies

```bash
git clone https://github.com/JoannaLai909/StockLens.git
cd StockLens
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values. `DB_PASSWORD` should match the password you set when starting PostgreSQL (see step 3). `FINMIND_TOKEN` is optional — the free tier works without it. Get a token at [finmindtrade.com](https://finmindtrade.com) if you hit rate limits.

### 3. Start PostgreSQL

```bash
docker run -d \
  --name stockdb \
  -e POSTGRES_PASSWORD=your_password_here \
  -e POSTGRES_DB=stockdb \
  -p 5432:5432 \
  postgres:15
```

Use the same password in your `.env` file.

### 4. Initialize the database

```bash
python etl.py --init-db
```

### 5. Run the ETL

```bash
# fetch all stocks, last 90 days
python etl.py

# last 180 days
python etl.py --days 180

# single stock only (for testing)
python etl.py --stock 2330
```

---

## Database Tables

| Table | Description |
|-------|-------------|
| `stocks` | Stock metadata (ticker, name, industry) |
| `daily_prices` | Daily OHLCV data (written by Member A ETL) |
| `factor_scores` | Quantitative factors (written by Member B) |

### Views (for Member C's Dashboard)

| View | Description |
|------|-------------|
| `v_latest_factors` | Latest factors for all stocks |
| `v_top10_return_20d` | Top 10 stocks by 20-day return |
| `v_industry_avg` | Average factor performance by industry |

---

## Development Workflow

Each member works on their own branch and opens a PR to merge into `main` when done.

```bash
# switch to your branch
git checkout feature/member-b-factors

# push your changes
git push origin feature/member-b-factors

# then open a Pull Request on GitHub -> main
```
