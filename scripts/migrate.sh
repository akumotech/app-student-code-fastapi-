#!/bin/bash

# 🗄️ Database Migration Script
# This script safely applies Alembic migrations with backups and checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups"
MAX_BACKUPS=10

echo -e "${BLUE}🗄️  Database Migration Script${NC}"
echo "=================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable is not set${NC}"
    echo "Set it with: export DATABASE_URL='postgresql://user:pass@localhost/dbname'"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to create backup
create_backup() {
    echo -e "${YELLOW}📦 Creating database backup...${NC}"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if pg_dump "$DATABASE_URL" > "$BACKUP_FILE"; then
        echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Failed to create backup!${NC}"
        exit 1
    fi
    
    # Clean old backups (keep only last MAX_BACKUPS)
    backup_count=$(ls -1 "$BACKUP_DIR"/backup_*.sql 2>/dev/null | wc -l)
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        echo -e "${YELLOW}🧹 Cleaning old backups (keeping last $MAX_BACKUPS)...${NC}"
        ls -t "$BACKUP_DIR"/backup_*.sql | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
    fi
}

# Function to check migration status
check_migration_status() {
    echo -e "${BLUE}🔍 Checking current migration status...${NC}"
    
    # Check if alembic is available
    if ! command -v alembic &> /dev/null; then
        echo -e "${RED}❌ ERROR: Alembic is not installed${NC}"
        echo "Install with: pip install alembic"
        exit 1
    fi
    
    # Show current revision
    echo "Current database revision:"
    alembic current || {
        echo -e "${YELLOW}⚠️  No migration history found. This might be the first migration.${NC}"
    }
    
    # Show head revision
    echo -e "\nTarget revision (head):"
    alembic show head || {
        echo -e "${YELLOW}⚠️  No migrations found in versions directory.${NC}"
    }
}

# Function to show pending migrations
show_pending_migrations() {
    echo -e "${BLUE}📋 Checking for pending migrations...${NC}"
    
    # Get current and head revisions
    CURRENT=$(alembic current --verbose 2>/dev/null | grep "Rev:" | cut -d' ' -f2 || echo "")
    HEAD=$(alembic show head 2>/dev/null | grep "Rev:" | cut -d' ' -f2 || echo "")
    
    if [ "$CURRENT" = "$HEAD" ] && [ -n "$CURRENT" ]; then
        echo -e "${GREEN}✅ Database is up to date (revision: $CURRENT)${NC}"
        return 0
    else
        echo -e "${YELLOW}📌 Pending migrations detected${NC}"
        if [ -n "$CURRENT" ]; then
            echo "Current: $CURRENT"
        else
            echo "Current: None (fresh database)"
        fi
        if [ -n "$HEAD" ]; then
            echo "Target:  $HEAD"
        else
            echo "Target:  None (no migrations found)"
        fi
        return 1
    fi
}

# Function to apply migrations
apply_migrations() {
    echo -e "${BLUE}🚀 Applying migrations...${NC}"
    
    if alembic upgrade head; then
        echo -e "${GREEN}✅ All migrations applied successfully!${NC}"
    else
        echo -e "${RED}❌ Migration failed!${NC}"
        echo -e "${YELLOW}💡 You can rollback using: alembic downgrade -1${NC}"
        echo -e "${YELLOW}💡 Or restore from backup: $BACKUP_FILE${NC}"
        exit 1
    fi
}

# Function to verify migration
verify_migration() {
    echo -e "${BLUE}🔎 Verifying migration...${NC}"
    
    # Check final status
    FINAL_REVISION=$(alembic current --verbose 2>/dev/null | grep "Rev:" | cut -d' ' -f2 || echo "")
    TARGET_REVISION=$(alembic show head 2>/dev/null | grep "Rev:" | cut -d' ' -f2 || echo "")
    
    if [ "$FINAL_REVISION" = "$TARGET_REVISION" ] && [ -n "$FINAL_REVISION" ]; then
        echo -e "${GREEN}✅ Migration verification successful!${NC}"
        echo "Current revision: $FINAL_REVISION"
    else
        echo -e "${YELLOW}⚠️  Migration verification inconclusive${NC}"
        echo "Current: $FINAL_REVISION"
        echo "Expected: $TARGET_REVISION"
    fi
}

# Main execution
main() {
    # Parse command line arguments
    SKIP_BACKUP=false
    DRY_RUN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-backup    Skip database backup (not recommended)"
                echo "  --dry-run        Show what would be done without applying"
                echo "  --help, -h       Show this help message"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Step 1: Check migration status
    check_migration_status
    
    # Step 2: Show pending migrations
    if show_pending_migrations; then
        echo -e "${GREEN}🎉 No migrations needed. Database is up to date!${NC}"
        exit 0
    fi
    
    # For dry run, stop here
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}🏃 Dry run complete. Use without --dry-run to apply migrations.${NC}"
        exit 0
    fi
    
    # Step 3: Create backup (unless skipped)
    if [ "$SKIP_BACKUP" = false ]; then
        create_backup
    else
        echo -e "${YELLOW}⚠️  Skipping backup as requested${NC}"
    fi
    
    # Step 4: Confirm before proceeding
    echo ""
    echo -e "${YELLOW}⚠️  About to apply migrations to database${NC}"
    echo "Database URL: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"  # Hide password
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🛑 Migration cancelled by user${NC}"
        exit 0
    fi
    
    # Step 5: Apply migrations
    apply_migrations
    
    # Step 6: Verify migration
    verify_migration
    
    echo ""
    echo -e "${GREEN}🎉 Migration completed successfully!${NC}"
    echo -e "${BLUE}💡 Next steps:${NC}"
    echo "   • Test your application thoroughly"
    echo "   • Monitor logs for any issues"
    echo "   • Keep the backup file: $BACKUP_FILE"
}

# Run main function
main "$@" 