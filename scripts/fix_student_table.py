#!/usr/bin/env python3
"""
Fix Student Table Schema
Run this to fix the data type mismatches in the student table.
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
    print("🔧 Fixing Student Table Schema")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        print("🔍 Current issues identified:")
        print("   1. batch_id is VARCHAR but should be INTEGER (foreign key)")
        print("   2. project column exists but project_id column is missing")
        
        print(f"\n📋 Planned changes:")
        print("   1. Rename current batch_id to batch_id_old (backup)")
        print("   2. Add new batch_id as INTEGER with foreign key constraint")
        print("   3. Add project_id as INTEGER with foreign key constraint")  
        print("   4. Keep existing project column as reference")
        
        print(f"\n⚠️  IMPORTANT NOTES:")
        print("   - This will add new columns without removing existing data")
        print("   - You'll need to populate the new foreign key columns with proper IDs")
        print("   - Existing data in string columns will be preserved")
        
        response = input("\nProceed with schema fixes? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Operation cancelled.")
            sys.exit(0)
        
        with engine.connect() as conn:
            print(f"\n🚧 Step 1: Renaming current batch_id to batch_id_old...")
            conn.execute(text("ALTER TABLE student RENAME COLUMN batch_id TO batch_id_old"))
            print("✅ Renamed batch_id to batch_id_old")
            
            print(f"\n🚧 Step 2: Adding new batch_id as INTEGER...")
            conn.execute(text("ALTER TABLE student ADD COLUMN batch_id INTEGER"))
            print("✅ Added batch_id as INTEGER")
            
            print(f"\n🚧 Step 3: Adding foreign key constraint for batch_id...")
            try:
                conn.execute(text("ALTER TABLE student ADD CONSTRAINT fk_student_batch FOREIGN KEY (batch_id) REFERENCES batch(id)"))
                print("✅ Added foreign key constraint for batch_id")
            except Exception as e:
                print(f"⚠️  Warning: Could not add foreign key constraint: {e}")
                print("   This is OK - you can add it later after populating data")
            
            print(f"\n🚧 Step 4: Adding project_id as INTEGER...")
            conn.execute(text("ALTER TABLE student ADD COLUMN project_id INTEGER"))
            print("✅ Added project_id as INTEGER")
            
            print(f"\n🚧 Step 5: Adding foreign key constraint for project_id...")
            try:
                conn.execute(text("ALTER TABLE student ADD CONSTRAINT fk_student_project FOREIGN KEY (project_id) REFERENCES project(id)"))
                print("✅ Added foreign key constraint for project_id")
            except Exception as e:
                print(f"⚠️  Warning: Could not add foreign key constraint: {e}")
                print("   This is OK - you can add it later after populating data")
            
            conn.commit()
        
        print(f"\n✅ Schema fixes completed successfully!")
        
        print(f"\n📋 NEXT STEPS REQUIRED:")
        print("   1. Update batch_id values with proper integer IDs from batch table")
        print("   2. Update project_id values with proper integer IDs from project table")
        print("   3. Test your application to ensure it works")
        print("   4. Once confirmed working, you can drop the old string columns")
        
        print(f"\n💡 Example data migration queries:")
        print("   -- Update batch_id based on batch name:")
        print("   UPDATE student SET batch_id = b.id FROM batch b WHERE b.name = student.batch_id_old;")
        print()
        print("   -- Update project_id based on project name:")
        print("   UPDATE student SET project_id = p.id FROM project p WHERE p.name = student.project;")
        
        print(f"\n🔍 To verify the changes, run check_student_table.py again")
        
    except Exception as e:
        print(f"❌ Error during schema fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 