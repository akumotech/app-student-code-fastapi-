#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment variables from .env file
load_env_file() {
    if [ -f ".env" ]; then
        echo -e "${BLUE}📄 Loading environment variables from .env file...${NC}"
        # Export all variables from .env file, ignoring comments and empty lines
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
        echo -e "${GREEN}✅ Environment variables loaded successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env file found. Using system environment variables...${NC}"
    fi
}

# Validate required environment variables
validate_env_vars() {
    echo -e "${BLUE}🔍 Validating required environment variables...${NC}"
    
    required_vars=("SECRET_KEY" "WAKATIME_CLIENT_ID" "WAKATIME_CLIENT_SECRET" "FRONTEND_DOMAIN" "FERNET_KEY" "REDIRECT_URI")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required environment variables:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "${RED}   - $var${NC}"
        done
        echo -e "${RED}Please check your .env file or environment configuration.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All required environment variables are set${NC}"
}

echo -e "${BLUE}Starting FastAPI application with Alembic migrations...${NC}"

# Load environment variables first
load_env_file
validate_env_vars

wait_for_database() {
    echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"

    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}❌ DATABASE_URL environment variable is not set${NC}"
        exit 1
    fi
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -d "$DATABASE_URL" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Database is ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}🔄 Attempt $attempt/$max_attempts: Database not ready, waiting 2 seconds...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Database connection timeout after $max_attempts attempts${NC}"
    exit 1
}

run_migrations() {

    ## refer to database_migration_plan.md for more details

    echo -e "${BLUE}🗄️ Running database migrations...${NC}"
    
    # Check if alembic version table exists to determine migration strategy
    alembic_table_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');" 2>/dev/null | xargs || echo "f")
    
    if [ "$alembic_table_exists" = "f" ]; then
        echo -e "${YELLOW}📋 No migration history found. Checking database state...${NC}"
        
        # Check if core tables exist (user table is our foundation)
        user_table_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user');" 2>/dev/null | xargs || echo "f")
        
        if [ "$user_table_exists" = "t" ]; then
            echo -e "${YELLOW}🏗️  Existing database detected. Using safe migration approach...${NC}"
            
            # For existing databases, only create missing tables safely
            python -c "
import os
from sqlmodel import SQLModel, create_engine, text
from app.auth.models import *
from app.students.models import *
from app.integrations.model import *
from app.admin.models import *

try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Get existing tables
    with engine.connect() as conn:
        result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \"public\"'))
        existing_tables = {row[0] for row in result}
    
    # Get required tables
    required_tables = set(SQLModel.metadata.tables.keys())
    missing_tables = required_tables - existing_tables
    
    if missing_tables:
        print(f'📝 Creating missing tables: {missing_tables}')
        # Create only missing tables with checkfirst=True for safety
        for table_name in missing_tables:
            table = SQLModel.metadata.tables[table_name]
            table.create(engine, checkfirst=True)
        print('✅ Missing tables created successfully')
    else:
        print('✅ All required tables already exist')
        
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"
            
            # Mark the current schema as migrated to avoid re-running migrations
            echo -e "${YELLOW}🏷️  Marking current state as migrated...${NC}"
            alembic stamp head
            
        else
            echo -e "${BLUE}🆕 Fresh database detected. Running full migration...${NC}"
            alembic upgrade head
        fi
    else
        echo -e "${BLUE}🔄 Database has migration history. Applying pending migrations...${NC}"
        alembic upgrade head
    fi
    
    echo -e "${GREEN}✅ Database migrations completed safely!${NC}"
}

start_application() {
    echo -e "${BLUE}🚀 Starting FastAPI application...${NC}"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
}

main() {
    if [ "$1" = "--skip-migrations" ]; then
        echo -e "${YELLOW}⚠️  Skipping migrations as requested${NC}"
        start_application
        return
    fi
    
    if [ "$1" = "--migrate-only" ]; then
        echo -e "${BLUE}🔧 Running migrations only (not starting app)${NC}"
        wait_for_database
        run_migrations
        echo -e "${GREEN}🎉 Migrations completed. Exiting.${NC}"
        return
    fi
    
    wait_for_database
    run_migrations
    start_application
}

trap 'echo -e "${YELLOW}Received termination signal. Shutting down gracefully...${NC}"; exit 0' SIGTERM SIGINT

main "$@" 