#!/usr/bin/env python3
"""
Alembic Setup Checker
Validates the Alembic configuration and identifies any issues
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables...")
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Hide password for security
        safe_url = database_url.replace('://', '://***@').split('@')[-1] if '@' in database_url else database_url
        print(f"✅ DATABASE_URL is set: {safe_url}")
    else:
        print("❌ DATABASE_URL is not set")
        print("   Set it with: export DATABASE_URL='postgresql://user:pass@localhost/dbname'")
        return False
    
    return True

def check_alembic_files():
    """Check if all required Alembic files exist"""
    print("\n🗄️ Checking Alembic Files...")
    
    required_files = [
        'alembic.ini',
        'alembic/env.py',
        'alembic/script.py.mako',
        'alembic/versions'
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def check_migrations():
    """Check migration files"""
    print("\n📋 Checking Migration Files...")
    
    versions_dir = Path('alembic/versions')
    if not versions_dir.exists():
        print("❌ Versions directory doesn't exist")
        return False
    
    migration_files = list(versions_dir.glob('*.py'))
    migration_files = [f for f in migration_files if not f.name.startswith('__')]
    
    if migration_files:
        print(f"✅ Found {len(migration_files)} migration file(s):")
        for file in migration_files:
            print(f"   • {file.name}")
    else:
        print("⚠️  No migration files found")
        print("   Run: alembic revision --autogenerate -m 'Initial migration'")
    
    return len(migration_files) > 0

def check_model_imports():
    """Check if models can be imported"""
    print("\n🏗️ Checking Model Imports...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        # Try importing models
        from app.auth.models import User
        print("✅ app.auth.models imported successfully")
        
        from app.students.models import Student
        print("✅ app.students.models imported successfully")
        
        from app.integrations.model import WakatimeIntegration
        print("✅ app.integrations.model imported successfully")
        
        from app.admin.models import AdminActivityLog
        print("✅ app.admin.models imported successfully")
        
        from sqlmodel import SQLModel
        print("✅ SQLModel imported successfully")
        
        return True
    
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_requirements():
    """Check if alembic is in requirements.txt"""
    print("\n📦 Checking Requirements...")
    
    req_file = Path('requirements.txt')
    if req_file.exists():
        content = req_file.read_text()
        if 'alembic' in content:
            print("✅ alembic found in requirements.txt")
            return True
        else:
            print("❌ alembic not found in requirements.txt")
            print("   Add: alembic==1.13.1")
            return False
    else:
        print("❌ requirements.txt not found")
        return False

def main():
    """Run all checks"""
    print("🚀 Alembic Setup Checker")
    print("=" * 40)
    
    checks = [
        ("Environment Variables", check_environment),
        ("Required Files", check_alembic_files),
        ("Migration Files", check_migrations),
        ("Model Imports", check_model_imports),
        ("Requirements", check_requirements),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n📊 Summary:")
    print("=" * 40)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All checks passed! Your Alembic setup looks good!")
        print("\nNext steps:")
        print("1. Run: alembic current (to check status)")
        print("2. Run: alembic stamp head (if this is initial setup)")
        print("3. Run: ./scripts/migrate.sh --dry-run (to test)")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")

if __name__ == "__main__":
    main() 