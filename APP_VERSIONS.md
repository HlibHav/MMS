# App Versions & Configurations Guide

This document lists all the different ways you can run the Promo Scenario Co-Pilot application.

## 🚀 Quick Reference

| Version | Command | Backend Port | Frontend Port | Database | Use Case |
|---------|---------|-------------|---------------|----------|----------|
| **Dev (SQLite)** | `./scripts/run-dev.sh` | 8000 | 5173 | SQLite | Development |
| **Dev (DuckDB)** | `DATABASE_URL=duckdb:///tmp/mms_data.duckdb ./scripts/run-dev.sh` | 8000 | 5173 | DuckDB | Development with DuckDB |
| **Simple Dev** | `./run_app.sh` | 8000 | 5173 | Default | Quick start |
| **Production Preview** | `cd frontend && npm run preview` | 8000 | 5173 | Any | Preview optimized build |
| **Docker Compose** | `docker-compose up` | 8000 | 3000 | Configurable | Production-like |
| **Test Mode** | `cd backend && pytest` | N/A | N/A | Test DB | Run tests |
| **Demo Mode** | Seed data + run dev | 8000 | 5173 | DuckDB/SQLite | Demo with sample data |

---

## 1. Development Versions

### 1.1 Development Mode (SQLite) - **RECOMMENDED**
**Best for**: Daily development work

```bash
./scripts/run-dev.sh
```

**Features**:
- Auto-reload enabled for both backend and frontend
- Uses SQLite database (no locking issues)
- Database: `sqlite://.tmp/mms_data.db`
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

**Custom ports**:
```bash
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./scripts/run-dev.sh
```

### 1.2 Development Mode (DuckDB)
**Best for**: Testing DuckDB-specific features

```bash
DATABASE_URL=duckdb:///tmp/mms_data.duckdb ./scripts/run-dev.sh
```

**Features**:
- Same as SQLite version but uses DuckDB
- Better for analytics workloads
- Database: `duckdb:///tmp/mms_data.duckdb`

### 1.3 Simple Development Runner
**Best for**: Quick start without script dependencies

```bash
./run_app.sh
```

**Features**:
- Simpler script, fewer options
- Auto-installs frontend dependencies if needed
- Custom ports via environment variables:
  ```bash
  UVICORN_PORT=9000 VITE_PORT=3000 ./run_app.sh
  ```

### 1.4 Manual Development (Separate Terminals)
**Best for**: Full control over each service

**Terminal 1 - Backend**:
```bash
cd backend
source .venv/bin/activate  # or your venv
export PYTHONPATH="$(cd .. && pwd):${PYTHONPATH}"
export DATABASE_URL="sqlite:///tmp/mms_data.db"
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev -- --host --port 5173
```

---

## 2. Production Versions

### 2.1 Production Preview (Frontend Only)
**Best for**: Testing production-optimized frontend

```bash
cd frontend
npm run build        # Build production version
npm run preview      # Preview the build
```

**Features**:
- Minified and optimized JavaScript/CSS
- Production-ready performance
- Requires backend running separately
- Frontend: http://localhost:4173 (default Vite preview port)

**Custom port**:
```bash
npm run preview -- --port 5173
```

### 2.2 Docker Compose (Full Stack)
**Best for**: Production-like environment, deployment testing

```bash
docker-compose up
```

**Features**:
- Production builds for both services
- Backend: http://localhost:8000
- Frontend: http://localhost:3000 (nginx)
- Uses `backend/config.example.env` for configuration
- Database configurable via `DATABASE_URL` in env file

**Build and run**:
```bash
docker-compose build    # Build images
docker-compose up -d    # Run in background
docker-compose logs -f  # View logs
docker-compose down     # Stop
```

---

## 3. Database Configurations

The app supports multiple database backends:

### 3.1 SQLite (Default for Dev)
```bash
export DATABASE_URL="sqlite:///tmp/mms_data.db"
./scripts/run-dev.sh
```

**Pros**: Simple, no setup required, good for development
**Cons**: Not suitable for production, limited concurrency

### 3.2 DuckDB
```bash
export DATABASE_URL="duckdb:///tmp/mms_data.duckdb"
./scripts/run-dev.sh
```

**Pros**: Fast analytics, columnar storage, good for data analysis
**Cons**: File-based, locking issues in multi-process scenarios

### 3.3 PostgreSQL (Production)
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/promo_co_pilot"
./scripts/run-dev.sh
```

**Pros**: Production-ready, concurrent access, robust
**Cons**: Requires PostgreSQL installation

**Setup PostgreSQL**:
```bash
createdb promo_co_pilot
cd backend
alembic upgrade head  # Run migrations
```

---

## 4. Demo Mode (With Sample Data)

**Best for**: Demonstrations, testing with realistic data

### Step 1: Load Sample Data
```bash
# Option A: Load CSV sample data
cd backend
python data/seed.py

