# 🚀 Database Migration Quick Start Guide

**Goal:** Transition from auto-creating tables to proper Alembic migrations in 30 minutes.

## ⏱️ Quick Implementation (30 minutes)

### Step 1: Install & Setup (5 minutes)

```bash
# 1. Install Alembic
pip install alembic
echo "alembic==1.13.1" >> requirements.txt

# 2. Initialize Alembic
alembic init alembic

# 3. Make scripts executable
chmod +x scripts/migrate.sh scripts/backup_db.sh
```

### Step 2: Configure Alembic (10 minutes)

**Edit `alembic.ini`:**

```ini
# Comment out or remove the sqlalchemy.url line:
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

**Replace content of `alembic/env.py`:**

```python
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import ALL your models (critical!)
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

from sqlmodel import SQLModel

config = context.config

# Set database URL from environment
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL")
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Step 3: Create Initial Migration (5 minutes)

```bash
# ⚠️ BACKUP FIRST!
./scripts/backup_db.sh backup

# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Mark current database state (DON'T actually run the migration)
alembic stamp head
```

### Step 4: Update Application Code (5 minutes)

**Update `app/auth/database.py`:**

```python
from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO_SQL)

def create_db_and_tables():
    """DEPRECATED: Use Alembic migrations instead"""
    if settings.ENVIRONMENT == "test":
        SQLModel.metadata.create_all(engine)
    else:
        raise RuntimeError("Auto-creation disabled. Use 'alembic upgrade head'")

def get_session():
    with Session(engine) as session:
        yield session
```

**Update `app/main.py` startup function:**

```python
@app.on_event("startup")
def on_startup():
    # Remove: create_db_and_tables()
    start_scheduler()
    # Database migrations handled separately
```

**Add to `app/config.py`:**

```python
class Settings(BaseSettings):
    # ... existing fields ...
    ENVIRONMENT: str = "development"  # Add this line
```

### Step 5: Test Migration (5 minutes)

```bash
# Test the migration process
./scripts/migrate.sh --dry-run

# If everything looks good, you're ready!
echo "✅ Migration setup complete!"
```

---

## 🔥 Daily Workflow (After Setup)

### Making Schema Changes:

```bash
# 1. Modify your models in code
# 2. Generate migration
alembic revision --autogenerate -m "Add new field to User"

# 3. Review the generated migration file
# 4. Apply migration
./scripts/migrate.sh
```

### Emergency Rollback:

```bash
# Rollback one migration
alembic downgrade -1

# Or restore from backup
./scripts/backup_db.sh restore backup_file.sql.gz
```

---

## 🛠️ Script Usage

### Migration Script:

```bash
./scripts/migrate.sh                 # Full migration with backup
./scripts/migrate.sh --dry-run       # Preview what would happen
./scripts/migrate.sh --skip-backup   # Skip backup (not recommended)
```

### Backup Script:

```bash
./scripts/backup_db.sh backup        # Create backup
./scripts/backup_db.sh list          # List all backups
./scripts/backup_db.sh info          # Show database info
./scripts/backup_db.sh restore file  # Restore from backup
```

---

## ⚡ Common Commands Reference

```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Check for pending migrations
alembic check

# Generate new migration
alembic revision --autogenerate -m "Description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Go to specific revision
alembic upgrade <revision_id>
```

---

## 🚨 IMPORTANT NOTES

1. **ALWAYS backup before production migrations**
2. **Review autogenerated migrations** - they're not perfect
3. **Test on staging first**
4. **Never edit applied migration files** - create new ones
5. **Coordinate with team** on migration conflicts

---

## 🆘 Troubleshooting

### "No module named 'app.xyz.models'"

- Make sure all model imports are in `alembic/env.py`
- Check your PYTHONPATH

### "Target database is not up to date"

- Run `alembic stamp head` if transitioning from auto-creation
- Check `alembic current` vs `alembic show head`

### Migration conflicts

- Use `alembic merge` to resolve conflicts
- Coordinate with team on migration order

### Rollback needed

- `alembic downgrade -1` for one step back
- Use backup scripts for full restore

---

## 📞 Next Steps After Setup

1. **Remove auto-creation** from production deployments
2. **Update CI/CD pipeline** to run migrations
3. **Train team** on new workflow
4. **Schedule regular backups**
5. **Monitor migration performance**

**🎉 You're now using professional database management!**
