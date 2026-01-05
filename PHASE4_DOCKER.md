# Phase 4: Docker & Multi-Container Orchestration

## Overview

Phase 4 containerizes the entire Code Intelligence Search Engine using Docker and Docker Compose. This enables:

- **Consistent deployment** across development, staging, and production
- **Isolated services** running independently with proper networking
- **Easy scaling** with Docker Compose or Kubernetes
- **Production-ready** multi-stage builds with optimized images
- **Zero-configuration deployment** - everything is self-contained

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Network (search-engine)              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │    Frontend      │  │    Backend       │                 │
│  │   (Nginx/SPA)    │  │   (FastAPI)      │                 │
│  │   Port 80, 5173  │  │   Port 8000      │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                             │
│           └─────────────────────┴─────────┐                  │
│                                           │                  │
│                    ┌──────────────────────┴──────┐            │
│                    │                             │            │
│            ┌───────▼─────────┐       ┌──────────▼──┐         │
│            │    Qdrant       │       │    Redis    │         │
│            │  (Vector DB)    │       │   (Cache)   │         │
│            │   Port 6333     │       │  Port 6379  │         │
│            └─────────────────┘       └─────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Files Created

### Backend
- **`backend/Dockerfile`** - Multi-stage build for FastAPI
  - Stage 1: Builder - compile dependencies with pip
  - Stage 2: Runtime - minimal Python image with wheels
  - Non-root user for security
  - Health checks enabled
  - 4 worker processes in production

- **`backend/.dockerignore`** - Reduces image size
  - Excludes: `__pycache__`, `.git`, `venv`, test files

### Frontend
- **`frontend/Dockerfile`** - Multi-stage build for React + Vite
  - Stage 1: Builder - Node.js to build React app
  - Stage 2: Runtime - Alpine Nginx to serve static files
  - Gzip compression enabled
  - Security headers configured
  - API proxy configured for backend

- **`frontend/nginx.conf`** - Nginx configuration
  - SPA routing (serve index.html for all routes)
  - Static asset caching (1 year expiry)
  - API proxy to backend on `/api`
  - Health check endpoint
  - Security headers

- **`frontend/.dockerignore`** - Reduces image size
  - Excludes: `node_modules`, `dist`, `.git`, config files

### Orchestration
- **`docker-compose.yml`** (root) - Full stack composition
  - All 4 services: Qdrant, Redis, Backend, Frontend
  - Proper networking and volume management
  - Health checks for each service
  - Dependency management (services wait for dependencies)
  - Environment variable support

- **`backend/docker-compose.yml`** - Same as root (for convenience)

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- 4GB+ RAM available
- Ports 80, 5173, 8000, 6333, 6379 available

### Development Mode

```bash
# From project root
cd /path/to/Code-Intelligence-Search-Engine

# Build and start all services
docker-compose up --build

# In another terminal, verify services are running
docker-compose ps

# Access the application
# Frontend: http://localhost (or http://localhost:5173)
# API docs: http://localhost:8000/docs
# Qdrant: http://localhost:6333/dashboard
```

### Production Mode

```bash
# Create .env file with production settings
cat > .env << EOF
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
EMBEDDING_DEVICE=cuda  # if GPU available
CACHE_ENABLED=true
REDIS_ENABLED=true
REDIS_PASSWORD=your-secure-password
AUTH_ENABLED=true
RATE_LIMIT_ENABLED=true
EOF

# Build with optimizations
docker-compose build --no-cache

# Start in background
docker-compose up -d

# Monitor logs
docker-compose logs -f backend frontend
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Application
APP_ENV=development              # development, staging, production
DEBUG=true                       # Set to false in production
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Embeddings
EMBEDDING_DEVICE=cpu             # cpu, cuda, mps
EMBEDDING_MODEL=microsoft/codebert-base

# Caching
CACHE_ENABLED=true               # Enable/disable caching
REDIS_ENABLED=true               # Use Redis if available
REDIS_PASSWORD=                  # Leave empty for dev, set for prod

# Authentication
AUTH_ENABLED=false               # Enable API key authentication
RATE_LIMIT_ENABLED=false         # Enable rate limiting

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost
```

## Service Details

### Qdrant (Vector Database)
- **Image**: `qdrant/qdrant:latest`
- **Port**: 6333 (internal), exposed to 6333
- **Volume**: `qdrant-storage` - persists vector data
- **Health Check**: HTTP GET /health

### Redis (Cache)
- **Image**: `redis:7-alpine`
- **Port**: 6379 (internal), exposed to 6379
- **Volume**: `redis-storage` - persists cache data
- **Health Check**: `redis-cli ping`

### Backend (FastAPI)
- **Image**: `code-search-backend:latest` (built locally)
- **Port**: 8000 (internal), exposed to 8000
- **Workers**: 4 (production-grade)
- **Health Check**: HTTP GET /health
- **Dependencies**: Qdrant, Redis (waits for them to be healthy)
- **Volumes**:
  - `./backend/app:/app/app` - live reload in dev
  - `./backend/data:/app/data` - persists indexed repositories

