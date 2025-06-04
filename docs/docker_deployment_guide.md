# 🐳 Docker Deployment Guide with Alembic Migrations

## 📋 **What's New in the Docker Setup**

Your Docker configuration now includes:

- **Automatic database migrations** on startup
- **Database health checks** and connection waiting
- **Proper service dependencies** with health conditions
- **Backup directory mounting** for database backups
- **Flexible migration options** for different deployment scenarios

---

## 🚀 **Quick Start**

### **Standard Deployment:**

```bash
# Build and start all services
docker-compose up --build

# The backend will automatically:
# 1. Wait for database to be ready
# 2. Run pending migrations
# 3. Start the FastAPI application
```

### **Migration-Only Deployment:**

```bash
# Run migrations only (useful for production deployments)
docker-compose --profile migration up migration

# Or build and run migration in one step
docker-compose build backend
docker-compose --profile migration run --rm migration
```

---

## 🔧 **Service Breakdown**

### **Database Service (`db`):**

```yaml
- Image: postgres:13
- Health checks every 5 seconds
- Persistent data storage with named volume
- Exposed on port 5432
```

### **Backend Service (`backend`):**

```yaml
- Automatically built from Dockerfile
- Waits for database health check
- Runs migrations on startup
- Mounts backup directory for database dumps
- Exposed on port 8000
```

### **Migration Service (`migration`):**

```yaml
- Same image as backend
- Only runs migrations, then exits
- Activated with --profile migration
- Useful for production deployments
```

---

## 🎯 **Deployment Scenarios**

### **1. Development Environment:**

```bash
# Start everything with hot reload
docker-compose up --build

# View logs
docker-compose logs -f backend

# Access application at http://localhost:8000
```

### **2. Production Deployment:**

```bash
# Step 1: Run migrations first (safer)
docker-compose --profile migration up migration

# Step 2: Start application services
docker-compose up --build -d backend frontend

# Step 3: Verify deployment
docker-compose ps
docker-compose logs backend
```

### **3. Database-Only Setup:**

```bash
# Start only the database
docker-compose up db

# Connect from host
psql postgresql://postgres:redhat1234@localhost:5432/postgres
```

---

## 🛠️ **Docker Entrypoint Options**

The `docker-entrypoint.sh` script supports several modes:

### **Default Mode (Migrations + App):**

```bash
docker run fastapi-student-view
# Waits for DB → Runs migrations → Starts app
```

### **Skip Migrations:**

```bash
docker run fastapi-student-view --skip-migrations
# Starts app immediately (for debugging)
```

### **Migrations Only:**

```bash
docker run fastapi-student-view --migrate-only
# Runs migrations only, then exits
```

---

## 📁 **File Structure in Container**

```
/app/
├── app/                    # Application code
├── alembic/               # Migration files
│   ├── versions/          # Migration scripts
│   └── env.py            # Alembic configuration
├── alembic.ini           # Alembic settings
├── scripts/              # Migration and backup scripts
│   ├── migrate.sh        # Migration script
│   └── backup_db.sh      # Backup script
├── docker-entrypoint.sh  # Startup script
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

---

## 🔍 **Debugging and Troubleshooting**

### **Check Migration Status:**

```bash
# Connect to running container
docker-compose exec backend bash

# Check current migration
alembic current

# View migration history
alembic history

# Manual migration (if needed)
alembic upgrade head
```

### **Database Connection Issues:**

```bash
# Check database health
docker-compose exec db pg_isready -U postgres

# Check backend logs
docker-compose logs backend

# Test database connection
docker-compose exec backend psql $DATABASE_URL -c "SELECT 1"
```

### **View Container Logs:**

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f backend
```

---

## 🔄 **Update and Rollback Procedures**

### **Standard Update:**

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and restart
docker-compose down
docker-compose up --build

# Migrations run automatically on startup
```

### **Safe Production Update:**

```bash
# 1. Backup database
docker-compose exec backend ./scripts/backup_db.sh backup

# 2. Test migration separately
docker-compose --profile migration up migration

# 3. If migration succeeds, restart services
docker-compose up --build -d
```

### **Emergency Rollback:**

```bash
# 1. Stop services
docker-compose down

# 2. Rollback migration in container
docker-compose run --rm backend alembic downgrade -1

# 3. Restart with previous code version
git checkout previous-commit
docker-compose up --build -d
```

---

## 🛡️ **Production Considerations**

### **Environment Variables:**

```bash
# Required variables in production .env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
FRONTEND_DOMAIN=https://your-domain.com
ENVIRONMENT=production
```

### **Security:**

- Change default database passwords
- Use secrets management for production
- Configure proper CORS settings
- Enable SSL/TLS for database connections

### **Monitoring:**

```bash
# Container health
docker-compose ps

# Resource usage
docker stats

# Database size and performance
docker-compose exec backend ./scripts/backup_db.sh info
```

---

## 📊 **Useful Commands Reference**

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Rebuild specific service
docker-compose build backend

# Run migrations only
docker-compose --profile migration up migration

# Connect to running backend
docker-compose exec backend bash

# View logs
docker-compose logs -f backend

# Clean up unused images
docker system prune
```

---

## 🎯 **Migration Workflow in Docker**

1. **Developer makes model changes**
2. **Generate migration locally:**
   ```bash
   alembic revision --autogenerate -m "Description"
   ```
3. **Commit migration file to git**
4. **Deploy to production:**
   ```bash
   docker-compose --profile migration up migration  # Safe
   docker-compose up --build -d                     # Deploy
   ```

---

**🎉 Your Docker setup is now production-ready with automated database migrations!**
