-- Database schema for Promo Scenario Co-Pilot

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
    margin_pct NUMERIC(5,2),
    units INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_sales_record UNIQUE (date, channel, department, promo_flag)
);

-- Promo catalog table
CREATE TABLE IF NOT EXISTS promo_catalog (
    id BIGSERIAL PRIMARY KEY,
    promo_id VARCHAR(128),
    promo_name TEXT,
    date_start DATE,
    date_end DATE,
    departments TEXT[],
    channels TEXT[],
    avg_discount_pct NUMERIC(5,2),
    mechanics JSONB,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API keys (for JWT bootstrap)
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);

