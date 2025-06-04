#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting FastAPI application with Alembic migrations...${NC}"

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
    
    if ! alembic current >/dev/null 2>&1; then
        echo -e "${YELLOW}📋 No migration history found. Checking if database has tables...${NC}"
        
        table_count=$(psql "$DATABASE_URL" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
        
        if [ "$table_count" -gt 0 ]; then
            echo -e "${YELLOW}🏷️  Existing tables found. Marking current state as migrated...${NC}"
            alembic stamp head
        else
            echo -e "${BLUE}🆕 Fresh database detected. Running initial migration...${NC}"
            alembic upgrade head
        fi
    else
        echo -e "${BLUE}🔄 Applying pending migrations...${NC}"
        alembic upgrade head
    fi
    
    echo -e "${GREEN}✅ Database migrations completed!${NC}"
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