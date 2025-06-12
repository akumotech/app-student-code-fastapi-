#!/usr/bin/env python3
"""
Create Missing batchstudentlink Table
Run this to create the single missing table that's causing the admin dashboard error.
"""

import os
import sys
from sqlmodel import SQLModel, create_engine

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all models to register them with SQLModel metadata
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

def main():
    print("🔧 Creating Missing batchstudentlink Table")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        # Get the specific table we need to create
        table_name = 'batchstudentlink'
        
        if table_name in SQLModel.metadata.tables:
            table = SQLModel.metadata.tables[table_name]
            
            print(f"🔍 Found table definition for: {table_name}")
            print(f"📝 Table columns:")
            for column in table.columns:
                print(f"   - {column.name}: {column.type}")
            
            print(f"\n⚠️  About to create the {table_name} table.")
            print("This operation is SAFE - it will NOT affect existing data.")
            
            response = input("\nProceed? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Operation cancelled.")
                sys.exit(0)
            
            # Create the missing table
            print(f"\n🚧 Creating {table_name} table...")
            table.create(engine, checkfirst=True)
            print(f"✅ Successfully created {table_name} table!")
            
            # Verify it was created
            print(f"\n🔍 Verifying table creation...")
            from sqlmodel import text
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table_name}')"))
                exists = result.scalar()
                if exists:
                    print(f"✅ Verification successful: {table_name} table exists")
                else:
                    print(f"❌ Verification failed: {table_name} table was not created")
                    sys.exit(1)
            
            print(f"\n🎉 Success! Your admin dashboard should now work properly.")
            print(f"The {table_name} table has been created and is ready to store user-batch relationships.")
            
        else:
            print(f"❌ ERROR: Could not find table definition for {table_name}")
            print("Available tables in metadata:")
            for name in sorted(SQLModel.metadata.tables.keys()):
                print(f"   - {name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 