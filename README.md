# LabelTool - Intelligent Text Detection & Removal Tool

**🌍 [中文](README.zh-CN.md) | [日本語](README.ja.md) | English**

A comprehensive web-based intelligent text annotation and processing tool that provides complete text processing workflows: from automatic detection to manual adjustment, intelligent removal, and smart text generation. Built with modern microservice architecture for scalability and maintainability.

## 🎯 Project Overview

LabelTool is a production-ready intelligent text processing platform that combines cutting-edge AI models with intuitive user interfaces to deliver professional text annotation and removal capabilities:

### 🔄 Complete Processing Workflow
1. **Automatic Text Detection** using PaddleOCR with high precision
2. **Manual Text Region Adjustment** with intuitive drag-and-drop interface  
3. **Text Removal with Advanced Inpainting** using IOPaint for seamless background preservation
4. **Text Generation and Replacement** allowing users to add custom text to processed images
5. **Dual-Mode Editing System** supporting both OCR editing and processed image text generation

### 🏗️ Modern Architecture
- **Microservice Architecture**: Separate services for better scalability and resource management
- **Domain-Driven Design**: Clean separation of concerns with DDD patterns in backend
- **Real-time Processing**: WebSocket-based progress tracking for long-running tasks
- **Production Ready**: Docker containerization with comprehensive monitoring and error handling
- **Modern Frontend**: React Router-based navigation with proper URL routing and browser history support
- **Persistent State**: SQLite database with full session management and historical data

## ✨ Key Features

### 🤖 Advanced AI Capabilities
- **High-Precision OCR**: PaddleOCR with PP-OCRv5 models for accurate text detection
- **State-of-the-Art Inpainting**: IOPaint LAMA model for seamless background preservation
- **Intelligent Font Analysis**: Automatic font property detection for text generation
- **Smart Image Scaling**: Automatic optimization for large images

### 🎨 Interactive User Experience
- **Interactive Canvas**: Konva.js-powered drag-and-drop text region editing
- **Dual-Mode System**: Separate editing modes for OCR correction and text generation
- **Advanced Undo/Redo**: Command-pattern based operation history with mode separation
- **Real-time Progress**: Live WebSocket updates during processing
- **Modern Navigation**: React Router with proper URL routing (home page `/` and editor `/editor/{session_id}`)
- **Session Gallery**: Virtualized gallery with infinite scrolling for historical sessions
- **Responsive Design**: Optimized for desktop and tablet devices

### 🗄️ Data Management
- **SQLite Database**: Persistent storage with zero configuration
- **Session Management**: Complete session lifecycle with status tracking
- **Historical Data**: Browse and manage previous processing sessions
- **Data Integrity**: Foreign key constraints and transaction safety
- **Performance Optimized**: Indexes for common query patterns

### 🏗️ Technical Excellence
- **Microservice Architecture**: Independent services for scalability
- **Production Ready**: Comprehensive error handling, health monitoring, and diagnostics
- **Docker Native**: Full containerization with persistent model caching
- **Performance Optimized**: GPU acceleration, memory management, and intelligent resource usage

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd labeltool-fakeDataGenerator

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# IOPaint Service: http://localhost:8081/docs
```

That's it! The application will be fully running with all AI models and dependencies.

### Performance Notes
- **First Run**: Downloads AI models (~2-3GB), may take 5-10 minutes
- **Subsequent Runs**: Models are cached, startup is much faster
- **GPU Support**: Enable CUDA for faster processing (see configuration)

## 🏗️ Architecture Overview

### Microservice Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │ IOPaint Service│
│   (React App)   │────│  (FastAPI)      │────│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8081    │  
│                 │    │                 │    │                 │
│ • React Router  │    │ • OCR Detection │    │ • Text Removal  │
│ • Canvas Editor │    │ • Session Mgmt  │    │ • LAMA Model    │
│ • File Upload   │    │ • SQLite DB     │    │ • Image Repair  │
│ • State Mgmt    │    │ • API Gateway   │    │ • Progress Track│
│ • Gallery       │    │ • Business Logic│    │ • WebSocket     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        └─────────── WebSocket & HTTP/REST ───────────────┘
```

### Service Responsibilities

