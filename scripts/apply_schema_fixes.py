#!/usr/bin/env python3
"""
Apply Schema Fixes Safely
Run this to apply the generated schema fixes to your production database.
"""

import os
import sys
from sqlmodel import create_engine, text
from datetime import datetime

def main():
    print("🔧 Applying Schema Fixes to Production")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    # Check if fixes file exists
    if not os.path.exists('schema_fixes.sql'):
        print("❌ ERROR: schema_fixes.sql file not found")
        print("Run sync_prod_schema.py first to generate the fixes")
        sys.exit(1)
    
    # Read and display the fixes
    print("📋 REVIEWING GENERATED FIXES:")
    print("=" * 30)
    with open('schema_fixes.sql', 'r') as f:
        fixes_content = f.read()
    
    print(fixes_content)
    print("=" * 30)
    
    print(f"\n⚠️  IMPORTANT SAFETY CHECKS:")
    print("1. Have you backed up your production database?")
    print("2. Have you reviewed all the SQL statements above?")
    print("3. Are you sure you want to apply these changes?")
    
    response = input("\n✅ I have backed up my database and reviewed the changes (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Operation cancelled. Please backup your database first!")
        sys.exit(0)
    
    try:
        engine = create_engine(database_url)
        
        # Parse SQL statements (simple approach - split by semicolon)
        sql_statements = []
        for line in fixes_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--') and line.endswith(';'):
                sql_statements.append(line[:-1])  # Remove semicolon
        
        if not sql_statements:
            print("✅ No SQL statements to execute (only comments found)")
            return
        
        print(f"\n🚧 Applying {len(sql_statements)} schema changes...")
        
        executed_statements = []
        failed_statements = []
        
        with engine.connect() as conn:
            for i, sql in enumerate(sql_statements, 1):
                try:
                    print(f"   {i}/{len(sql_statements)}: Executing: {sql[:60]}{'...' if len(sql) > 60 else ''}")
                    conn.execute(text(sql))
                    executed_statements.append(sql)
                    print(f"   ✅ Success")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    failed_statements.append((sql, str(e)))
                    
                    # Ask if user wants to continue
                    if len(failed_statements) < 3:  # Only ask for first few failures
                        response = input(f"   Continue with remaining statements? (y/N): ").strip().lower()
                        if response != 'y':
                            print("   Stopping execution...")
                            break
            
            # Commit changes
            if executed_statements and not failed_statements:
                conn.commit()
                print(f"\n✅ All {len(executed_statements)} statements executed successfully!")
            elif executed_statements:
                conn.commit()
                print(f"\n⚠️  {len(executed_statements)} statements succeeded, {len(failed_statements)} failed")
            else:
                conn.rollback()
                print(f"\n❌ No statements executed successfully")
                
        # Summary
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"   ✅ Successful: {len(executed_statements)}")
        print(f"   ❌ Failed: {len(failed_statements)}")
        
        if failed_statements:
            print(f"\n❌ FAILED STATEMENTS:")
            for sql, error in failed_statements:
                print(f"   - {sql}")
                print(f"     Error: {error}")
        
        if executed_statements and len(failed_statements) == 0:
            print(f"\n🎉 Schema sync completed successfully!")
            print(f"📝 Next step: Run 'alembic stamp head' to mark schema as current")
            
            # Offer to run alembic stamp head
            response = input(f"\nRun 'alembic stamp head' now? (y/N): ").strip().lower()
            if response == 'y':
                try:
                    import subprocess
                    result = subprocess.run(['alembic', 'stamp', 'head'], 
                                          capture_output=True, text=True, cwd=os.path.dirname(__file__))
                    if result.returncode == 0:
                        print("✅ Alembic migration state marked successfully")
                    else:
                        print(f"⚠️  Warning: alembic stamp failed: {result.stderr}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not run alembic stamp: {e}")
        
        # Create backup log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"schema_fix_log_{timestamp}.txt"
        with open(log_filename, 'w') as f:
            f.write(f"Schema Fix Application Log - {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            f.write("EXECUTED STATEMENTS:\n")
            for sql in executed_statements:
                f.write(f"✅ {sql}\n")
            f.write(f"\nFAILED STATEMENTS:\n")
            for sql, error in failed_statements:
                f.write(f"❌ {sql}\n")
                f.write(f"   Error: {error}\n")
        
        print(f"\n📝 Execution log saved to: {log_filename}")
        
    except Exception as e:
        print(f"❌ Error applying schema fixes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 