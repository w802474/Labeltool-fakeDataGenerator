# Docker Deployment Guide

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

This document describes how to use Docker to run the LabelTool project.

## 🚀 Quick Start

### 1. Clone the project and enter the directory
```bash
git clone <your-repo-url>
cd labeltool
```

### 2. Environment configuration (optional)
```bash
# Copy environment variables configuration file
cp .env.example .env

# Modify configuration in .env file as needed
nano .env
```

### 3. Build and start services
```bash
# Build and start all services (backend starts first, frontend waits for backend health check)
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 4. Access the application
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Backend API status: http://localhost:8000/

## 📋 Service Description

### Backend Service (labeltool-backend)
- **Port**: 8000
- **Tech Stack**: Python 3.11.13 + FastAPI + PaddleOCR
- **Function**: Provides OCR text detection and image processing API
- **Health Check**: Automatically checks service status, takes about 40 seconds to initialize after startup

### Frontend Service (labeltool-frontend)
- **Port**: 3000
- **Tech Stack**: React 18 + TypeScript + Nginx
- **Function**: Provides user interface and image annotation functionality
- **Dependencies**: Starts only after backend service health check passes

## 🔧 Docker Command Reference

### Service Management
```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Rebuild and start
docker-compose up --build

# Stop services
docker-compose down

# Stop services and remove volumes
docker-compose down -v

# View service status
docker-compose ps

# View service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

### Build services individually
```bash
# Build backend only
docker-compose build backend

# Build frontend only
docker-compose build frontend
```

### Service restart
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

## 📁 Data Persistence

The project uses Docker volumes to persist important data:

- `backend_uploads`: Uploaded image files
- `backend_processed`: Processed image files
- `backend_exports`: Exported files
- `backend_logs`: Application logs

### Volume management commands
```bash
# View all volumes
docker volume ls

# View specific volume details
docker volume inspect labeltool_backend_uploads

# Remove unused volumes
docker volume prune
```

## ⚙️ Environment Variables Configuration

Main environment variables:

### API Configuration
- `API_HOST`: API listening address (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `LOG_LEVEL`: Log level (default: INFO)

### File Processing Configuration
- `MAX_FILE_SIZE`: Maximum file size (default: 50MB)
- `UPLOAD_DIR`: Upload directory (default: uploads)
- `PROCESSED_DIR`: Processed files directory (default: processed)

### OCR Configuration
- `PADDLEOCR_DEVICE`: Device type (cpu/cuda, default: cpu)
- `PADDLEOCR_LANG`: OCR language (default: en)

### CORS Configuration
- `CORS_ORIGINS`: Allowed frontend domains

## 🐛 Troubleshooting

### 1. Port Conflicts
If ports 3000 or 8000 are occupied, modify port mapping in `docker-compose.yml`:
```yaml
ports:
  - "3001:80"  # Change frontend to 3001
  - "8001:8000"  # Change backend to 8001
```

### 2. Insufficient Memory
PaddleOCR and image processing require substantial memory, ensure Docker has sufficient memory allocation (recommended 4GB+).

### 3. Service Startup Failure
```bash
# View detailed logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild images
docker-compose build --no-cache
```

### 4. Permission Issues
```bash
# Ensure correct directory permissions
sudo chown -R $USER:$USER uploads processed exports logs
```

### 5. Network Connection Issues
```bash
# Check network connections
docker network ls
docker network inspect labeltool_labeltool-network
```

## 🔄 Development Mode

If you need to modify code during development:

### Backend Development
```bash
# Stop backend container
docker-compose stop backend

# Run backend locally for development
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
# Stop frontend container
docker-compose stop frontend

# Run frontend locally for development
cd frontend
npm run dev
```

## 📊 Monitoring and Logs

### Health Checks
All services are configured with health checks:
```bash
# View service health status
docker-compose ps
```

### Log Viewing
```bash
# View all logs in real-time
docker-compose logs -f

# View recent logs
docker-compose logs --tail=100

# View error logs only
docker-compose logs | grep ERROR
```

## 🚀 Production Environment Deployment

### 1. Modify environment variables
```bash
# Production environment configuration
API_RELOAD=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
```

### 2. Use external database (if needed)
Modify `docker-compose.yml` to add database service.

### 3. Configure reverse proxy
Recommended to use Nginx or other reverse proxy in production environment.

### 4. SSL certificates
Configure HTTPS certificates to ensure secure access.

## 📝 Updates and Maintenance

### Update application
```bash
# Pull latest code
git pull

# Rebuild and start
docker-compose up --build -d

# Clean old images
docker image prune
```

### Backup data
```bash
# Backup volume data
docker run --rm -v labeltool_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

If you have any issues, please check the log files or contact the development team.