**Frontend Service**:
- React 18 + TypeScript + Vite
- React Router 6.18 for proper URL navigation
- Interactive Konva.js canvas for region editing
- Zustand state management with undo/redo system
- Virtualized gallery with infinite scrolling
- Real-time WebSocket progress tracking
- Responsive Tailwind CSS design

**Backend Service**:
- FastAPI + Python 3.11 with DDD architecture
- SQLite database with SQLAlchemy async ORM
- PaddleOCR integration for text detection
- Session and task management with persistence
- IOPaint service client integration
- RESTful API with comprehensive documentation

**IOPaint Service** ([📖 Detailed Documentation](iopaint-service/README.md)):
- Independent FastAPI microservice
- IOPaint 1.6.0 with LAMA model
- Advanced image inpainting capabilities
- Resource monitoring and optimization
- WebSocket progress reporting
- Standalone deployment capability

## 🛠️ Technology Stack

### Frontend Technologies
- **Framework**: React 18 + TypeScript + Vite
- **Routing**: React Router DOM 6.18 for SPA navigation
- **Canvas**: Konva.js + react-konva for interactive editing
- **State Management**: Zustand with persistence and undo/redo
- **UI Components**: Custom Tailwind CSS components
- **Virtualization**: react-window for performance optimization
- **HTTP Client**: Axios with interceptors
- **File Upload**: React-Dropzone with progress tracking
- **Testing**: Jest + React Testing Library

### Backend Technologies
- **Framework**: FastAPI + Python 3.11 + Pydantic v2
- **Database**: SQLite with SQLAlchemy async ORM
- **OCR Engine**: PaddleOCR (latest with PP-OCRv5 models)
- **Image Processing**: OpenCV + Pillow + NumPy
- **Architecture**: Domain-Driven Design (DDD)
- **Async Processing**: aiohttp + WebSocket support
- **Configuration**: Pydantic Settings with environment variables
- **Logging**: Loguru with structured logging

### IOPaint Service Technologies
- **Framework**: FastAPI + Python 3.11
- **AI Model**: IOPaint 1.6.0 with LAMA inpainting model
- **Image Processing**: Advanced scaling and optimization
- **Monitoring**: Resource tracking and diagnostics
- **Error Handling**: Intelligent retry and recovery mechanisms

### Infrastructure & DevOps
- **Containerization**: Docker + Docker Compose
- **Database**: SQLite file storage (320KB database size)
- **Model Caching**: Persistent volumes for AI models
- **Networking**: Bridge network with service discovery
- **Health Monitoring**: Comprehensive health checks
- **Volume Management**: Shared storage for images and cache

## 🎯 User Workflows

### 1. Modern Web Navigation
```
Home Page (/) → Gallery Selection → Editor (/editor/{session_id}) → Process → Results
     ↓              ↓                    ↓                     ↓         ↓
Browser URL    Historical Sessions   Canvas Editing     AI Processing  Download
```

### 2. Session Management
```
Upload Image → OCR Detection → Session Storage → Edit/Process → Historical Access
     ↓              ↓               ↓               ↓              ↓
  Validation   Text Regions    SQLite Database  AI Processing   Gallery View
```

### 3. Dual-Mode Editing System

**OCR Mode**:
- Edit detected text content
- Adjust text region boundaries
- Correct OCR recognition errors
- Perfect for text annotation and correction

**Processed Mode**:
- Work with inpainted background images
- Add custom text with intelligent positioning
- Font-aware text rendering
- Ideal for text replacement and enhancement

## 🗄️ Database Architecture

### SQLite Database Design
The application uses SQLite for persistent data storage with the following benefits:

**Database Features**:
- **Zero Configuration**: No separate database server required
- **ACID Compliance**: Transaction safety and data integrity
- **File-based Storage**: Easy backup and deployment (`/data/labeltool.db`)
- **High Performance**: Local file access with minimal latency
- **JSON Support**: Store complex data structures (bounding boxes, configurations)

**Table Structure**:
```sql
-- Sessions table: Main session management
sessions (
  id: VARCHAR(255) PRIMARY KEY,
  original_image_path: VARCHAR(500),
  processed_image_path: VARCHAR(500),
  status: VARCHAR(50),
  created_at: DATETIME,
  updated_at: DATETIME
)

-- Text regions table: OCR and processed text regions
text_regions (
  id: VARCHAR(255) PRIMARY KEY,
  session_id: VARCHAR(255) FOREIGN KEY,
  region_type: VARCHAR(50),  -- 'ocr' or 'processed'
  bounding_box_json: JSON,
  corners_json: JSON,
  confidence: FLOAT,
  original_text: TEXT,
  edited_text: TEXT,
  user_input_text: TEXT
)
```

