#!/usr/bin/env python3
"""
Export Production Schema Structure
Run this to export your production database schema for comparison with dev.
"""

import os
import sys
from sqlmodel import create_engine, text
from sqlalchemy import inspect

def main():
    print("📋 Exporting Production Database Schema")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        schema_report = []
        schema_report.append("# Production Database Schema Report")
        schema_report.append(f"Generated from: {database_url.split('@')[1] if '@' in database_url else 'database'}")
        schema_report.append("")
        
        table_names = inspector.get_table_names()
        schema_report.append(f"## Tables ({len(table_names)})")
        
        for table_name in sorted(table_names):
            schema_report.append(f"\n### Table: {table_name}")
            
            columns = inspector.get_columns(table_name)
            schema_report.append("| Column | Type | Nullable | Default |")
            schema_report.append("|--------|------|----------|---------|")
            
            for col in columns:
                nullable = "✓" if col['nullable'] else "✗"
                default = str(col['default']) if col['default'] else ""
                schema_report.append(f"| {col['name']} | {col['type']} | {nullable} | {default} |")
            
            # Foreign keys
            try:
                fks = inspector.get_foreign_keys(table_name)
                if fks:
                    schema_report.append("\n**Foreign Keys:**")
                    for fk in fks:
                        cols = ", ".join(fk['constrained_columns'])
                        ref_table = fk['referred_table']
                        ref_cols = ", ".join(fk['referred_columns'])
                        schema_report.append(f"- {cols} → {ref_table}({ref_cols})")
            except:
                pass
        
        # Save to file
        filename = "production_schema.md"
        with open(filename, 'w') as f:
            f.write('\n'.join(schema_report))
        
        print(f"✅ Schema exported to {filename}")
        print(f"📁 File contains {len(table_names)} tables")
        
        # Also print summary to console
        print(f"\n📊 PRODUCTION SCHEMA SUMMARY:")
        for table_name in sorted(table_names):
            columns = inspector.get_columns(table_name)
            print(f"   {table_name}: {len(columns)} columns")
        
        print(f"\n💡 Next steps:")
        print(f"1. Review {filename}")
        print(f"2. Compare with your dev schema")
        print(f"3. Use sync_prod_schema.py to generate fixes")
        
    except Exception as e:
        print(f"❌ Error exporting schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 