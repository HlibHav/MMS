"""
Example usage of Data Analyst Agent tools.

This script demonstrates how to use the tools to process XLSB files
and load them into the database.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    XLSBReaderTool,
    DataCleaningTool,
    DataMergerTool,
    DataValidationTool,
    DatabaseLoaderTool,
    PromoProcessor
)


def process_data_files(
    file_paths: list,
    database_url: str,
    merge_strategy: str = 'union'
):
    """
    Process XLSB files and load into database.
    
    Args:
        file_paths: List of paths to XLSB files
        database_url: Database connection string
        merge_strategy: 'union', 'intersect', or 'overwrite'
    """
    print("=" * 60)
    print("Data Analyst Agent - Processing Files")
    print("=" * 60)
    
    # Step 1: Read XLSB files
    print("\n1. Reading XLSB files...")
    reader = XLSBReaderTool()
    dataframes = {}
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"   ⚠️  File not found: {file_path}")
            continue
        
        print(f"   📄 Reading: {file_path}")
        try:
            # Inspect file first
            metadata = reader.inspect_file(file_path)
            print(f"      - Sheets: {metadata['sheets']}")
            print(f"      - Columns: {len(metadata['columns'])}")
            print(f"      - Rows: {metadata['row_count']}")
            print(f"      - Size: {metadata['file_size_mb']} MB")
            
            # Read file
            df = reader.read_file(file_path)
            dataframes[file_path] = df
            print(f"      ✅ Loaded {len(df)} rows")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            dataframes[file_path] = None
    
    # Step 2: Clean data
    print("\n2. Cleaning data...")
    cleaner = DataCleaningTool()
    cleaned_dataframes = {}
    
    for file_path, df in dataframes.items():
        if df is None or df.empty:
            continue
        
        print(f"   🧹 Cleaning: {os.path.basename(file_path)}")
        try:
            cleaned_df = cleaner.clean_dataframe(df)
            cleaned_dataframes[file_path] = cleaned_df
            print(f"      ✅ Cleaned: {len(cleaned_df)} rows")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
    
    # Step 3: Detect overlaps
    print("\n3. Detecting overlaps...")
    merger = DataMergerTool()
    overlap_info = merger.detect_overlaps(cleaned_dataframes)
    
    if overlap_info['has_overlaps']:
        print(f"   ⚠️  Found {len(overlap_info['overlaps'])} overlaps:")
        for overlap in overlap_info['overlaps']:
            print(f"      - {os.path.basename(overlap['file1'])} ↔ {os.path.basename(overlap['file2'])}")
            print(f"        Overlap: {overlap['overlap_start']} to {overlap['overlap_end']} ({overlap['overlap_days']} days)")
    else:
        print("   ✅ No overlaps detected")
    
    # Step 4: Merge files
    print(f"\n4. Merging files (strategy: {merge_strategy})...")
    try:
        merged_df = merger.merge_files(cleaned_dataframes, merge_strategy=merge_strategy)
        print(f"   ✅ Merged: {len(merged_df)} total rows")
        print(f"      - Date range: {merged_df['date'].min()} to {merged_df['date'].max()}")
        print(f"      - Channels: {merged_df['channel'].unique().tolist()}")
        print(f"      - Departments: {sorted(merged_df['department'].unique().tolist())}")
    except Exception as e:
        print(f"   ❌ Error merging: {str(e)}")
        return
    
    # Step 5: Validate data quality
    print("\n5. Validating data quality...")
    validator = DataValidationTool()
    quality_report = validator.validate_data_quality(merged_df)
    
    print(f"   📊 Quality Report:")
    print(f"      - Total records: {quality_report['total_records']:,}")
    print(f"      - Clean records: {quality_report['clean_records']:,}")
    print(f"      - Completeness: {quality_report['completeness']:.1%}")
    print(f"      - Accuracy: {quality_report['accuracy']:.1%}")
    print(f"      - Consistency: {quality_report['consistency']:.1%}")
    print(f"      - Timeliness: {quality_report['timeliness']:.1%}")
    print(f"      - Overall score: {quality_report['overall_score']:.1%}")
    
    if quality_report['issues']:
        print(f"\n   ⚠️  Found {len(quality_report['issues'])} issues:")
        for issue in quality_report['issues'][:5]:  # Show first 5
            print(f"      - [{issue['severity'].upper()}] {issue['message']}")
        if len(quality_report['issues']) > 5:
            print(f"      ... and {len(quality_report['issues']) - 5} more")
    
    # Step 6: Load to database
    print("\n6. Loading to database...")
    loader = DatabaseLoaderTool(database_url)
    
    try:
        result = loader.load_dataframe(merged_df, table_name='sales_aggregated', if_exists='append')
        
        if result['success']:
            print(f"   ✅ Successfully loaded {result['rows_inserted']:,} rows")
        else:
            print(f"   ❌ Failed: {result['message']}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    finally:
        loader.close()
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)
    
    return quality_report


def process_promo_file_example():
    """Example of processing promotional catalog file."""
    print("\n" + "=" * 60)
    print("Promo Catalog Processing Example")
    print("=" * 60)
    
    data_dir = Path(__file__).parent.parent.parent / "Data"
    promo_file = str(data_dir / "Promo_October-September_FY25.xlsb")
    
    if not Path(promo_file).exists():
        print(f"⚠️  Promo file not found: {promo_file}")
        return
    
    database_url = "duckdb:///data/promo.db"
    
    # Initialize processor
    processor = PromoProcessor(database_url)
    
    # Process promo file
    result = processor.process_promo_file(promo_file, load_to_db=True)
    
    print(f"\n✅ Processing complete!")
    print(f"   - Campaigns extracted: {result['campaigns_extracted']}")
    print(f"   - Records processed: {result['records_processed']}")
    if result.get('quality_report'):
        print(f"   - Quality score: {result['quality_report']['overall_score']:.1%}")
    
    if result.get('campaigns'):
        print(f"\n📋 Sample campaigns:")
        for i, campaign in enumerate(result['campaigns'][:3], 1):
            print(f"   {i}. {campaign.get('promo_name', 'N/A')}")
            print(f"      Dates: {campaign.get('date_start')} to {campaign.get('date_end')}")
            print(f"      Departments: {', '.join(campaign.get('departments', []))}")
            print(f"      Avg Discount: {campaign.get('avg_discount_pct', 0):.1f}%")


if __name__ == "__main__":
    # Example usage - Sales data files
    data_dir = Path(__file__).parent.parent.parent / "Data"
    
    # Example file paths (adjust based on your actual files)
    file_paths = [
        str(data_dir / "Web_September_FY25.xlsb"),
        str(data_dir / "Web_October-January_FY25.xlsb"),
        # Add more files as needed
    ]
    
    # Database URL (DuckDB for local, PostgreSQL for production)
    database_url = "duckdb:///data/promo.db"
    # database_url = "postgresql://user:pass@localhost:5432/promo_co_pilot"
    
    # Process sales data files
    quality_report = process_data_files(
        file_paths=file_paths,
        database_url=database_url,
        merge_strategy='union'
    )
    
    # Process promo catalog file
    process_promo_file_example()

