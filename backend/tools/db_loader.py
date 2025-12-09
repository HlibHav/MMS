"""
Database Loader Tool for Data Analyst Agent

Loads processed data into the database.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseLoaderTool:
    """Tool for loading data into database."""
    
    def __init__(self, database_url: str):
        """
        Initialize database loader.
        
        Args:
            database_url: Database connection string
                - PostgreSQL: postgresql://user:pass@host:port/db
                - DuckDB: duckdb:///path/to/db
        """
        self.database_url = database_url
        self.engine = None
        self._connect()
    
    def _connect(self):
        """Create database connection."""
        try:
            if self.database_url.startswith('duckdb://'):
                # DuckDB connection
                import duckdb
                db_path = self.database_url.replace('duckdb://', '')
                self.engine = duckdb.connect(db_path)
                logger.info(f"Connected to DuckDB: {db_path}")
            else:
                # PostgreSQL connection
                self.engine = create_engine(self.database_url)
                logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def create_table_if_not_exists(self, table_name: str = 'sales_aggregated'):
        """
        Create sales_aggregated table if it doesn't exist.
        
        Args:
            table_name: Name of the table
        """
        if self.database_url.startswith('duckdb://'):
            # DuckDB schema
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGINT PRIMARY KEY,
                date DATE NOT NULL,
                channel VARCHAR(20) NOT NULL,
                department VARCHAR(50) NOT NULL,
                promo_flag BOOLEAN DEFAULT FALSE,
                discount_pct NUMERIC(5,2),
                sales_value NUMERIC(15,2) NOT NULL,
                margin_value NUMERIC(15,2) NOT NULL,
                margin_pct NUMERIC(5,2),
                units INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (date, channel, department, promo_flag)
            )
            """
        else:
            # PostgreSQL schema
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGSERIAL PRIMARY KEY,
                date DATE NOT NULL,
                channel VARCHAR(20) NOT NULL CHECK (channel IN ('online', 'offline')),
                department VARCHAR(50) NOT NULL,
                promo_flag BOOLEAN DEFAULT FALSE,
                discount_pct NUMERIC(5,2),
                sales_value NUMERIC(15,2) NOT NULL,
                margin_value NUMERIC(15,2) NOT NULL,
                margin_pct NUMERIC(5,2) GENERATED ALWAYS AS (
                    CASE WHEN sales_value > 0 
                    THEN (margin_value / sales_value * 100) 
                    ELSE 0 END
                ) STORED,
                units INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT unique_sales_record UNIQUE (date, channel, department, promo_flag)
            )
            """
        
        try:
            if self.database_url.startswith('duckdb://'):
                self.engine.execute(create_sql)
            else:
                with self.engine.connect() as conn:
                    conn.execute(text(create_sql))
                    conn.commit()
            logger.info(f"Table {table_name} created or already exists")
        except Exception as e:
            logger.error(f"Failed to create table: {str(e)}")
            raise
    
    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str = 'sales_aggregated',
        if_exists: str = 'append',
        upsert: bool = False,
        conflict_keys: Optional[list] = None
    ) -> Dict:
        """
        Load DataFrame into database.
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            if_exists: What to do if table exists ('fail', 'replace', 'append')
            
        Returns:
            Dictionary with load results
        """
        if df.empty:
            return {
                "success": False,
                "message": "DataFrame is empty",
                "rows_inserted": 0
            }
        
        # Prepare DataFrame
        df_load = df.copy()
        
        # Add promo_flag if discount_pct exists
        if 'discount_pct' in df_load.columns:
            df_load['promo_flag'] = (df_load['discount_pct'] > 0) | (df_load['discount_pct'].notna())
        elif 'promo_flag' not in df_load.columns:
            df_load['promo_flag'] = False
        
        # Calculate margin_pct
        if 'sales_value' in df_load.columns and 'margin_value' in df_load.columns:
            df_load['margin_pct'] = (df_load['margin_value'] / df_load['sales_value'] * 100).where(
                df_load['sales_value'] > 0, 0
            )
        
        # Ensure required columns
        required_cols = ['date', 'channel', 'department', 'sales_value', 'margin_value', 'units']
        missing = [col for col in required_cols if col not in df_load.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Select only columns that exist in table
        table_columns = ['date', 'channel', 'department', 'promo_flag', 'discount_pct',
                        'sales_value', 'margin_value', 'units']
        df_load = df_load[[col for col in table_columns if col in df_load.columns]]
        
        try:
            # Create table if not exists
            self.create_table_if_not_exists(table_name)
            
            # Load data with optional upsert
            rows_before = self._count_rows(table_name)

            if upsert and conflict_keys:
                if self.database_url.startswith('duckdb://'):
                    # DuckDB MERGE
                    self.engine.register('df_temp', df_load)
                    conflict = ", ".join(conflict_keys)
                    assignments = ", ".join([f"{col}=excluded.{col}" for col in df_load.columns])
                    merge_sql = f"""
                    CREATE OR REPLACE TEMP TABLE tmp_load AS SELECT * FROM df_temp;
                    INSERT INTO {table_name}
                    SELECT * FROM tmp_load
                    ON CONFLICT ({conflict}) DO UPDATE SET {assignments};
                    """
                    self.engine.execute(merge_sql)
                else:
                    # PostgreSQL upsert via ON CONFLICT
                    with self.engine.begin() as conn:
                        tmp_table = f"{table_name}_tmp_load"
                        df_load.to_sql(tmp_table, conn, if_exists='replace', index=False)
                        conflict = ", ".join(conflict_keys)
                        columns = ", ".join(df_load.columns)
                        assignments = ", ".join([f"{col}=EXCLUDED.{col}" for col in df_load.columns if col not in conflict_keys])
                        upsert_sql = f"""
                        INSERT INTO {table_name} ({columns})
                        SELECT {columns} FROM {tmp_table}
                        ON CONFLICT ({conflict}) DO UPDATE SET {assignments};
                        DROP TABLE {tmp_table};
                        """
                        conn.execute(text(upsert_sql))
            else:
                if self.database_url.startswith('duckdb://'):
                    self.engine.execute(f"INSERT INTO {table_name} SELECT * FROM df_load")
                else:
                    df_load.to_sql(
                        table_name,
                        self.engine,
                        if_exists=if_exists,
                        index=False,
                        method='multi'
                    )

            rows_after = self._count_rows(table_name)
            rows_inserted = max(rows_after - rows_before, 0)
            
            logger.info(f"Loaded {rows_inserted} rows into {table_name}")
            
            return {
                "success": True,
                "message": f"Successfully loaded {rows_inserted} rows",
                "rows_inserted": rows_inserted,
                "table_name": table_name
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading data: {str(e)}")
            return {
                "success": False,
                "message": f"Database error: {str(e)}",
                "rows_inserted": 0
            }
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "rows_inserted": 0
            }
    
    def _count_rows(self, table_name: str) -> int:
        """Count rows in table."""
        try:
            if self.database_url.startswith('duckdb://'):
                result = self.engine.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                return result[0] if result else 0
            else:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    return result.scalar() or 0
        except:
            return 0
    
    def close(self):
        """Close database connection."""
        if self.engine:
            if self.database_url.startswith('duckdb://'):
                self.engine.close()
            else:
                self.engine.dispose()
            logger.info("Database connection closed")


