# Promo Scenario Co-Pilot

AI-powered promotional campaign planning and optimization system for retail businesses.

## 🎯 Overview

Promo Scenario Co-Pilot is an intelligent assistant that helps promotional leads quickly close gaps vs targets by:
- Discovering promotional opportunities through data analysis
- Modeling and comparing multiple campaign scenarios
- Optimizing scenarios for maximum business impact
- Generating creative briefs and assets
- Learning from post-campaign performance

## 🏗️ Architecture

The system follows a multi-agent architecture with specialized engines and tools:

- **Agents**: LLM-powered orchestrators for different workflow stages
- **Engines**: Business logic and computation modules
- **Tools**: Data access and external API integrations
- **UI**: Modern React interface with chat-based co-pilot

## 🚀 Tech Stack

- **Backend**: Python (LangChain, FastAPI)
- **Frontend**: React (TypeScript), Tailwind CSS
- **Observability**: Phoenix Arize
- **Runtime**: Node.js (for frontend tooling)
- **UI Components**: [ReactBits.dev](http://reactbits.dev/)

## 📋 Key Features

### 1. Promo Briefing Agent
Converts natural language prompts into structured promotional briefs with targets, constraints, and objectives.

### 2. Data & Baseline Forecast Agent
Builds baseline forecasts from historical data, identifying gaps vs targets by department and channel.

### 3. Scenario Lab
Generates and compares 2-3 promotional scenarios (Conservative, Balanced, Aggressive) with detailed KPI projections.

### 4. Optimization Engine
Finds optimal scenarios balancing sales targets, margin constraints, and EBIT goals.

### 5. Creative Companion
Generates structured creative briefs and asset specifications from selected scenarios.

### 6. Post-Mortem Analytics
Analyzes actual vs forecasted performance and updates uplift models.

## 📁 Project Structure

```
MMS/
├── docs/                    # Documentation
│   ├── architecture.md     # System architecture
│   ├── api/                 # API documentation
│   ├── data-models.md       # Data schemas
│   └── ui-specs.md          # UI/UX specifications
├── backend/                 # Python backend
│   ├── agents/              # LangChain agents
│   ├── engines/             # Business logic engines
│   ├── tools/               # Data access tools
│   │   ├── xlsb_reader.py  # XLSB file reader
│   │   ├── data_cleaner.py  # Data cleaning
│   │   ├── promo_processor.py  # Promo catalog processor
│   │   └── ...              # Other tools
│   ├── models/              # Data models
│   └── api/                 # FastAPI endpoints
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── screens/         # Main screens
│   │   ├── services/        # API clients
│   │   └── hooks/           # React hooks
│   └── public/
└── Data/                    # Data files
    ├── Web_*.xlsb           # Web sales data
    ├── Stores_*.xlsb        # Store sales data
    └── Promo_*.xlsb         # Promotional catalog data
```

## 🛠️ Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or DuckDB for local dev)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd MMS

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment setup
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

```bash
# Terminal 1: Backend
cd backend
uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

## 📚 Documentation

### Core Documentation
- [Architecture Documentation](./docs/architecture.md) - System architecture and design
- [API Specification](./docs/API_SPECIFICATION.md) - Complete API reference
- [Database Schema](./docs/DATABASE_SCHEMA.md) - Database structure and schema
- [Product Requirements Document](./docs/PRD.md) - Product requirements and specifications
- [System Prompts](./docs/system-prompts.md) - LLM agent system prompts

### Technical Documentation
- [API Reference](./docs/api/README.md) - API endpoints and usage
- [Data Models](./docs/data-models.md) - Data structures and schemas
- [UI Specifications](./docs/ui-specs.md) - UI/UX specifications
- [Development Guide](./docs/development.md) - Development workflow
- [Setup Guide](./docs/setup.md) - Installation and setup
- [Hackathon Plan](./docs/hackathon-plan.md) - 14-hour build plan

### Documentation Index
- [Documentation Summary](./docs/SUMMARY.md) - Complete documentation index

## 🔧 Configuration

Key environment variables:

- `OPENAI_API_KEY`: For LLM agents
- `PHOENIX_API_KEY`: For observability
- `DATABASE_URL`: Database connection string
- `CDP_API_URL`: Customer data platform endpoint (optional)
- Note: Open-Meteo API is used for weather (free, no API key required)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Observability

The system uses Phoenix Arize for:
- LLM call tracing and monitoring
- Agent performance metrics
- Scenario evaluation tracking
- Error and latency monitoring

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

[Specify license]

## 🎯 Roadmap

- [ ] MVP implementation (hackathon scope)
- [ ] Production data pipeline integration
- [ ] Advanced ML models for uplift prediction
- [ ] Real-time scenario optimization
- [ ] Multi-tenant support
- [ ] Advanced creative generation with images

