# LabelTool - Intelligent Text Detection & Removal Tool

*[English](README.md) | [中文文档](README.zh-CN.md) | [日本語ドキュメント](README.ja.md)*

A comprehensive web-based tool for intelligent text processing with **dual-mode editing system**: OCR text detection/correction and advanced text generation with AI-powered inpainting.

## ✨ Key Features

- 🤖 **Advanced OCR**: PaddleOCR with PP-OCRv5 models for high-precision text detection
- 🖼️ **AI Text Removal**: IOPaint LAMA model for seamless background preservation
- ✨ **Text Generation**: Custom text rendering with font analysis and precise positioning
- 🎨 **Interactive Canvas**: Konva.js-powered drag-and-drop text region editing
- ↩️ **Dual Undo/Redo**: Separate command histories for OCR and processed modes
- 🐳 **Docker Ready**: Full-stack containerization with persistent model caching
- 📱 **Responsive Design**: Works seamlessly on desktop and tablet devices

## 🚀 Quick Start (Recommended)

### Using Docker Compose (Easiest)

```bash
# Clone and start the application
git clone <repository-url>
cd labeltool
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
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
**Backend**: FastAPI + Python 3.11 + PaddleOCR + IOPaint + Docker  
**AI Models**: PP-OCRv5 (text detection) + LAMA (inpainting)

## 🔧 API Endpoints

```bash
# Create session with image upload
POST /api/v1/sessions

# Process text removal
POST /api/v1/sessions/{id}/process

# Generate custom text
POST /api/v1/sessions/{id}/generate-text

# Download result
GET /api/v1/sessions/{id}/result
```

Full API documentation: http://localhost:8000/docs

## 📖 Documentation

- [Docker Deployment Guide](DOCKER.md) - Complete Docker setup and deployment instructions

## 🛠️ Troubleshooting

**Docker issues**:
```bash
# Check if Docker is running
docker --version
docker-compose --version

# View logs
docker-compose logs backend
docker-compose logs frontend
```

**Performance**: First run downloads AI models (~2GB). Subsequent runs are much faster.

**Memory**: Large images are automatically resized. Use smaller images if you encounter memory issues.