## 🔌 API Documentation

### Main Backend API (Port 8000)

**Session Management**:
```bash
POST   /api/v1/sessions                    # Create session with OCR detection
GET    /api/v1/sessions/{id}               # Get session details
PUT    /api/v1/sessions/{id}/regions       # Update text regions (dual-mode)
DELETE /api/v1/sessions/{id}               # Clean up session and files
GET    /api/v1/sessions                    # List historical sessions with pagination
```

**Processing Endpoints**:
```bash
POST   /api/v1/sessions/{id}/process-async # Start async text removal
GET    /api/v1/tasks/{id}/status           # Get processing status
POST   /api/v1/tasks/{id}/cancel           # Cancel processing task
```

**Text Generation**:
```bash
POST   /api/v1/sessions/{id}/generate-text # Generate text in regions
POST   /api/v1/sessions/{id}/preview-text  # Preview text generation
```

**File Operations**:
```bash
GET    /api/v1/sessions/{id}/image         # Get original image
GET    /api/v1/sessions/{id}/result        # Download processed result
```

### IOPaint Service API (Port 8081)

For detailed IOPaint service documentation, see: **[IOPaint Service Documentation](iopaint-service/README.md)**

**Core Endpoints**:
```bash
GET    /api/v1/health                      # Health check with diagnostics
GET    /api/v1/info                        # Service information
POST   /api/v1/inpaint-regions            # Text inpainting with regions
POST   /api/v1/inpaint-regions-json       # Inpainting with statistics
```

## 💻 Development Setup

### Local Development

**Prerequisites**:
- Docker & Docker Compose (recommended)
- Python 3.11+ & Node.js 18+ (for local development)
- Git for version control

**Option 1: Docker Development**
```bash
# Full stack development
docker-compose up --build

# Backend only
docker-compose up backend iopaint-service

# Frontend development server
cd frontend && npm run dev  # Port 5173 with hot reload
```

**Option 2: Local Development**
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# IOPaint service setup (new terminal)
cd iopaint-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Testing

**Backend Testing**:
```bash
cd backend
pytest tests/ -v --cov=app
```

**Frontend Testing**:
```bash
cd frontend
npm run test        # Run tests
npm run test:watch  # Watch mode
npm run test:coverage  # Coverage report
```

**Integration Testing**:
```bash
# Test full workflow with Docker
docker-compose up -d
curl http://localhost:8000/api/v1/health
curl http://localhost:8081/api/v1/health
```

## 🚢 Production Deployment

### Docker Production Setup

```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build -d

# With GPU support
docker-compose -f docker-compose.gpu.yml up --build -d

# Monitor services
docker-compose logs -f
docker-compose ps
```

### Environment Configuration

**Backend Environment**:
```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:////app/data/labeltool.db
DATABASE_ECHO=false

# OCR Configuration
PADDLEOCR_DEVICE=cpu          # cpu/cuda
PADDLEOCR_LANG=en             # Language support

# IOPaint Service
IOPAINT_SERVICE_URL=http://iopaint-service:8081
IOPAINT_TIMEOUT=300           # Processing timeout

# Application Settings
MAX_FILE_SIZE=52428800        # 50MB max upload
LOG_LEVEL=INFO                # Logging level
```

**IOPaint Service Environment**:
```env
# Model Configuration
IOPAINT_MODEL=lama            # AI model selection
IOPAINT_DEVICE=cpu            # cpu/cuda/mps
IOPAINT_LOW_MEM=true          # Memory optimization

# Performance Settings
MAX_IMAGE_SIZE=2048           # Max dimension
REQUEST_TIMEOUT=300           # Processing timeout
```

## 📊 Monitoring & Observability

### Health Monitoring

**Service Health Checks**:
```bash
# Main application health
curl http://localhost:8000/api/v1/health

# IOPaint service health
curl http://localhost:8081/api/v1/health

# Docker health status
docker-compose ps
```

**Processing Metrics**:
- Real-time progress tracking via WebSocket
- Processing time and resource usage
- Error rates and retry statistics
- Model performance metrics
- Database query performance

