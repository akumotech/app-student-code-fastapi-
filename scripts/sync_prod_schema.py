#!/usr/bin/env python3
"""
Production Schema Sync
Sync your production database schema with your dev schema (SQLModel metadata).
This will identify all differences and generate the necessary ALTER statements.
"""

import os
import sys
from sqlmodel import SQLModel, create_engine, text
from sqlalchemy import inspect

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all models to register them with SQLModel metadata
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

def get_db_table_info(engine, table_name):
    """Get detailed table information from database"""
    inspector = inspect(engine)
    
    if table_name not in inspector.get_table_names():
        return None
        
    columns = {}
    for col in inspector.get_columns(table_name):
        columns[col['name']] = {
            'type': str(col['type']),
            'nullable': col['nullable'],
            'default': col['default']
        }
    
    return columns

def compare_schemas(engine):
    """Compare SQLModel metadata with actual database schema"""
    print("🔍 Comparing dev schema (SQLModel) with production database...")
    
    issues = []
    fixes = []
    
    for table_name, table in SQLModel.metadata.tables.items():
        print(f"\n📋 Checking table: {table_name}")
        
        # Get current table structure from database
        db_columns = get_db_table_info(engine, table_name)
        
        if db_columns is None:
            print(f"   ❌ Table {table_name} doesn't exist in database")
            issues.append(f"Missing table: {table_name}")
            fixes.append(f"-- Create missing table {table_name}")
            fixes.append(f"-- This should be handled by the create_missing_table.py script")
            continue
        
        # Compare each column
        model_columns = {col.name: col for col in table.columns}
        
        for col_name, col in model_columns.items():
            if col_name not in db_columns:
                print(f"   ❌ Missing column: {col_name}")
                issues.append(f"{table_name}.{col_name} - missing column")
                
                col_type = str(col.type)
                nullable = "NULL" if col.nullable else "NOT NULL"
                fixes.append(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable};")
                
            else:
                # Check data type compatibility
                db_col = db_columns[col_name]
                model_type = str(col.type).upper()
                db_type = db_col['type'].upper()
                
                # Common type mappings for comparison
                type_mappings = {
                    'INTEGER': ['INT', 'INT4', 'SERIAL'],
                    'VARCHAR': ['CHARACTER VARYING', 'TEXT'],
                    'BOOLEAN': ['BOOL'],
                    'DATETIME': ['TIMESTAMP', 'TIMESTAMP WITHOUT TIME ZONE'],
                    'DATE': ['DATE'],
                    'FLOAT': ['REAL', 'DOUBLE PRECISION']
                }
                
                types_match = False
                for standard, variants in type_mappings.items():
                    if model_type.startswith(standard) and any(db_type.startswith(v) for v in variants):
                        types_match = True
                        break
                    if db_type.startswith(standard) and any(model_type.startswith(v) for v in variants):
                        types_match = True
                        break
                
                if not types_match and model_type != db_type:
                    print(f"   ⚠️  Type mismatch {col_name}: DB has {db_type}, model expects {model_type}")
                    issues.append(f"{table_name}.{col_name} - type mismatch: {db_type} vs {model_type}")
                    
                    # For type changes, we need to be more careful
                    fixes.append(f"-- {table_name}.{col_name}: Change from {db_type} to {model_type}")
                    fixes.append(f"-- ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {model_type}; -- REVIEW THIS CAREFULLY")
                    
        # Check for extra columns in database
        for db_col_name in db_columns:
            if db_col_name not in model_columns:
                print(f"   ❓ Extra column in DB: {db_col_name}")
                # Don't automatically drop columns - just note them
                fixes.append(f"-- Extra column {table_name}.{db_col_name} exists in DB but not in model")
    
    return issues, fixes

def main():
    print("🔄 Production Database Schema Sync")
    print("=" * 60)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        print("📦 Loaded SQLModel metadata with tables:")
        for table_name in sorted(SQLModel.metadata.tables.keys()):
            print(f"   - {table_name}")
        
        # Compare schemas
        issues, fixes = compare_schemas(engine)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Found {len(issues)} schema issues")
        
        if not issues:
            print("✅ Your production database schema matches your dev schema!")
            return
        
        print(f"\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        
        print(f"\n🔧 GENERATED FIXES:")
        print("-- SQL script to sync production with dev schema")
        print("-- REVIEW CAREFULLY before executing!")
        print("-- Backup your database before applying these changes")
        print()
        
        for fix in fixes:
            print(fix)
        
        print(f"\n💾 Save fixes to file? (y/N): ", end="")
        response = input().strip().lower()
        if response == 'y':
            with open('schema_fixes.sql', 'w') as f:
                f.write("-- Schema fixes to sync production with dev\n")
                f.write("-- Generated by sync_prod_schema.py\n")
                f.write("-- REVIEW CAREFULLY before executing!\n")
                f.write("-- Backup your database before applying these changes\n\n")
                for fix in fixes:
                    f.write(fix + '\n')
            print("✅ Fixes saved to schema_fixes.sql")
        
        print(f"\n⚠️  NEXT STEPS:")
        print("1. Review the generated SQL fixes carefully")
        print("2. Backup your production database")
        print("3. Test the fixes on a database copy first")
        print("4. Apply the fixes to production")
        print("5. Run alembic stamp head to mark schema as current")
        
    except Exception as e:
        print(f"❌ Error during schema comparison: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 