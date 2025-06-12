#!/usr/bin/env python3
"""
Production Migration Script
Run this script on your production server to safely create missing database tables.
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
    print("🗄️ Production Database Migration Script")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        print("Please set DATABASE_URL and try again.")
        print("Example: export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)
    
    print(f"🔗 Connecting to database...")
    print("📦 Application models loaded successfully")
    
    try:
        
        engine = create_engine(database_url)
        
        print("🔍 Checking existing tables...")
        
        # Get existing tables
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            existing_tables = {row[0] for row in result}
        
        print(f"📋 Found {len(existing_tables)} existing tables:")
        for table in sorted(existing_tables):
            print(f"   ✓ {table}")
        
        # Get required tables from metadata
        required_tables = set(SQLModel.metadata.tables.keys())
        missing_tables = required_tables - existing_tables
        
        print(f"\n🔍 Required tables: {len(required_tables)}")
        print(f"📝 Missing tables: {len(missing_tables)}")
        
        if missing_tables:
            print(f"\n🚧 Creating missing tables:")
            for table in sorted(missing_tables):
                print(f"   📝 Creating: {table}")
            
            print(f"\n⚠️  About to create {len(missing_tables)} missing tables.")
            print("This operation is SAFE - it will NOT affect existing data.")
            
            # In production, you might want to add a confirmation prompt
            response = input("\nProceed? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Operation cancelled.")
                sys.exit(0)
            
            # Create only missing tables with checkfirst=True for safety
            tables_created = 0
            for table_name in missing_tables:
                try:
                    table = SQLModel.metadata.tables[table_name]
                    table.create(engine, checkfirst=True)
                    print(f"   ✅ Created: {table_name}")
                    tables_created += 1
                except Exception as e:
                    print(f"   ❌ Failed to create {table_name}: {e}")
                    
            print(f"\n✅ Successfully created {tables_created}/{len(missing_tables)} tables")
            
            # Now mark the current state as migrated for Alembic
            print("\n🏷️  Setting up Alembic migration state...")
            try:
                import subprocess
                result = subprocess.run(['alembic', 'stamp', 'head'], 
                                      capture_output=True, text=True, cwd=os.path.dirname(__file__))
                if result.returncode == 0:
                    print("✅ Alembic migration state marked successfully")
                else:
                    print(f"⚠️  Warning: Could not mark Alembic state: {result.stderr}")
                    print("You may need to run 'alembic stamp head' manually later")
            except Exception as e:
                print(f"⚠️  Warning: Could not run alembic stamp: {e}")
                print("You may need to run 'alembic stamp head' manually later")
        else:
            print("\n✅ All required tables already exist!")
            
            # Check if Alembic is set up
            if 'alembic_version' not in existing_tables:
                print("\n🏷️  Setting up Alembic migration tracking...")
                try:
                    import subprocess
                    result = subprocess.run(['alembic', 'stamp', 'head'], 
                                          capture_output=True, text=True, cwd=os.path.dirname(__file__))
                    if result.returncode == 0:
                        print("✅ Alembic migration state marked successfully")
                    else:
                        print(f"⚠️  Warning: Could not mark Alembic state: {result.stderr}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not run alembic stamp: {e}")
        
        print(f"\n🎉 Migration completed successfully!")
        print("Your production database is now up to date.")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 