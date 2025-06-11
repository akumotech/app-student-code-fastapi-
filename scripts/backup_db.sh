#!/bin/bash

# 📦 Database Backup Script
# Creates backups with automatic cleanup and restore functionality

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
COMPRESS=true

echo -e "${BLUE}📦 Database Backup Script${NC}"
echo "=========================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable is not set${NC}"
    echo "Set it with: export DATABASE_URL='postgresql://user:pass@localhost/dbname'"
    exit 1
fi

# Function to create backup
create_backup() {
    local backup_type="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_base="$BACKUP_DIR/backup_${backup_type}_${timestamp}"
    
    echo -e "${YELLOW}📦 Creating $backup_type backup...${NC}"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    if [ "$COMPRESS" = true ]; then
        local backup_file="${backup_base}.sql.gz"
        if pg_dump "$DATABASE_URL" | gzip > "$backup_file"; then
            echo -e "${GREEN}✅ Compressed backup created: $backup_file${NC}"
            echo "Size: $(du -h "$backup_file" | cut -f1)"
        else
            echo -e "${RED}❌ Failed to create backup!${NC}"
            exit 1
        fi
    else
        local backup_file="${backup_base}.sql"
        if pg_dump "$DATABASE_URL" > "$backup_file"; then
            echo -e "${GREEN}✅ Backup created: $backup_file${NC}"
            echo "Size: $(du -h "$backup_file" | cut -f1)"
        else
            echo -e "${RED}❌ Failed to create backup!${NC}"
            exit 1
        fi
    fi
    
    echo "$backup_file"  # Return the backup file path
}

# Function to clean old backups
cleanup_backups() {
    local backup_pattern="$1"
    echo -e "${BLUE}🧹 Cleaning old backups...${NC}"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}⚠️  Backup directory doesn't exist${NC}"
        return
    fi
    
    # Count backups
    local backup_count=$(ls -1 "$BACKUP_DIR"/$backup_pattern 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        echo "Found $backup_count backups, keeping last $MAX_BACKUPS"
        ls -t "$BACKUP_DIR"/$backup_pattern | tail -n +$((MAX_BACKUPS + 1)) | while read file; do
            echo "Removing: $(basename "$file")"
            rm "$file"
        done
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    else
        echo "Found $backup_count backups (within limit of $MAX_BACKUPS)"
    fi
}

# Function to list backups
list_backups() {
    echo -e "${BLUE}📋 Available backups:${NC}"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}⚠️  No backup directory found${NC}"
        return
    fi
    
    local backups=($(ls -t "$BACKUP_DIR"/backup_*.sql* 2>/dev/null || true))
    
    if [ ${#backups[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No backups found${NC}"
        return
    fi
    
    echo ""
    printf "%-3s %-30s %-12s %-10s\n" "#" "Filename" "Size" "Date"
    echo "------------------------------------------------"
    
    for i in "${!backups[@]}"; do
        local file="${backups[$i]}"
        local filename=$(basename "$file")
        local size=$(du -h "$file" | cut -f1)
        local date=$(stat -c %y "$file" | cut -d' ' -f1)
        printf "%-3s %-30s %-12s %-10s\n" "$((i+1))" "$filename" "$size" "$date"
    done
}

# Function to restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}❌ Backup file not found: $backup_file${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}⚠️  WARNING: This will REPLACE the current database!${NC}"
    echo "Backup file: $backup_file"
    echo "Target database: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"
    echo ""
    read -p "Are you absolutely sure? Type 'RESTORE' to continue: " confirmation
    
    if [ "$confirmation" != "RESTORE" ]; then
        echo -e "${BLUE}🛑 Restore cancelled${NC}"
        exit 0
    fi
    
    echo -e "${BLUE}🔄 Restoring database...${NC}"
    
    # Check if file is compressed
    if [[ "$backup_file" == *.gz ]]; then
        if gunzip -c "$backup_file" | psql "$DATABASE_URL"; then
            echo -e "${GREEN}✅ Database restored successfully from compressed backup${NC}"
        else
            echo -e "${RED}❌ Failed to restore database!${NC}"
            exit 1
        fi
    else
        if psql "$DATABASE_URL" < "$backup_file"; then
            echo -e "${GREEN}✅ Database restored successfully${NC}"
        else
            echo -e "${RED}❌ Failed to restore database!${NC}"
            exit 1
        fi
    fi
}

