# Docker Deployment Guide

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

This document describes how to use Docker to run the **LabelTool - Intelligent Text Detection & Removal Tool** project with **microservice architecture** (3 services: Frontend, Backend, IOPaint Service).

## 🚀 Quick Start

### 1. Clone the project and enter the directory
```bash
git clone <your-repo-url>
cd Labeltool-fakeDataGenerator
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
# Build and start all 3 services (IOPaint → Backend → Frontend startup order)
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 4. Access the application
- **Frontend**: http://localhost:3000 (User Interface)
- **Backend API**: http://localhost:8000/docs (Main API Documentation)
- **IOPaint Service**: http://localhost:8081/docs (Text Removal Service Documentation)
- **Backend Status**: http://localhost:8000/ (API Health Status)
- **IOPaint Status**: http://localhost:8081/api/v1/health (IOPaint Health Status)

## 📋 Microservice Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │ IOPaint Service│
│   (React App)   │────│  (FastAPI)      │────│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8081    │  
│                 │    │                 │    │                 │
│ - User Interface│    │ - OCR Detection │    │ - Text Removal  │
│ - Canvas Editor │    │ - Session Mgmt  │    │ - LAMA Model    │
│ - File Upload   │    │ - API Gateway   │    │ - Inpainting    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🎯 IOPaint Service (labeltool-iopaint)
- **Port**: 8081
- **Tech Stack**: Python 3.11 + FastAPI 0.108.0 + IOPaint 1.6.0 + LAMA Model
- **Dependencies**: IOPaint, HuggingFace Hub, OpenCV, Pillow 9.5.0
- **Function**: Advanced text inpainting and removal using AI
- **Health Check**: ~60 seconds initialization (downloads LAMA model ~2GB on first run)
- **Volume**: Persistent HuggingFace model cache (~2GB)
- **Service Dependencies**: None (fully independent service)

### 🔧 Backend Service (labeltool-backend)
- **Port**: 8000
- **Tech Stack**: Python 3.11 + FastAPI 0.108.0 + PaddleOCR + Pydantic v2
- **Dependencies**: PaddleOCR, PaddlePaddle, OpenCV, Pillow 9.5.0, WebSockets
- **Function**: OCR text detection, session management, API orchestration
- **Health Check**: ~40 seconds initialization (downloads PaddleOCR models on first run)
- **Volume**: Persistent PaddleX model cache, uploads, processed files, logs
- **Service Dependencies**: Requires IOPaint Service to be healthy

### 🎨 Frontend Service (labeltool-frontend)
- **Port**: 3000 (Nginx proxy)
- **Tech Stack**: React 18 + TypeScript + Vite + Konva.js + Zustand
- **Dependencies**: React-Konva, Axios, Tailwind CSS, Lucide React
- **Function**: Interactive canvas editing, drag-and-drop file upload, real-time progress
- **Build**: Multi-stage Docker build with Nginx serving static files
- **Service Dependencies**: Starts only after backend service health check passes

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
docker-compose logs iopaint-service  # IOPaint service logs
docker-compose logs backend          # Backend service logs
docker-compose logs frontend         # Frontend service logs

# Follow logs in real-time
docker-compose logs -f iopaint-service
```

### Build services individually
```bash
# Build IOPaint service only
docker-compose build iopaint-service

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
docker-compose restart iopaint-service
docker-compose restart backend
docker-compose restart frontend
```

## 📁 Data Persistence

The project uses Docker volumes to persist important data:

### Backend Service Volumes
- `backend_uploads`: Uploaded image files
- `backend_removal`: Text removal processed image files
- `backend_generated`: Text generation result image files
- `backend_exports`: Exported files
- `backend_logs`: Application logs
- `paddlex_cache`: PaddleOCR model cache

### IOPaint Service Volumes
- `huggingface_cache`: IOPaint LAMA model cache (~2GB)
- `iopaint_temp`: Temporary processing files

### Volume management commands
```bash
# View all volumes
docker volume ls

# View specific volume details
docker volume inspect labeltool-fakedatagenerator_backend_uploads
docker volume inspect labeltool-fakedatagenerator_huggingface_cache
docker volume inspect labeltool-fakedatagenerator_paddlex_cache

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
- `REMOVAL_DIR`: Text removal results directory (default: removal)
- `GENERATED_DIR`: Text generation results directory (default: generated)

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
# View detailed logs for all services
docker-compose logs -f iopaint-service
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild images
docker-compose build --no-cache

# Check service health status
docker-compose ps
```

### 4. IOPaint Service Issues
```bash
# Check IOPaint service logs
docker-compose logs -f iopaint-service

# Restart IOPaint service only
docker-compose restart iopaint-service

# Check IOPaint service health
curl http://localhost:8081/api/v1/health
```

### 5. Permission Issues
```bash
# Ensure correct directory permissions
sudo chown -R $USER:$USER uploads removal generated exports logs
```

### 6. Network Connection Issues
```bash
# Check network connections
docker network ls
docker network inspect labeltool-fakedatagenerator_labeltool-network

# Test service connectivity
curl http://localhost:3000  # Frontend
curl http://localhost:8000/api/v1/health  # Backend
curl http://localhost:8081/api/v1/health  # IOPaint Service
```

## 🔄 Development Mode

If you need to modify code during development:

### IOPaint Service Development
```bash
# Stop IOPaint service container
docker-compose stop iopaint-service

# Run IOPaint service locally for development
cd iopaint-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

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

### Development with Mixed Modes
```bash
# Run IOPaint and Backend in Docker, Frontend locally
docker-compose up iopaint-service backend
cd frontend && npm run dev

# Run only IOPaint in Docker, Backend and Frontend locally
docker-compose up iopaint-service
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
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
# Backup backend uploads and result files
docker run --rm -v labeltool-fakedatagenerator_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_backend_removal:/data -v $(pwd):/backup alpine tar czf /backup/removal-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_backend_generated:/data -v $(pwd):/backup alpine tar czf /backup/generated-backup.tar.gz -C /data .

# Backup model caches (important for faster startup)
docker run --rm -v labeltool-fakedatagenerator_huggingface_cache:/data -v $(pwd):/backup alpine tar czf /backup/iopaint-models-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_paddlex_cache:/data -v $(pwd):/backup alpine tar czf /backup/paddleocr-models-backup.tar.gz -C /data .
```

If you have any issues, please check the log files or contact the development team.