"""
Data Validation Tool for Data Analyst Agent

Validates data quality and generates quality reports.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataValidationTool:
    """Tool for validating data quality."""
    
    def __init__(self):
        self.required_columns = ['date', 'channel', 'department', 'sales_value', 'margin_value', 'units']
        self.valid_channels = ['online', 'offline']
        self.valid_departments = ['TV', 'Gaming', 'Audio', 'Accessories', 'Smartphones', 'Computers']
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and generate report.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with quality metrics and issues
        """
        if df.empty:
            return {
                "total_records": 0,
                "clean_records": 0,
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "timeliness": 0.0,
                "issues": []
            }
        
        issues = []
        
        # Completeness checks
        completeness_score, completeness_issues = self._check_completeness(df)
        issues.extend(completeness_issues)
        
        # Accuracy checks
        accuracy_score, accuracy_issues = self._check_accuracy(df)
        issues.extend(accuracy_issues)
        
        # Consistency checks
        consistency_score, consistency_issues = self._check_consistency(df)
        issues.extend(consistency_issues)
        
        # Timeliness checks
        timeliness_score, timeliness_issues = self._check_timeliness(df)
        issues.extend(timeliness_issues)

        # Anomaly detection (simple z-score on sales_value)
        anomaly_issues = self._check_anomalies(df)
        issues.extend(anomaly_issues)
        
        # Calculate clean records
        clean_records = len(df) - len([i for i in issues if i['severity'] == 'high'])
        
        return {
            "total_records": len(df),
            "clean_records": clean_records,
            "completeness": completeness_score,
            "accuracy": accuracy_score,
            "consistency": consistency_score,
            "timeliness": timeliness_score,
            "anomaly_checks": len(anomaly_issues),
            "overall_score": (completeness_score + accuracy_score + consistency_score + timeliness_score) / 4,
            "issues": issues,
            "date_range": {
                "start": str(df['date'].min()) if 'date' in df.columns else None,
                "end": str(df['date'].max()) if 'date' in df.columns else None
            },
            "channels": df['channel'].value_counts().to_dict() if 'channel' in df.columns else {},
            "departments": df['department'].value_counts().to_dict() if 'department' in df.columns else {}
        }
    
    def _check_completeness(self, df: pd.DataFrame) -> tuple:
        """Check for missing values."""
        issues = []
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0
        
        # Check required columns
        for col in self.required_columns:
            if col not in df.columns:
                issues.append({
                    "type": "missing_column",
                    "severity": "high",
                    "column": col,
                    "message": f"Required column '{col}' is missing"
                })
            elif df[col].isnull().any():
                missing_count = df[col].isnull().sum()
                missing_pct = (missing_count / len(df)) * 100
                issues.append({
                    "type": "missing_values",
                    "severity": "high" if missing_pct > 10 else "medium",
                    "column": col,
                    "count": int(missing_count),
                    "percentage": round(missing_pct, 2),
                    "message": f"Column '{col}' has {missing_count} missing values ({missing_pct:.1f}%)"
                })
        
        return completeness, issues
    
    def _check_accuracy(self, df: pd.DataFrame) -> tuple:
        """Check data accuracy (valid ranges, types)."""
        issues = []
        accuracy_score = 1.0
        
        # Check date format
        if 'date' in df.columns:
            try:
                pd.to_datetime(df['date'], errors='raise')
            except:
                issues.append({
                    "type": "invalid_date_format",
                    "severity": "high",
                    "column": "date",
                    "message": "Date column contains invalid date formats"
                })
                accuracy_score -= 0.3
        
        # Check channel values
        if 'channel' in df.columns:
            invalid_channels = df[~df['channel'].isin(self.valid_channels)]
            if len(invalid_channels) > 0:
                issues.append({
                    "type": "invalid_channel",
                    "severity": "medium",
                    "column": "channel",
                    "count": len(invalid_channels),
                    "invalid_values": invalid_channels['channel'].unique().tolist(),
                    "message": f"Found {len(invalid_channels)} records with invalid channel values"
                })
                accuracy_score -= 0.1
        
        # Check numeric columns
        numeric_cols = ['sales_value', 'margin_value', 'units']
        for col in numeric_cols:
            if col in df.columns:
                # Check for negative values (except margin_value)
                if col != 'margin_value':
                    negative = df[df[col] < 0]
                    if len(negative) > 0:
                        issues.append({
                            "type": "negative_values",
                            "severity": "medium",
                            "column": col,
                            "count": len(negative),
                            "message": f"Column '{col}' has {len(negative)} negative values"
                        })
                        accuracy_score -= 0.1
                
                # Check for outliers (values > 3 standard deviations)
                if len(df) > 10:  # Need enough data for outlier detection
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        outliers = df[abs(df[col] - mean) > 3 * std]
                        if len(outliers) > 0:
                            issues.append({
                                "type": "outliers",
                                "severity": "low",
                                "column": col,
                                "count": len(outliers),
                                "message": f"Column '{col}' has {len(outliers)} potential outliers"
                            })
        
        # Check discount percentage
        if 'discount_pct' in df.columns:
            invalid_discount = df[(df['discount_pct'] < 0) | (df['discount_pct'] > 100)]
            if len(invalid_discount) > 0:
                issues.append({
                    "type": "invalid_discount",
                    "severity": "medium",
                    "column": "discount_pct",
                    "count": len(invalid_discount),
                    "message": f"Found {len(invalid_discount)} records with discount outside 0-100% range"
                })
                accuracy_score -= 0.1
        
        accuracy_score = max(0.0, accuracy_score)
        return accuracy_score, issues
    
    def _check_consistency(self, df: pd.DataFrame) -> tuple:
        """Check data consistency."""
        issues = []
        consistency_score = 1.0
        
        # Check margin calculation consistency
        if 'sales_value' in df.columns and 'margin_value' in df.columns:
            # Calculate expected margin percentage
            df['calculated_margin_pct'] = (df['margin_value'] / df['sales_value'] * 100).where(df['sales_value'] > 0)
            
            # Check for unrealistic margins (>50% or <0%)
            unrealistic = df[(df['calculated_margin_pct'] > 50) | (df['calculated_margin_pct'] < 0)]
            if len(unrealistic) > 0:
                issues.append({
                    "type": "unrealistic_margin",
                    "severity": "medium",
                    "count": len(unrealistic),
                    "message": f"Found {len(unrealistic)} records with unrealistic margin percentages"
                })
                consistency_score -= 0.2
        
        # Check date consistency (no future dates)
        if 'date' in df.columns:
            today = datetime.now().date()
            future_dates = df[pd.to_datetime(df['date']).dt.date > today]
            if len(future_dates) > 0:
                issues.append({
                    "type": "future_dates",
                    "severity": "low",
                    "count": len(future_dates),
                    "message": f"Found {len(future_dates)} records with future dates"
                })
        
        consistency_score = max(0.0, consistency_score)
        return consistency_score, issues
    
    def _check_timeliness(self, df: pd.DataFrame) -> tuple:
        """Check data timeliness."""
        issues = []
        timeliness_score = 1.0
        
        if 'date' in df.columns:
            # Check for gaps in date sequence
            dates = pd.to_datetime(df['date']).dt.date.unique()
            dates_sorted = sorted(dates)
            
            if len(dates_sorted) > 1:
                gaps = []
                for i in range(len(dates_sorted) - 1):
                    gap_days = (dates_sorted[i+1] - dates_sorted[i]).days
                    if gap_days > 1:
                        gaps.append({
                            "start": str(dates_sorted[i]),
                            "end": str(dates_sorted[i+1]),
                            "gap_days": gap_days
                        })
                
                if gaps:
                    issues.append({
                        "type": "date_gaps",
                        "severity": "low",
                        "count": len(gaps),
                        "gaps": gaps[:10],  # Limit to first 10
                        "message": f"Found {len(gaps)} gaps in date sequence"
                    })
                    timeliness_score -= 0.1
        
        timeliness_score = max(0.0, timeliness_score)
        return timeliness_score, issues

    def _check_anomalies(self, df: pd.DataFrame) -> list:
        """Simple anomaly checks for extreme sales values."""
        issues = []
        if 'sales_value' in df.columns and len(df) > 10:
            mean = df['sales_value'].mean()
            std = df['sales_value'].std()
            if std > 0:
                zscores = (df['sales_value'] - mean) / std
                outliers = df[abs(zscores) > 4]
                if len(outliers) > 0:
                    issues.append({
                        "type": "anomaly_sales",
                        "severity": "low",
                        "count": len(outliers),
                        "message": f"Detected {len(outliers)} anomalous sales values (>|4| z-score)"
                    })
        return issues