# Function to show database info
show_db_info() {
    echo -e "${BLUE}🗄️  Database Information:${NC}"
    
    # Extract database components
    local db_url="$DATABASE_URL"
    local db_name=$(echo "$db_url" | sed -n 's|.*/\([^?]*\).*|\1|p')
    local db_host=$(echo "$db_url" | sed -n 's|.*://[^@]*@\([^:/]*\).*|\1|p')
    local db_port=$(echo "$db_url" | sed -n 's|.*://[^@]*@[^:]*:\([^/]*\)/.*|\1|p')
    
    echo "Database: $db_name"
    echo "Host: $db_host"
    echo "Port: ${db_port:-5432}"
    echo ""
    
    # Get database size
    local size_query="SELECT pg_size_pretty(pg_database_size('$db_name'));"
    local db_size=$(psql "$DATABASE_URL" -t -c "$size_query" 2>/dev/null | xargs || echo "Unknown")
    echo "Database size: $db_size"
    
    # Get table count
    local table_query="SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
    local table_count=$(psql "$DATABASE_URL" -t -c "$table_query" 2>/dev/null | xargs || echo "Unknown")
    echo "Tables: $table_count"
}

# Main execution
main() {
    local command="backup"
    local backup_type="manual"
    local restore_file=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            backup)
                command="backup"
                shift
                ;;
            list)
                command="list"
                shift
                ;;
            restore)
                command="restore"
                shift
                if [[ $# -gt 0 ]]; then
                    restore_file="$1"
                    shift
                fi
                ;;
            cleanup)
                command="cleanup"
                shift
                ;;
            info)
                command="info"
                shift
                ;;
            --auto)
                backup_type="auto"
                shift
                ;;
            --no-compress)
                COMPRESS=false
                shift
                ;;
            --max-backups)
                if [[ $# -gt 1 ]]; then
                    MAX_BACKUPS="$2"
                    shift 2
                else
                    echo -e "${RED}❌ --max-backups requires a number${NC}"
                    exit 1
                fi
                ;;
            --help|-h)
                echo "Usage: $0 [COMMAND] [OPTIONS]"
                echo ""
                echo "Commands:"
                echo "  backup     Create a new backup (default)"
                echo "  list       List available backups"
                echo "  restore    Restore from backup file"
                echo "  cleanup    Clean old backups"
                echo "  info       Show database information"
                echo ""
                echo "Options:"
                echo "  --auto             Mark backup as automatic"
                echo "  --no-compress      Don't compress backup files"
                echo "  --max-backups N    Keep maximum N backups (default: 10)"
                echo "  --help, -h         Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0 backup                    # Create manual backup"
                echo "  $0 backup --auto             # Create automatic backup"
                echo "  $0 list                      # List all backups"
                echo "  $0 restore backup_file.sql   # Restore from specific file"
                echo "  $0 cleanup                   # Clean old backups"
                exit 0
                ;;
            *)
                if [ "$command" = "restore" ] && [ -z "$restore_file" ]; then
                    restore_file="$1"
                    shift
                else
                    echo -e "${RED}❌ Unknown option: $1${NC}"
                    echo "Use --help for usage information"
                    exit 1
                fi
                ;;
        esac
    done
    
    case "$command" in
        backup)
            show_db_info
            backup_file=$(create_backup "$backup_type")
            cleanup_backups "backup_*.sql*"
            echo ""
            echo -e "${GREEN}🎉 Backup completed successfully!${NC}"
            echo "Backup file: $backup_file"
            ;;
        list)
            list_backups
            ;;
        restore)
            if [ -z "$restore_file" ]; then
                echo -e "${RED}❌ Please specify a backup file to restore${NC}"
                echo "Usage: $0 restore <backup_file>"
                echo ""
                list_backups
                exit 1
            fi
            
            # If relative path, assume it's in backup directory
            if [[ "$restore_file" != /* ]]; then
                restore_file="$BACKUP_DIR/$restore_file"
            fi
            
            restore_backup "$restore_file"
            ;;
        cleanup)
            cleanup_backups "backup_*.sql*"
            ;;
        info)
            show_db_info
            ;;
    esac
}

# Run main function
main "$@" 