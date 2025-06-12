#!/usr/bin/env python3
"""
Database Table Checker
Run this to see what tables exist in your production database.
"""

import os
import sys
from sqlmodel import SQLModel, create_engine, text

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all models to register them with SQLModel metadata
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

def main():
    print("🔍 Database Table Checker")
    print("=" * 40)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        # Get existing tables
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            existing_tables = [row[0] for row in result]
        
        # Get required tables from metadata
        required_tables = sorted(SQLModel.metadata.tables.keys())
        existing_tables_set = set(existing_tables)
        required_tables_set = set(required_tables)
        
        print(f"📋 EXISTING TABLES ({len(existing_tables)}):")
        for table in existing_tables:
            status = "✅" if table in required_tables_set else "❓"
            print(f"   {status} {table}")
        
        print(f"\n📝 REQUIRED TABLES ({len(required_tables)}):")
        for table in required_tables:
            status = "✅" if table in existing_tables_set else "❌"
            print(f"   {status} {table}")
        
        missing_tables = required_tables_set - existing_tables_set
        extra_tables = existing_tables_set - required_tables_set
        
        if missing_tables:
            print(f"\n❌ MISSING TABLES ({len(missing_tables)}):")
            for table in sorted(missing_tables):
                print(f"   - {table}")
        
        if extra_tables:
            print(f"\n❓ EXTRA TABLES ({len(extra_tables)}):")
            for table in sorted(extra_tables):
                print(f"   - {table}")
        
        if not missing_tables:
            print(f"\n✅ All required tables exist!")
        else:
            print(f"\n⚠️  {len(missing_tables)} tables are missing and need to be created.")
            
        # Check specifically for the batchstudentlink table
        if 'batchstudentlink' in missing_tables:
            print(f"\n🔍 The 'batchstudentlink' table is missing - this is causing your admin dashboard error.")
        elif 'batchstudentlink' in existing_tables:
            print(f"\n✅ The 'batchstudentlink' table exists.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 