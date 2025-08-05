# LabelTool - Intelligent Text Detection & Removal Tool

## 🔄 Project Awareness & Context
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in this document.
- **Use Docker containers for deployment and development** with docker-compose for orchestration.
- **Follow the Domain-Driven Design (DDD) approach** for backend architecture with clear separation of concerns.

## 🎯 Project Overview
LabelTool is a comprehensive web-based intelligent text annotation and processing tool that provides:
1. **Automatic text detection** using PaddleOCR with high precision
2. **Manual text region adjustment** with intuitive drag-and-drop interface  
3. **Text removal with advanced inpainting** using IOPaint for seamless background preservation
4. **Text generation and replacement** allowing users to add custom text to processed images
5. **Dual-mode editing system** supporting both OCR editing and processed image text generation

### Current Technology Stack
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI 0.108.0 + Python 3.11 + Pydantic v2
- **OCR Engine**: PaddleOCR (latest version with PP-OCRv5 models)
- **Text Inpainting**: IOPaint 1.6.0 with LAMA model for advanced text removal
- **Image Processing**: OpenCV + Pillow + Konva.js (canvas interactions)
- **State Management**: Zustand with persistence and undo/redo system
- **File Upload**: React-Dropzone with progress tracking
- **UI Components**: Custom Tailwind components + Lucide React icons
- **Container**: Docker + Docker Compose for full-stack deployment
- **Testing**: Jest + React Testing Library (Frontend), Pytest (Backend)

## 🧱 Code Structure & Modularity

### Current Directory Structure
```
Labeltool-fakeDataGenerator/
├── frontend/                    # React TypeScript Frontend
│   ├── src/components/          # React components (ImageCanvas, FileUpload, Toolbar, etc.)
│   ├── src/hooks/               # Custom React hooks (useCanvas, useFileUpload, etc.)
│   ├── src/stores/              # Zustand state management
│   ├── src/services/            # API communication services
│   ├── src/types/               # TypeScript type definitions
│   └── src/utils/               # Utility functions
├── backend/                     # FastAPI Python Backend
│   ├── app/domain/              # Domain models and business logic
│   ├── app/application/         # Use case implementations
│   ├── app/infrastructure/      # Infrastructure layer (OCR, storage, API)
│   ├── uploads/                 # Original uploaded images
│   ├── processed/               # Processed result images
│   └── logs/                    # Application logs
├── iopaint-service/             # IOPaint Microservice
│   ├── app/services/            # Core IOPaint services
│   ├── app/api/                 # API routes and models
│   └── app/websocket/           # WebSocket progress tracking
└── docker-compose.yml           # Full-stack orchestration
```

### Code Organization Rules
- **Never create a file longer than 500 lines of code.** If approaching this limit, refactor into smaller modules.
- **Organize code into clearly separated modules** grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python-dotenv and load_dotenv()** for environment variables.
- **Follow DDD patterns**: Entities, Value Objects, Domain Services, Use Cases, and Infrastructure adapters.

## 🏗️ Microservice Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │ IOPaint Service│
│   (React App)   │────│  (FastAPI)      │────│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8081    │  
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Responsibilities

**Frontend Service**:
- React 18 + TypeScript + Vite
- Interactive Konva.js canvas for region editing
- Zustand state management with undo/redo system
- Real-time WebSocket progress tracking
- Responsive Tailwind CSS design

**Backend Service**:
- FastAPI + Python 3.11 with DDD architecture
- PaddleOCR integration for text detection
- Session and task management
- IOPaint service client integration
- RESTful API with comprehensive documentation

**IOPaint Service**:
- Independent FastAPI microservice
- IOPaint 1.6.0 with LAMA model
- Advanced image inpainting capabilities
- Resource monitoring and optimization
- Standalone deployment capability

## 🧪 Testing & Reliability
- **Always create Pytest unit tests for new backend features** (use cases, domain services, API endpoints).
- **Always create Jest/RTL tests for new frontend components** and custom hooks.
- **After updating any logic**, check whether existing tests need updates.
- **Tests should live in `/tests` folder** mirroring the main app structure.
- **Include at least**:
  - 1 test for expected behavior
  - 1 edge case test
  - 1 error/failure case test

## ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- **Add new sub-tasks or TODOs** discovered during development to `TASK.md` under a "Discovered During Work" section.
- **Always test OCR accuracy** after making changes to image preprocessing or PaddleOCR configuration.
- **Always verify text removal quality** visually and programmatically after implementing new inpainting algorithms.

## 📎 Style & Conventions

### Python Backend Standards
- **Use Python 3.11+** as the primary language.
- **Follow PEP8** with `black` formatting and `isort` for imports.
- **Use Pydantic v2** for data validation and serialization.
- **Use FastAPI** for all API endpoints with proper OpenAPI documentation.
- **Use type hints everywhere** including return types and complex generics.
- **Write Google-style docstrings** for every function.

