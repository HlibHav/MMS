-- Database schema for Promo Scenario Co-Pilot (PostgreSQL dialect)

-- Sales aggregated table
CREATE TABLE IF NOT EXISTS sales_aggregated (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('online','offline')),
    department VARCHAR(50) NOT NULL,
    promo_flag BOOLEAN DEFAULT FALSE,
    discount_pct NUMERIC(5,2),
    sales_value NUMERIC(15,2) NOT NULL,
    margin_value NUMERIC(15,2) NOT NULL,
    margin_pct NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE WHEN sales_value > 0 THEN (margin_value / sales_value * 100) ELSE 0 END
    ) STORED,
    units INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_sales_record UNIQUE (date, channel, department, promo_flag)
);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_aggregated(date);
CREATE INDEX IF NOT EXISTS idx_sales_channel ON sales_aggregated(channel);
CREATE INDEX IF NOT EXISTS idx_sales_department ON sales_aggregated(department);
CREATE INDEX IF NOT EXISTS idx_sales_promo ON sales_aggregated(promo_flag);

-- Promo scenarios
CREATE TABLE IF NOT EXISTS promo_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(100) NOT NULL,
    source_opportunity_id UUID,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    scenario_type VARCHAR(50),
    mechanics JSONB NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (date_range_end >= date_range_start)
);
CREATE INDEX IF NOT EXISTS idx_scenarios_date_range ON promo_scenarios(date_range_start, date_range_end);
CREATE INDEX IF NOT EXISTS idx_scenarios_type ON promo_scenarios(scenario_type);

-- Scenario KPIs
CREATE TABLE IF NOT EXISTS scenario_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES promo_scenarios(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_sales_value NUMERIC(15,2) NOT NULL,
    total_margin_value NUMERIC(15,2) NOT NULL,
    total_margin_pct NUMERIC(5,2) NOT NULL,
    total_ebit NUMERIC(15,2) NOT NULL,
    total_units INTEGER NOT NULL,
    sales_value_delta NUMERIC(15,2) NOT NULL,
    margin_value_delta NUMERIC(15,2) NOT NULL,
    ebit_delta NUMERIC(15,2) NOT NULL,
    units_delta INTEGER NOT NULL,
    kpi_breakdown JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (period_end >= period_start)
);
CREATE INDEX IF NOT EXISTS idx_kpis_scenario ON scenario_kpis(scenario_id);
CREATE INDEX IF NOT EXISTS idx_kpis_period ON scenario_kpis(period_start, period_end);

-- Validation reports
CREATE TABLE IF NOT EXISTS validation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES promo_scenarios(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PASS','WARN','BLOCK')),
    issues JSONB,
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (scenario_id)
);
CREATE INDEX IF NOT EXISTS idx_validation_status ON validation_reports(status);

-- Post-mortem reports
CREATE TABLE IF NOT EXISTS post_mortem_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES promo_scenarios(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    forecast_kpi_id UUID REFERENCES scenario_kpis(id),
    actual_kpi JSONB NOT NULL,
    vs_forecast JSONB,
    post_promo_dip JSONB,
    cannibalization_signals JSONB,
    insights TEXT[],
    learning_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (period_end >= period_start)
);
CREATE INDEX IF NOT EXISTS idx_postmortem_scenario ON post_mortem_reports(scenario_id);
CREATE INDEX IF NOT EXISTS idx_postmortem_period ON post_mortem_reports(period_start, period_end);

-- Creative briefs
CREATE TABLE IF NOT EXISTS creative_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES promo_scenarios(id) ON DELETE CASCADE,
    brief JSONB NOT NULL,
    assets JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_creative_scenario ON creative_briefs(scenario_id);

-- Segments
CREATE TABLE IF NOT EXISTS segments (
    segment_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    share_of_customers NUMERIC(5,4) NOT NULL CHECK (share_of_customers >= 0 AND share_of_customers <= 1),
    share_of_revenue NUMERIC(5,4) NOT NULL CHECK (share_of_revenue >= 0 AND share_of_revenue <= 1),
    avg_basket_value NUMERIC(10,2) NOT NULL,
    fav_categories TEXT[],
    discount_sensitivity VARCHAR(20) CHECK (discount_sensitivity IN ('low','medium','high')),
    purchase_frequency NUMERIC(5,2),
    last_purchase_days_ago INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Uplift coefficients
CREATE TABLE IF NOT EXISTS uplift_coefficients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('online','offline')),
    discount_band VARCHAR(20) NOT NULL,
    uplift_sales_pct NUMERIC(6,2) NOT NULL,
    uplift_units_pct NUMERIC(6,2) NOT NULL,
    margin_impact_pct NUMERIC(6,2) NOT NULL,
    confidence NUMERIC(3,2),
    sample_size INTEGER,
    model_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (department, channel, discount_band, model_version)
);
CREATE INDEX IF NOT EXISTS idx_uplift_department ON uplift_coefficients(department);
CREATE INDEX IF NOT EXISTS idx_uplift_channel ON uplift_coefficients(channel);
CREATE INDEX IF NOT EXISTS idx_uplift_version ON uplift_coefficients(model_version);

-- Targets
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    month VARCHAR(7) NOT NULL,
    geo VARCHAR(10) NOT NULL,
    sales_value_target NUMERIC(15,2) NOT NULL,
    margin_pct_target NUMERIC(5,2) NOT NULL,
    units_target INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (month, geo)
);
CREATE INDEX IF NOT EXISTS idx_targets_month ON targets(month);
CREATE INDEX IF NOT EXISTS idx_targets_geo ON targets(geo);

-- Promo catalog
CREATE TABLE IF NOT EXISTS promo_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promo_name VARCHAR(200),
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    departments TEXT[],
    channels TEXT[],
    avg_discount_pct NUMERIC(5,2),
    mechanics JSONB,
    source_file VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (date_end >= date_start)
);
CREATE INDEX IF NOT EXISTS idx_promo_dates ON promo_catalog(date_start, date_end);
CREATE INDEX IF NOT EXISTS idx_promo_departments ON promo_catalog USING GIN(departments);
CREATE INDEX IF NOT EXISTS idx_promo_source_file ON promo_catalog(source_file);

-- Data processing jobs
CREATE TABLE IF NOT EXISTS data_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('queued','processing','completed','failed')),
    files_queued INTEGER NOT NULL,
    files_processed INTEGER DEFAULT 0,
    records_processed BIGINT DEFAULT 0,
    errors INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON data_processing_jobs(status);

-- API keys (for JWT/bootstrap)
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);

