# LabelTool - Intelligent Text Detection & Removal Tool

*[English](README.md) | [中文文档](README.zh-CN.md) | [日本語ドキュメント](README.ja.md)*

A comprehensive web-based tool for intelligent text processing with **dual-mode editing system**: OCR text detection/correction and advanced text generation with AI-powered inpainting. Now featuring a **microservice architecture** for better scalability and maintainability.

## ✨ Key Features

- 🤖 **Advanced OCR**: PaddleOCR with PP-OCRv5 models for high-precision text detection
- 🖼️ **AI Text Removal**: IOPaint LAMA model for seamless background preservation
- ✨ **Text Generation**: Custom text rendering with font analysis and precise positioning
- 🎨 **Interactive Canvas**: Konva.js-powered drag-and-drop text region editing
- ↩️ **Dual Undo/Redo**: Separate command histories for OCR and processed modes
- 🏗️ **Microservice Architecture**: Separate services for better scalability and resource management
- 🐳 **Docker Ready**: Full-stack containerization with persistent model caching
- 📱 **Responsive Design**: Works seamlessly on desktop and tablet devices

## 🚀 Quick Start (Recommended)

### Using Docker Compose (Easiest)

```bash
# Clone and start the application
git clone <repository-url>
cd labeltool
docker-compose up --build

# Access the application (3-service architecture)
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# IOPaint Service: http://localhost:8081
# API Docs: http://localhost:8000/docs
# IOPaint Docs: http://localhost:8081/docs
```

That's it! The application will be fully running with all dependencies.

## 💻 Local Development Setup

### Prerequisites
- Docker & Docker Compose (recommended)
- *OR* Python 3.11+ & Node.js 18+ (for local development)

### Option 1: Docker Development
```bash
# Run backend only
docker-compose up backend

# Run specific service for development
cd frontend && npm run dev  # Frontend dev server on :5173
```

### Option 2: Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 🎯 How to Use

1. **Upload Image**: Drag and drop an image (JPEG, PNG, WEBP, max 50MB)
2. **Auto Detection**: PaddleOCR automatically detects text regions
3. **Edit Regions**: 
   - **OCR Mode**: Adjust boundaries, correct text
   - **Processed Mode**: Add custom text for generation
4. **Process**: Remove text with AI inpainting (IOPaint LAMA model)
5. **Generate Text**: Render custom text with font-aware positioning
6. **Download**: Get your processed image

## 🛠️ Technology Stack

**Frontend**: React 18 + TypeScript + Konva.js + Zustand + Tailwind CSS  
**Backend**: FastAPI + Python 3.11 + PaddleOCR + HTTP Client  
**IOPaint Service**: FastAPI + IOPaint 1.6.0 + LAMA Model  
**AI Models**: PP-OCRv5 (text detection) + LAMA (inpainting)  
**Architecture**: Microservices with Docker Compose orchestration

## 🏗️ Microservice Architecture

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

**Benefits of this architecture**:
- **Service Isolation**: Each service can be developed, deployed, and scaled independently
- **Resource Optimization**: IOPaint can use dedicated GPU resources
- **Fault Tolerance**: Failure in one service doesn't crash the entire system
- **Reusability**: IOPaint service can be used by other applications

## 🔧 API Endpoints

### Main Backend API (Port 8000)
```bash
# Create session with image upload
POST /api/v1/sessions

# Process text removal (calls IOPaint service internally)
POST /api/v1/sessions/{id}/process

# Generate custom text
POST /api/v1/sessions/{id}/generate-text

# Download result
GET /api/v1/sessions/{id}/result
```

### IOPaint Service API (Port 8081) 
```bash
# Health check
GET /api/v1/health

# Service information
GET /api/v1/info

# Text inpainting with regions
POST /api/v1/inpaint-regions
```

**Documentation**:
- Main API: http://localhost:8000/docs
- IOPaint Service: http://localhost:8081/docs

## 📖 Documentation

- [Docker Deployment Guide](DOCKER.md) - Complete Docker setup and deployment instructions

## 🛠️ Troubleshooting

**Docker issues**:
```bash
# Check if Docker is running
docker --version
docker-compose --version

# View logs for each service
docker-compose logs frontend
docker-compose logs backend  
docker-compose logs iopaint-service

# View all services status
docker-compose ps
```

**Performance**: First run downloads AI models (~2GB). Subsequent runs are much faster.

**Memory**: Large images are automatically resized. Use smaller images if you encounter memory issues.