# Backend Project Structure

This document describes the structure of the backend codebase with all modules and their purposes.

## Directory Structure

```
backend/
├── __init__.py                 # Backend package initialization
├── PROJECT_STRUCTURE.md        # This file
├── requirements.txt            # Python dependencies
│
├── agents/                     # LangChain-powered orchestrators
│   ├── __init__.py
│   ├── discovery_agent.py      # Discovery & context analysis
│   ├── scenario_lab_agent.py   # Scenario modeling & comparison
│   ├── optimization_agent.py   # Scenario optimization
│   ├── creative_agent.py       # Creative brief & asset generation
│   ├── post_mortem_agent.py    # Performance analysis & learning
│   ├── validation_agent.py     # Quality & risk control
│   ├── data_analyst_agent.py   # Data processing & ETL
│   └── co_pilot_agent.py       # Conversational interface
│
├── engines/                    # Business logic and computation
│   ├── __init__.py
│   ├── context_engine.py       # Build promotional context
│   ├── forecast_baseline_engine.py  # Calculate baseline forecasts
│   ├── uplift_elasticity_engine.py  # Estimate promotional uplift
│   ├── scenario_evaluation_engine.py # Calculate scenario KPIs
│   ├── scenario_optimization_engine.py # Optimize scenarios
│   ├── validation_engine.py    # Validate scenarios
│   ├── creative_engine.py      # Generate creative briefs
│   ├── post_mortem_analytics_engine.py # Analyze performance
│   └── learning_engine.py      # Update models from post-mortems
│
├── tools/                      # Data access and external integrations
│   ├── __init__.py
│   ├── sales_data_tool.py      # Historical sales data access
│   ├── promo_catalog_tool.py   # Historical promotional campaigns
│   ├── cdp_tool.py             # Customer data platform (mock)
│   ├── context_data_tool.py    # Events, holidays, seasonality
│   ├── weather_tool.py         # Weather forecast (Open-Meteo)
│   ├── targets_config_tool.py  # Business targets & configuration
│   ├── xlsb_reader.py          # XLSB file reading
│   ├── data_cleaner.py         # Data cleaning & standardization
│   ├── data_merger.py          # Merge multiple data files
│   ├── data_validator.py       # Data quality validation
│   └── db_loader.py            # Database loading
│
├── models/                     # Data models and schemas
│   ├── __init__.py
│   └── schemas.py              # Pydantic models for validation
│
└── api/                        # FastAPI endpoints
    ├── __init__.py
    ├── main.py                 # FastAPI app initialization
    └── routes/                 # API route handlers
        ├── __init__.py
        ├── discovery.py        # Discovery endpoints
        ├── scenarios.py        # Scenario Lab endpoints
        ├── optimization.py     # Optimization endpoints
        ├── creative.py         # Creative endpoints
        └── data.py             # Data processing endpoints
```

## Module Overview

### Agents (`agents/`)

Agents are LangChain-powered orchestrators that coordinate multiple tools and engines to accomplish complex tasks. Each agent has a specific purpose and set of responsibilities:

1. **DiscoveryAgent**: Analyzes situations, gathers context, identifies opportunities
2. **ScenarioLabAgent**: Creates, evaluates, and compares promotional scenarios
3. **OptimizationAgent**: Finds optimal scenarios for maximum business impact
4. **CreativeAgent**: Generates creative briefs and campaign assets
5. **PostMortemAgent**: Analyzes performance and learns from results
6. **ValidationAgent**: Validates scenarios and ensures compliance
7. **DataAnalystAgent**: Processes, cleans, and loads data
8. **CoPilotAgent**: Provides conversational interface and explanations

### Engines (`engines/`)

Engines contain the core business logic and computational algorithms. They are stateless and can be reused across different agents:

1. **ContextEngine**: Builds comprehensive promotional context
2. **ForecastBaselineEngine**: Calculates baseline forecasts
3. **UpliftElasticityEngine**: Estimates promotional uplift
4. **ScenarioEvaluationEngine**: Calculates KPIs for scenarios
5. **ScenarioOptimizationEngine**: Optimizes scenarios
6. **ValidationEngine**: Validates scenarios against rules
7. **CreativeEngine**: Generates creative briefs and copy
8. **PostMortemAnalyticsEngine**: Analyzes actual vs forecasted performance
9. **LearningEngine**: Updates models from post-mortems

### Tools (`tools/`)

Tools provide data access and external API integrations. They abstract away the details of data sources:

1. **SalesDataTool**: Historical sales data from database
2. **PromoCatalogTool**: Historical promotional campaigns
3. **CDPTool**: Customer data platform integration (mock for MVP)
4. **ContextDataTool**: Events, holidays, seasonality data
5. **WeatherTool**: Weather forecasts (Open-Meteo API)
6. **TargetsConfigTool**: Business targets and configuration
7. **Data Processing Tools**: XLSB reading, cleaning, validation, loading

### Models (`models/`)

Models define the data structures used throughout the application using Pydantic:

- Core domain models: `PromoScenario`, `PromoContext`, `ScenarioKPI`, etc.
- Supporting models: `Event`, `Segment`, `Targets`, `Constraints`, etc.
- All models are defined in `schemas.py` with validation

### API (`api/`)

FastAPI application with organized route handlers:

- `main.py`: Application setup and configuration
- `routes/`: Feature-based route handlers
  - `discovery.py`: Discovery endpoints
  - `scenarios.py`: Scenario Lab endpoints
  - `optimization.py`: Optimization endpoints
  - `creative.py`: Creative endpoints
  - `data.py`: Data processing endpoints

## Implementation Status

All modules are currently placeholders with:
- ✅ Complete class structures
- ✅ Method signatures
- ✅ Type hints
- ✅ Documentation strings
- ⏳ Implementation logic (TODO)

## Next Steps

1. Implement core data models in `models/schemas.py`
2. Implement tools, starting with database connections
3. Implement engines, starting with basic calculations
4. Implement agents, connecting tools and engines
5. Implement API routes, connecting to agents
6. Add tests for each module
7. Add configuration management
8. Add logging and observability

## Development Guidelines

- All modules use type hints
- All classes and methods have docstrings
- Use relative imports within the backend package
- Follow the architecture defined in `docs/architecture.md`
- Keep engines stateless and reusable
- Keep tools focused on single responsibilities