### TypeScript Frontend Standards
- **Use strict TypeScript configuration** with no implicit any.
- **Prefer functional components** with hooks over class components.
- **Use custom hooks** for complex state logic and side effects.
- **Follow React best practices**: memo, useMemo, useCallback for performance.
- **Use Tailwind CSS** for styling with consistent design tokens.

## 🎨 UI/UX Design Guidelines

### Design Principles
1. **Simplicity First**: Minimize UI elements, focus on core functionality
2. **Visual Guidance**: Use color and animation to guide user workflow  
3. **Responsive Design**: Support different screen sizes and devices
4. **Accessibility**: Support keyboard navigation and screen readers

### Layout Structure
- **Top Toolbar**: File operations, processing controls
- **Main Canvas**: Image display and annotation editing area
- **Side Panel**: Text region list and properties
- **Bottom Status Bar**: Processing progress and operation feedback

## 🚀 Current API Design

### RESTful Endpoints
```
# Core Session Management
POST   /api/v1/sessions                        # Create new labeling session with OCR
GET    /api/v1/sessions/{session_id}           # Get complete session details
PUT    /api/v1/sessions/{session_id}/regions   # Update text regions (dual-mode)
DELETE /api/v1/sessions/{session_id}           # Clean up session and files

# Processing Endpoints
POST   /api/v1/sessions/{session_id}/process   # Execute text removal with IOPaint
GET    /api/v1/sessions/{session_id}/estimate  # Get processing time estimate

# Text Generation
POST   /api/v1/sessions/{session_id}/generate-text    # Generate text in regions
POST   /api/v1/sessions/{session_id}/preview-text     # Preview text generation

# File Operations
GET    /api/v1/sessions/{session_id}/image     # Get original uploaded image
GET    /api/v1/sessions/{session_id}/result    # Download processed result image

# System Health & Info
GET    /api/v1/health                          # Health check with service status
GET    /api/v1/info                            # Service configuration info
```

## 📚 Documentation & Explainability
- **Update `README.md`** when adding new features, changing dependencies, or modifying setup steps.
- **Comment non-obvious algorithms** especially OCR parameter tuning and image processing logic.
- **Add inline `# Reason:` comments** for complex business rules and optimization decisions.
- **Document PaddleOCR configuration** parameters and their effects on detection accuracy.

## ⚡ Performance & Optimization

### Frontend Performance
- **Implement image lazy loading** and progressive loading for large files
- **Use Web Workers** for heavy image processing tasks
- **Implement virtual scrolling** for large numbers of text regions
- **Use React.memo and useMemo** to prevent unnecessary re-renders
- **Optimize canvas rendering** with requestAnimationFrame for smooth interactions

### Backend Performance  
- **Use async/await** for all I/O operations including OCR and image processing
- **Implement task queues** (Celery/RQ) for long-running image processing
- **Add image caching** with Redis for processed results
- **Enable GPU acceleration** for PaddleOCR when available
- **Optimize database queries** and use connection pooling

## 🔒 Security Considerations
- **Validate all uploaded files** for type, size, and malicious content
- **Sanitize file names** and use UUIDs for internal file storage
- **Implement rate limiting** on API endpoints
- **Use secure file upload** with temporary directories and cleanup
- **Never expose internal file paths** in API responses
- **Log security events** including failed uploads and processing errors

## 🚀 Current Development Workflow

### Docker-Based Development Setup
```bash
# Full-stack development with Docker Compose
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000 (Nginx + React)
# - Backend API: http://localhost:8000 (FastAPI + Python 3.11)
# - IOPaint Service: http://localhost:8081 (FastAPI + IOPaint)
# - API Documentation: http://localhost:8000/docs (Swagger UI)

# Individual service development:
docker-compose up iopaint-service backend  # Backend services only
cd frontend && npm run dev                  # Frontend dev server with hot reload
```

### Quality Checklist Before Commits
- [ ] All tests pass (frontend and backend)
- [ ] OCR detection works on sample images
- [ ] Text removal preserves background quality
- [ ] UI is responsive and accessible
- [ ] API endpoints return proper error codes
- [ ] No hardcoded file paths or secrets
- [ ] Code follows style guidelines (black, eslint)
- [ ] Documentation is updated

### Adding New Features
1. **Create task in `TASK.md`** with clear acceptance criteria
2. **Write tests first** (TDD approach) for both frontend and backend
3. **Implement domain logic** following DDD patterns
4. **Add API endpoints** with proper validation and error handling
5. **Update frontend components** with new functionality
6. **Test OCR accuracy** and text removal quality manually
7. **Update documentation** including API docs and README

---

**IMPORTANT**: This document serves as the definitive guide for developing the LabelTool application. Follow these guidelines consistently to maintain code quality, performance, and user experience standards.