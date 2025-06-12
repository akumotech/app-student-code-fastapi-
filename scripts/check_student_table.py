#!/usr/bin/env python3
"""
Check Student Table Structure
Run this to see the actual vs expected structure of the student table.
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
    print("🔍 Student Table Structure Checker")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        # Get actual table structure from database
        print("📋 ACTUAL STUDENT TABLE STRUCTURE (from database):")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'student'
                ORDER BY ordinal_position
            """))
            actual_columns = list(result)
            
        if not actual_columns:
            print("❌ Student table does not exist in database!")
            return
            
        for col in actual_columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"   {col[0]}: {col[1]} {nullable}{default}")
        
        # Get expected table structure from SQLModel
        print(f"\n📝 EXPECTED STUDENT TABLE STRUCTURE (from SQLModel):")
        if 'student' in SQLModel.metadata.tables:
            student_table = SQLModel.metadata.tables['student']
            for column in student_table.columns:
                nullable = "NULL" if column.nullable else "NOT NULL"
                print(f"   {column.name}: {column.type} {nullable}")
        else:
            print("❌ Student table not found in SQLModel metadata!")
            return
        
        # Compare structures
        print(f"\n🔍 ANALYSIS:")
        actual_col_names = {col[0] for col in actual_columns}
        expected_col_names = {col.name for col in student_table.columns}
        
        missing_in_db = expected_col_names - actual_col_names
        extra_in_db = actual_col_names - expected_col_names
        
        if missing_in_db:
            print(f"❌ MISSING COLUMNS IN DATABASE:")
            for col in missing_in_db:
                print(f"   - {col}")
        
        if extra_in_db:
            print(f"❓ EXTRA COLUMNS IN DATABASE:")
            for col in extra_in_db:
                print(f"   - {col}")
                
        if not missing_in_db and not extra_in_db:
            print("✅ Column names match!")
        
        # Check specifically for the batch_id vs batch issue
        if 'batch_id' in expected_col_names and 'batch' in actual_col_names:
            print(f"\n🎯 FOUND THE ISSUE:")
            print(f"   - Database has column: 'batch'")
            print(f"   - Application expects: 'batch_id'")
            print(f"   - This is causing the error!")
            
            print(f"\n💡 SOLUTION OPTIONS:")
            print(f"   1. Rename database column 'batch' to 'batch_id'")
            print(f"   2. Update the model to use 'batch' instead of 'batch_id'")
            print(f"   3. Add missing 'batch_id' column and migrate data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 