### Logging

**Structured Logging**:
- JSON-formatted logs for production
- Request/response tracing
- Error tracking with stack traces
- Performance metrics logging
- Database operation logging

**Log Access**:
```bash
# View service logs
docker-compose logs -f backend
docker-compose logs -f iopaint-service
docker-compose logs -f frontend

# Export logs
docker-compose logs --no-color > application.log
```

## 🔧 Configuration & Customization

### OCR Configuration

**PaddleOCR Settings**:
```python
OCR_CONFIG = {
    "det_db_thresh": 0.3,        # Detection threshold
    "det_db_box_thresh": 0.6,    # Bounding box threshold
    "det_limit_side_len": 1920,  # Max image dimension
    "use_angle_cls": True,       # Text angle classification
    "lang": "en"                 # Language support
}
```

### IOPaint Configuration

**Model Options**:
- **lama** (default): Best quality inpainting
- **ldm**: Latent Diffusion Model
- **zits**: Fast processing
- **mat**: Mask-Aware Transformer
- **fcf**: Fourier Convolutions
- **manga**: Specialized for anime/manga

**Performance Tuning**:
```env
IOPAINT_LOW_MEM=true          # Enable for limited memory
IOPAINT_CPU_OFFLOAD=true      # CPU/GPU load balancing
MAX_IMAGE_SIZE=2048           # Reduce for faster processing
```

### Database Configuration

**SQLite Optimization**:
```env
DATABASE_ECHO=false           # Disable SQL logging in production
DATABASE_POOL_SIZE=5          # Connection pool size
DATABASE_TIMEOUT=30           # Query timeout seconds
```

## 🛠️ Troubleshooting

### Common Issues

**1. Service Startup Issues**
```bash
# Check Docker status
docker --version
docker-compose --version

# View service logs
docker-compose logs backend
docker-compose logs iopaint-service

# Restart services
docker-compose restart
```

**2. Database Issues**
```bash
# Check database file
ls -la data/labeltool.db

# Reset database (WARNING: loses all data)
rm data/labeltool.db
docker-compose restart backend
```

**3. Model Download Issues**
```bash
# Check internet connection
curl -I https://huggingface.co

# Clear model cache
rm -rf volumes/huggingface_cache/*
rm -rf volumes/paddlex_cache/*

# Rebuild with fresh models
docker-compose down -v
docker-compose up --build
```

**4. Frontend Navigation Issues**
```bash
# Clear browser cache and localStorage
# Check browser console for JavaScript errors
# Verify all services are running on correct ports
```

**5. Performance Issues**
```bash
# Enable GPU support
docker-compose -f docker-compose.gpu.yml up

# Reduce image size limits
# Edit environment variables:
# MAX_IMAGE_SIZE=1024
# MAX_FILE_SIZE=10485760  # 10MB
```

**6. Memory Issues**
```bash
# Enable low memory mode
# IOPaint service environment:
IOPAINT_LOW_MEM=true
IOPAINT_CPU_OFFLOAD=true

# Reduce concurrent processing
MAX_CONCURRENT_TASKS=1
```

### Getting Help

**Logs and Diagnostics**:
```bash
# Generate diagnostic report
docker-compose logs --no-color > diagnostic.log
docker-compose ps >> diagnostic.log
docker system df >> diagnostic.log

# Check resource usage
docker stats

# Database status
sqlite3 data/labeltool.db ".tables"
sqlite3 data/labeltool.db "SELECT COUNT(*) FROM sessions;"
```

**Common Solutions**:
- First run takes longer due to model downloads
- Use smaller images if memory is limited
- Enable GPU support for faster processing
- Check firewall settings for port access
- Clear browser cache if navigation issues occur

## 📖 Additional Documentation

- **[IOPaint Service](iopaint-service/README.md)** - Detailed service documentation
- **[Docker Deployment](DOCKER.md)** - Complete deployment guide
- **[API Reference](http://localhost:8000/docs)** - Interactive API documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Contribution guidelines

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PaddleOCR Team** for the excellent OCR models
- **IOPaint Developers** for the state-of-the-art inpainting capabilities
- **React & FastAPI Communities** for the robust frameworks
- **SQLAlchemy Team** for the powerful ORM
- **Docker** for containerization support