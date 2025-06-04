# 🗄️ Database Migration Plan: From Auto-Creation to Alembic

**Current State:** FastAPI auto-creates tables via `SQLModel.metadata.create_all()`  
**Target State:** Alembic-managed database migrations with version control  
**Timeline:** 1-2 days implementation + ongoing workflow

## 🚨 Why Change is Critical

### Current Problems:

- **No version control** for database schema changes
- **Data loss risk** when columns/tables are modified
- **Production deployment issues** without rollback capability
- **Team coordination problems** with schema conflicts
- **No migration history** or change tracking

### Benefits of Alembic:

- **Versioned migrations** with up/down capabilities
- **Safe production deployments** with rollback options
- **Team collaboration** with shared migration files
- **Data preservation** during schema changes
- **Audit trail** of all database changes

---

## 📋 Migration Plan Overview

### Phase 1: Setup Alembic (Day 1)

1. Install Alembic and configure
2. Generate initial migration from current schema
3. Test migration process
4. Update deployment scripts

### Phase 2: Workflow Implementation (Day 2)

1. Remove auto-creation code
2. Update development workflow
3. Create production migration strategy
4. Team documentation and training

---

## 🛠️ Phase 1: Alembic Setup

### Step 1: Install Alembic

```bash
pip install alembic
# Add to requirements.txt
echo "alembic==1.13.1" >> requirements.txt
```

### Step 2: Initialize Alembic

```bash
# From project root
alembic init alembic
```

This creates:

```
alembic/
├── versions/          # Migration files
├── env.py            # Alembic environment config
├── script.py.mako    # Migration template
└── alembic.ini       # Alembic configuration
```

### Step 3: Configure Alembic

**Edit `alembic.ini`:**

```ini
# Replace the sqlalchemy.url line with:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# We'll set this via environment variable instead
# sqlalchemy.url =
```

**Edit `alembic/env.py`:**

```python
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

# Import your SQLModel
from sqlmodel import SQLModel

# this is the Alembic Config object
config = context.config

# Set the database URL from environment
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dbname")
)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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

### Step 4: Generate Initial Migration

**⚠️ CRITICAL: Backup your database first!**

```bash
# Create database backup
pg_dump your_database > backup_before_migration.sql

# Generate initial migration from current schema
alembic revision --autogenerate -m "Initial migration"
```

This creates a migration file in `alembic/versions/` that represents your current schema.

### Step 5: Mark Current State

Since your database already has the tables, you need to mark the initial migration as already applied:

```bash
# Mark the initial migration as applied (don't actually run it)
alembic stamp head
```

---

## 🔧 Phase 2: Update Application Code

### Step 1: Remove Auto-Creation

**Update `app/auth/database.py`:**

```python
from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO_SQL)

# Remove the create_db_and_tables function or make it optional
def create_db_and_tables():
    """
    DEPRECATED: Use Alembic migrations instead
    Only use this for testing environments
    """
    if settings.ENVIRONMENT == "test":
        SQLModel.metadata.create_all(engine)
    else:
        raise RuntimeError(
            "Auto-creation disabled. Use 'alembic upgrade head' instead."
        )

def get_session():
    with Session(engine) as session:
        yield session
```

### Step 2: Update Main Application

**Update `app/main.py`:**

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.auth.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.openapi.utils import get_openapi

## local imports
# Remove: from app.auth.database import create_db_and_tables
from app.integrations.routes import router as integrations_router
from app.students.routes import router as students_router
from app.admin.routes import router as admin_router
from app.auth.utils import verify_access_token
from app.integrations.scheduler import start_scheduler
from app.config import settings

# ... rest of your existing code ...

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Remove: create_db_and_tables()
    start_scheduler()
    # Database should be migrated separately using Alembic

# ... rest of your existing code ...
```

### Step 3: Update Configuration

**Add to `app/config.py`:**

```python
import os
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    DATABASE_ECHO_SQL: bool = True
    WAKATIME_CLIENT_ID: str
    WAKATIME_CLIENT_SECRET: str
    FRONTEND_DOMAIN: str
    FERNET_KEY: str
    REDIRECT_URI: str

    # Add environment setting
    ENVIRONMENT: str = "development"  # "development", "production", "test"

    # Cookie Settings
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token_cookie"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY.encode("utf-8"))

settings = Settings()
```

---

## 🚀 Migration Workflow

### Development Workflow

1. **Make Model Changes:**

   ```python
   # Example: Add new field to User model
   class User(SQLModel, table=True):
       id: Optional[int] = Field(default=None, primary_key=True)
       email: EmailStr = Field(unique=True, index=True)
       name: str
       # New field
       created_at: datetime = Field(default_factory=datetime.utcnow)
   ```

2. **Generate Migration:**

   ```bash
   alembic revision --autogenerate -m "Add created_at to User table"
   ```