# Option B: Load custom Parquet data
python scripts/load_custom_sales.py
```

### Step 2: Run App
```bash
./scripts/run-dev.sh
```

**Features**:
- Pre-populated with sample sales data
- Deterministic API responses
- Ready for demo walkthrough
- See `docs/demo-script.md` for demo flow

---

## 5. Test Mode

**Best for**: Running automated tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=agents --cov=engines --cov=tools --cov-report=html

# Specific test file
pytest tests/test_smoke_demo.py

# Frontend tests
cd frontend
npm test
```

**Test Files Available**:
- `test_smoke_demo.py` - Smoke tests for demo flow
- `test_discovery_routes.py` - Discovery API tests
- `test_scenario_routes.py` - Scenario API tests
- `test_optimization_routes.py` - Optimization API tests
- `test_creative_routes.py` - Creative API tests
- `test_data_routes.py` - Data processing tests

---

## 6. Environment-Specific Configurations

### 6.1 Development Environment
```bash
export ENVIRONMENT=development
export DATABASE_URL=sqlite:///tmp/mms_data.db
export LOG_LEVEL=DEBUG
export CORS_ORIGINS=http://localhost:5173
```

**Features**:
- Auth bypassed (mock user)
- Debug logging enabled
- CORS allows localhost

### 6.2 Production Environment
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@host:5432/db
export LOG_LEVEL=INFO
export JWT_SECRET_KEY=your-secret-key
export CORS_ORIGINS=https://yourdomain.com
```

**Features**:
- Full authentication required
- Production logging
- Secure CORS settings

### 6.3 Staging Environment
```bash
export ENVIRONMENT=staging
export DATABASE_URL=postgresql://user:pass@staging-host:5432/db
export LOG_LEVEL=INFO
```

---

## 7. Feature-Specific Configurations

### 7.1 With Phoenix Observability
```bash
export PHOENIX_API_KEY=your-key
export PHOENIX_ENDPOINT=https://phoenix.yourdomain.com
export PHOENIX_PROJECT_NAME=promo-scenario-co-pilot
./scripts/run-dev.sh
```

**Features**:
- LLM call tracing
- Performance monitoring
- Error tracking

### 7.2 With Redis (Rate Limiting)
```bash
export REDIS_URL=redis://localhost:6379
./scripts/run-dev.sh
```

**Default**: Uses in-memory storage (`memory://`)

### 7.3 With Custom API Keys
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
./scripts/run-dev.sh
```

---

## 8. Custom Port Configurations

All scripts support custom ports:

```bash
# Dev script
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./scripts/run-dev.sh

# Simple script
UVICORN_PORT=9000 VITE_PORT=3000 ./run_app.sh

# Manual
uvicorn backend.api.main:app --port 9000
npm run dev -- --port 3000
```

---

## 9. Data Loading Versions

### 9.1 Fresh Start (No Data)
Just run the app - empty database, demo endpoints return mock data

### 9.2 With Sample CSV Data
```bash
python backend/data/seed.py
```

### 9.3 With Custom Parquet Data
```bash
export SALES_DATA_PATH=/path/to/data.parquet
python scripts/load_custom_sales.py
```

### 9.4 With XLSB Files
Use the API endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/data/process-xlsb \
  -F "files=@Web_September_FY25.xlsb" \
  -F "files=@Stores_September_FY25.xlsb"
```

---

## 10. Comparison Matrix

| Feature | Dev (SQLite) | Dev (DuckDB) | Production Preview | Docker Compose |
|---------|--------------|--------------|-------------------|----------------|
| Auto-reload | ✅ | ✅ | ❌ | ❌ |
| Database | SQLite | DuckDB | Any | Configurable |
| Performance | Good | Excellent | Excellent | Excellent |
| Setup Time | Fast | Fast | Medium | Slow |
| Production-like | ❌ | ❌ | ✅ (Frontend) | ✅ |
| Best For | Development | Analytics Dev | UI Testing | Deployment |

---

## 🎯 Recommended Workflows

### Daily Development
```bash
./scripts/run-dev.sh
```

### Demo Preparation
```bash
python backend/data/seed.py
./scripts/run-dev.sh
```

### Production Testing
```bash
docker-compose up
```

### Quick API Testing
```bash
cd backend
uvicorn backend.api.main:app --reload
# Use http://localhost:8000/docs for API testing
```

---

## 📝 Notes

- **Default ports**: Backend 8000, Frontend 5173
- **Database**: SQLite for dev (no setup), PostgreSQL for production
- **Auth**: Bypassed in development mode (`ENVIRONMENT=development`)
- **CORS**: Configured for localhost in dev, strict in production
- **Logging**: DEBUG in dev, INFO in production
- **Hot reload**: Enabled in dev mode, disabled in production builds

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :5173

# Kill process or use different port
BACKEND_PORT=9000 FRONTEND_PORT=3000 ./scripts/run-dev.sh
```

### Database Connection Issues
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test SQLite
sqlite3 .tmp/mms_data.db "SELECT 1;"

# Test PostgreSQL
psql $DATABASE_URL -c "SELECT 1;"
```

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

---

For more details, see:
- `docs/setup.md` - Setup guide
- `docs/development.md` - Development guide
- `docs/demo-script.md` - Demo walkthrough


