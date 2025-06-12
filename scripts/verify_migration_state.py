#!/usr/bin/env python3
"""
Verify Migration State and Setup
Run this to confirm your database is properly set up for future migrations.
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

def check_alembic_state(engine):
    """Check if Alembic is properly tracking the database"""
    try:
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')"
            ))
            alembic_exists = result.scalar()
            
            if not alembic_exists:
                return False, "Alembic version table doesn't exist"
            
            # Check current revision
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_revision = result.scalar()
            
            if not current_revision:
                return False, "No current revision set"
                
            return True, current_revision
    except Exception as e:
        return False, f"Error checking Alembic state: {e}"

def check_schema_match(engine):
    """Check if current schema matches SQLModel metadata"""
    inspector = inspect(engine)
    issues = []
    
    for table_name, table in SQLModel.metadata.tables.items():
        if table_name not in inspector.get_table_names():
            issues.append(f"Missing table: {table_name}")
            continue
            
        db_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        model_columns = {col.name: col for col in table.columns}
        
        for col_name in model_columns:
            if col_name not in db_columns:
                issues.append(f"Missing column: {table_name}.{col_name}")
    
    return issues

def main():
    print("🔍 Verifying Migration State and Setup")
    print("=" * 50)
    
    # Check for DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        # Check Alembic state
        print("📋 Checking Alembic migration tracking...")
        alembic_ok, alembic_info = check_alembic_state(engine)
        
        if alembic_ok:
            print(f"✅ Alembic is tracking migrations (current revision: {alembic_info})")
        else:
            print(f"❌ Alembic issue: {alembic_info}")
            print("   Run 'alembic stamp head' to fix this")
        
        # Check schema consistency
        print("\n🔍 Checking schema consistency...")
        schema_issues = check_schema_match(engine)
        
        if not schema_issues:
            print("✅ Database schema matches your models")
        else:
            print(f"❌ Found {len(schema_issues)} schema issues:")
            for issue in schema_issues[:5]:  # Show first 5 issues
                print(f"   - {issue}")
            if len(schema_issues) > 5:
                print(f"   ... and {len(schema_issues) - 5} more")
        
        # Overall assessment
        print(f"\n📊 OVERALL ASSESSMENT:")
        if alembic_ok and not schema_issues:
            print("🎉 EXCELLENT! Your database is properly set up for migrations")
            print("\n✅ You should NOT have database drift issues going forward IF you follow proper workflow")
        elif alembic_ok and schema_issues:
            print("⚠️  PARTIAL: Alembic is set up but schema has issues")
            print("   You may still have some drift - consider running sync script again")
        elif not alembic_ok and not schema_issues:
            print("⚠️  PARTIAL: Schema is good but Alembic tracking is missing")
            print("   Run 'alembic stamp head' to complete setup")
        else:
            print("❌ ISSUES: Both schema and Alembic tracking need attention")
        
        # Best practices guidance
        print(f"\n📝 BEST PRACTICES TO PREVENT FUTURE DRIFT:")
        print("1. 🚫 NEVER modify database directly in production")
        print("2. 📝 ALWAYS create migrations for model changes:")
        print("   - Make model changes in your code")
        print("   - Run: alembic revision --autogenerate -m 'description'")
        print("   - Review the generated migration file")
        print("   - Test on staging/dev first")
        print("   - Deploy migration to production: alembic upgrade head")
        print("3. 🔄 Keep environments in sync:")
        print("   - Dev → Staging → Production")
        print("   - Same migration process for all environments")
        print("4. 🏗️  For major changes:")
        print("   - Plan data migrations carefully")
        print("   - Always backup before migrations")
        print("   - Test rollback procedures")
        
        # Check current migration files
        print(f"\n📁 CURRENT MIGRATION FILES:")
        alembic_dir = "alembic/versions"
        if os.path.exists(alembic_dir):
            migration_files = [f for f in os.listdir(alembic_dir) if f.endswith('.py')]
            if migration_files:
                print(f"   Found {len(migration_files)} migration files:")
                for f in sorted(migration_files)[-3:]:  # Show last 3
                    print(f"   - {f}")
                if len(migration_files) > 3:
                    print(f"   ... and {len(migration_files) - 3} earlier files")
            else:
                print("   ⚠️  No migration files found")
        else:
            print("   ❌ Alembic versions directory not found")
        
        # Container vs non-container guidance
        print(f"\n🐳 ENVIRONMENT-SPECIFIC NOTES:")
        print("📦 For containerized deployments:")
        print("   - Migrations run automatically via docker-entrypoint.sh")
        print("   - Your current setup should handle this")
        print("🖥️  For non-containerized deployments:")
        print("   - Run 'alembic upgrade head' manually after code updates")
        print("   - Consider adding this to your deployment scripts")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 