3. **Review Migration:**

   ```python
   # Check the generated migration file
   # Make sure it looks correct before applying
   ```

4. **Apply Migration:**
   ```bash
   alembic upgrade head
   ```

### Production Deployment

1. **Pre-deployment:**

   ```bash
   # Backup production database
   pg_dump production_db > backup_$(date +%Y%m%d_%H%M%S).sql

   # Test migration on staging
   alembic upgrade head
   ```

2. **Deployment:**

   ```bash
   # Deploy application code first
   git pull origin main

   # Apply migrations
   alembic upgrade head

   # Start/restart application
   systemctl restart your-app
   ```

3. **Rollback (if needed):**

   ```bash
   # Rollback one migration
   alembic downgrade -1

   # Rollback to specific revision
   alembic downgrade revision_id
   ```

---

## 📁 Updated Project Structure

```
your-project/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_migration.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── app/
│   ├── auth/
│   │   ├── database.py  # Updated without auto-creation
│   │   └── models.py
│   ├── students/
│   ├── integrations/
│   └── main.py  # Updated without startup table creation
├── requirements.txt  # Now includes alembic
└── scripts/
    ├── migrate.sh      # New deployment script
    └── backup_db.sh    # New backup script
```

---

## 🛡️ Safety Scripts

### Create `scripts/migrate.sh`:

```bash
#!/bin/bash
set -e

echo "🗄️ Starting database migration..."

# Backup first
echo "📦 Creating backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump $DATABASE_URL > $BACKUP_FILE
echo "✅ Backup created: $BACKUP_FILE"

# Check current migration status
echo "🔍 Current migration status:"
alembic current

# Show pending migrations
echo "📋 Pending migrations:"
alembic show head

# Apply migrations
echo "🚀 Applying migrations..."
alembic upgrade head

echo "✅ Migration completed successfully!"
```

### Create `scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump $DATABASE_URL > $BACKUP_FILE

echo "✅ Database backed up to: $BACKUP_FILE"

# Keep only last 10 backups
ls -t $BACKUP_DIR/backup_*.sql | tail -n +11 | xargs -r rm
```

---

## 🔄 Team Workflow

### For New Features:

1. **Create feature branch**
2. **Modify models**
3. **Generate migration:** `alembic revision --autogenerate -m "Description"`
4. **Test migration locally**
5. **Commit migration file with code changes**
6. **Code review includes migration review**
7. **Deploy to staging and test**
8. **Deploy to production**

### Migration Conflicts:

```bash
# When two branches have conflicting migrations
alembic merge -m "Merge migrations" revision1 revision2
```

---

## 🧪 Testing Strategy

### Unit Tests:

```python
# tests/test_migrations.py
import pytest
from alembic import command
from alembic.config import Config
from sqlmodel import Session, create_engine

def test_migration_up_down():
    """Test that migrations can be applied and rolled back"""
    # Apply all migrations
    command.upgrade(alembic_cfg, "head")

    # Rollback one
    command.downgrade(alembic_cfg, "-1")

    # Apply again
    command.upgrade(alembic_cfg, "head")
```

### Integration Tests:

```python
# Test that application works after migration
def test_app_after_migration():
    # Apply migrations
    command.upgrade(alembic_cfg, "head")

    # Test API endpoints
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 200
```

---

## 📊 Monitoring & Maintenance

### Regular Tasks:

- **Weekly:** Review migration files in PRs
- **Monthly:** Clean old backup files
- **Quarterly:** Review and optimize slow migrations

### Database Health Checks:

```bash
# Check migration status
alembic current

# Check for pending migrations
alembic check

# Show migration history
alembic history
```

---

## 🚨 Common Pitfalls to Avoid

1. **Never edit applied migration files** - create new ones instead
2. **Always backup before production migrations**
3. **Test migrations on staging first**
4. **Review autogenerated migrations** - they're not always perfect
5. **Don't skip migration files** - apply them in order
6. **Coordinate with team** on migration conflicts

---

## 🎯 Implementation Checklist

### Setup Phase:

- [ ] Install Alembic
- [ ] Configure `alembic/env.py` with your models
- [ ] Generate initial migration
- [ ] Mark current database state with `alembic stamp head`
- [ ] Test migration on development database

### Code Changes:

- [ ] Remove `create_db_and_tables()` from startup
- [ ] Update deployment scripts
- [ ] Add environment configuration
- [ ] Create backup and migration scripts

### Team Preparation:

- [ ] Document new workflow
- [ ] Train team on Alembic commands
- [ ] Set up CI/CD pipeline integration
- [ ] Establish migration review process

### Production Deployment:

- [ ] Backup production database
- [ ] Test migration on staging
- [ ] Schedule maintenance window
- [ ] Apply migration during deployment
- [ ] Monitor application health

---

**Next Steps:** Start with Phase 1 setup in your development environment. Once you're comfortable with the workflow, schedule a maintenance window to apply this to production.