### Frontend (React + Nginx)
- **Image**: `code-search-frontend:latest` (built locally)
- **Port**: 80 (internal), exposed to 80 and 5173
- **Health Check**: HTTP GET / (wget)
- **Dependencies**: Backend (waits for startup)
- **Features**:
  - SPA routing (client-side routing works)
  - Static asset caching (1 year for .js, .css, etc.)
  - API proxy to backend (`/api` routes)
  - Gzip compression enabled

## Volume Management

### Named Volumes (Persistent Data)
```bash
# View all volumes
docker volume ls

# Inspect a volume
docker volume inspect code-intelligence-search-engine_qdrant-storage

# Backup volumes
docker run --rm -v code-intelligence-search-engine_qdrant-storage:/volume \
  -v $(pwd):/backup \
  alpine tar -czf /backup/qdrant-backup.tar.gz -C /volume .

# Clear volumes (WARNING: deletes all data)
docker-compose down -v
```

### Bind Mounts (Development)
```bash
# Backend code hot-reload
# ./backend/app:/app/app enables live code changes without container restart

# To persist changes permanently, edit files in ./backend/app/
```

## Common Commands

```bash
# Build services
docker-compose build                    # Build all images
docker-compose build --no-cache backend # Rebuild backend from scratch

# Start/stop services
docker-compose up                       # Start all services (foreground)
docker-compose up -d                    # Start all services (background)
docker-compose down                     # Stop and remove containers
docker-compose down -v                  # Also remove volumes (careful!)
docker-compose pause                    # Pause all services
docker-compose unpause                  # Resume all services

# View logs
docker-compose logs                     # Show all logs
docker-compose logs -f backend          # Follow backend logs
docker-compose logs --tail=100 frontend # Last 100 lines of frontend

# Execute commands in containers
docker-compose exec backend python -c "from app.config import get_settings; print(get_settings().CACHE_ENABLED)"
docker-compose exec frontend ls -la /usr/share/nginx/html

# Health status
docker-compose ps                       # Show all services and health

# Restart services
docker-compose restart backend          # Restart backend
docker-compose restart                  # Restart all services

# Remove images
docker-compose down --rmi local         # Remove local built images
docker-compose down --rmi all           # Remove all images (including dependencies)
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port 8000 already in use
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# 2. Dependencies not ready
docker-compose logs qdrant redis

# 3. Missing Python dependencies
docker-compose build --no-cache backend
```

### Frontend shows blank page
```bash
# Check browser console for errors
# Check logs
docker-compose logs frontend

# Verify API proxy
curl http://localhost:8000/health

# Check Nginx config
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### Cache not working
```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Verify backend environment
docker-compose exec backend env | grep REDIS

# Check backend logs
docker-compose logs backend | grep -i cache
```

### Out of disk space
```bash
# Clean up Docker
docker system prune -a --volumes

# Then rebuild
docker-compose build --no-cache
docker-compose up
```

## Performance Optimization

### For Development
- Keep `DEBUG=true` for detailed logging
- Use `EMBEDDING_DEVICE=cpu` (no CUDA overhead)
- Small test datasets for faster indexing
- Enable hot-reload with bind mounts

### For Production
- Set `DEBUG=false` and `LOG_LEVEL=WARNING`
- Use `EMBEDDING_DEVICE=cuda` if GPU available
- Enable `CACHE_ENABLED=true` and `REDIS_ENABLED=true`
- Use strong `REDIS_PASSWORD`
- Enable `AUTH_ENABLED=true` and `RATE_LIMIT_ENABLED=true`
- Consider multi-replica Qdrant and Redis sentinel
- Use reverse proxy (nginx, traefik) in front
- Add monitoring (Prometheus, Grafana)

### Resource Limits (Optional)

Add to docker-compose.yml services:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Deployment

### Docker Hub
```bash
# Tag images
docker tag code-search-backend:latest username/code-search-backend:1.0.0
docker tag code-search-frontend:latest username/code-search-frontend:1.0.0

# Push to registry
docker push username/code-search-backend:1.0.0
docker push username/code-search-frontend:1.0.0
```

### Kubernetes
```bash
# Generate manifests (manual process, or use tools like Kompose)
# kompose convert -f docker-compose.yml -o k8s/

# Deploy
kubectl apply -f k8s/
```

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml search-engine

# Monitor
docker stack services search-engine
```

## Image Sizes

```
Backend:   ~800MB  (Python 3.11 + dependencies)
Frontend:  ~40MB   (Alpine Nginx + built React app)
Qdrant:    ~500MB  (Rust-based vector DB)
Redis:     ~20MB   (Alpine Redis)
```

## Next Steps

- **Phase 5**: GitHub Actions CI/CD pipelines
- **Phase 6**: Kubernetes deployment
- **Phase 7**: Monitoring & alerting
- **Phase 8**: Load testing & optimization
- **Phase 9**: API versioning & documentation
- **Phase 10**: Security hardening & compliance

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Qdrant Docker Setup](https://qdrant.tech/documentation/guides/installation/#docker)
- [Redis Docker Setup](https://hub.docker.com/_/redis)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Configuration](https://nginx.org/en/docs/)
