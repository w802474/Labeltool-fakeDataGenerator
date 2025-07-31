# LabelTool - Intelligent Text Detection & Removal Tool

## CURRENT IMPLEMENTED FEATURES:

- **Dual-Mode Text Processing System**: OCR editing mode for text detection/correction + Processed mode for text generation/replacement
- **Advanced OCR Integration**: PaddleOCR with PP-OCRv5 models for high-precision text detection and recognition
- **Interactive Canvas Editing**: Konva.js-powered canvas with drag-and-drop text region manipulation, resize handles, and real-time updates
- **IOPaint Text Removal**: Advanced AI-powered text inpainting using IOPaint LAMA model for seamless background preservation
- **Custom Text Generation**: Font-aware text rendering with automatic font analysis, scaling, and precise positioning
- **Comprehensive Undo/Redo System**: Separate command histories for OCR and processed modes with full state restoration
- **Docker-Based Deployment**: Full-stack containerization with docker-compose orchestration and persistent volumes
- **Real-Time Progress Tracking**: WebSocket-like progress updates for long-running operations (OCR, inpainting, text generation)
- **Session Management**: Complete session lifecycle with automatic cleanup and file management
- **Multi-Format Support**: JPEG, PNG, WEBP with validation, size limits (50MB), and secure handling

## ARCHITECTURE:

### Frontend (React 18 + TypeScript + Vite):
- **React 18** with strict TypeScript configuration and Vite for fast development and HMR
- **Konva.js** for high-performance canvas-based image editing with interactive text regions
- **Zustand** for state management with persistence, undo/redo system, and devtools integration
- **Tailwind CSS** with custom design tokens for consistent, responsive styling
- **React-Dropzone** for secure file upload with progress tracking and validation
- **Custom Hooks Ecosystem**: useCanvas, useKeyboardShortcuts, useToast, useFileUpload, useRegionSync
- **Lucide React Icons** for consistent iconography throughout the application

### Backend (FastAPI + Python 3.11):
- **FastAPI** with Pydantic v2 for robust API validation, automatic OpenAPI documentation, and async support
- **Domain-Driven Design (DDD)** with clean architecture: Domain → Application → Infrastructure layers
- **PaddleOCR Integration** with global instance management and PP-OCRv5 models for optimal text detection
- **IOPaint Service** with LAMA model for advanced AI-powered text inpainting and background preservation
- **Advanced Text Renderer** with PIL-based font analysis, scaling calculations, and precise text positioning
- **Comprehensive Error Handling** with custom exception types and structured error responses
- **File Management System** with secure upload/processed directory separation and automatic cleanup

### Current Key Components:
- `ImageCanvas/` - Konva.js-powered canvas with interactive text region editing, selection, and real-time updates
- `EditableText/` - Inline text editing component supporting both OCR correction and text generation modes
- `Toolbar/` - Action buttons with processing controls, mode switching, and operation management  
- `FileUpload/` - Drag-and-drop upload with progress indicators, validation, and error handling
- `Toast System/` - Non-intrusive notification system for operation feedback and error reporting
- `StatusBar/` - Real-time processing progress with stage indicators and time estimation

## KEY IMPLEMENTATION EXAMPLES:

### Current Working Examples in Codebase:

#### Frontend Examples:
- `useAppStore.ts` - Comprehensive Zustand store with dual-mode support, undo/redo system, and async operations
- `ImageCanvas/ImageCanvas.tsx` - Konva.js canvas implementation with interactive text regions and real-time editing
- `EditableText/EditableText.tsx` - Inline text editing with mode-aware behavior (OCR vs. processed)
- `useKeyboardShortcuts.ts` - System-wide keyboard shortcuts with conflict resolution
- `undoCommands.ts` - Command pattern implementation for undo/redo operations

#### Backend Examples:
- `detect_text_regions.py` - Complete OCR workflow with error handling and status management
- `process_text_removal.py` - IOPaint integration with service lifecycle management
- `generate_text_in_regions.py` - Advanced text rendering with font analysis and positioning
- `text_renderer.py` - PIL-based text rendering with scaling and anchor positioning
- `routes.py` - Comprehensive FastAPI endpoints with proper error handling and validation

#### Configuration Examples:
- `docker-compose.yml` - Full-stack containerization with health checks and volume management
- `settings.py` - Pydantic settings with environment variable support and validation
- `main.py` - FastAPI application setup with middleware, logging, and startup events

Use these actual implementations as reference for understanding the current architecture patterns, error handling strategies, and integration approaches.

## DOCUMENTATION:

### Current Core Technologies:
- **FastAPI**: https://fastapi.tiangolo.com/ (API framework with automatic OpenAPI docs)
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR (PP-OCRv5 models for text detection)
- **IOPaint**: https://github.com/Sanster/IOPaint (LAMA model for text inpainting)
- **React 18**: https://react.dev/ (Frontend framework with concurrent features)
- **Konva.js**: https://konvajs.org/ (2D canvas library for interactive graphics)
- **TypeScript**: https://www.typescriptlang.org/ (Type-safe JavaScript)
- **Tailwind CSS**: https://tailwindcss.com/ (Utility-first CSS framework)
- **Zustand**: https://zustand-demo.pmnd.rs/ (Lightweight state management)
- **Docker**: https://docs.docker.com/ (Containerization and deployment)

### Specialized Libraries:
- **Pillow (PIL)**: https://pillow.readthedocs.io/ (Advanced image processing and text rendering)
- **OpenCV**: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html (Computer vision and image manipulation)
- **React-Dropzone**: https://react-dropzone.js.org/ (File upload component)
- **Lucide React**: https://lucide.dev/ (Icon library)
- **Loguru**: https://loguru.readthedocs.io/ (Advanced Python logging)

### Architecture & Testing Resources:
- **Domain-Driven Design**: https://martinfowler.com/bliki/DomainDrivenDesign.html
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- **React Testing Library**: https://testing-library.com/docs/react-testing-library/intro/
- **Pytest**: https://docs.pytest.org/
- **Docker Compose**: https://docs.docker.com/compose/

## CURRENT PROJECT STRUCTURE:

```
labeltool/
├── frontend/                    # React TypeScript Frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ImageCanvas/     # Konva.js-based interactive canvas
│   │   │   ├── FileUpload/      # Drag-and-drop upload with progress
│   │   │   ├── Toolbar/         # Processing controls and mode switching
│   │   │   ├── EditableText/    # Dual-mode text editing component
│   │   │   ├── Header.tsx       # Application header with actions
│   │   │   ├── StatusBar.tsx    # Progress and status display
│   │   │   ├── ErrorBoundary.tsx # Error handling boundary
│   │   │   └── ui/              # Reusable UI components
│   │   │       ├── Button.tsx, Card.tsx, Toast.tsx
│   │   │       ├── ConfirmDialog.tsx, Progress.tsx
│   │   │       └── LaserScanAnimation.tsx
│   │   ├── hooks/               # Custom React hooks ecosystem
│   │   │   ├── useCanvas.ts     # Canvas interaction management
│   │   │   ├── useFileUpload.ts # File upload handling
│   │   │   ├── useKeyboardShortcuts.ts # System-wide shortcuts
│   │   │   ├── useRegionSync.ts # Region selection synchronization
│   │   │   ├── useConfirmDialog.ts # Dialog state management
│   │   │   └── useToast.ts      # Toast notification system
│   │   ├── stores/              # Zustand state management
│   │   │   └── useAppStore.ts   # Main store with undo/redo system
│   │   ├── services/            # API communication
│   │   │   └── api.ts           # RESTful API client with validation
│   │   ├── types/               # TypeScript definitions
│   │   │   └── index.ts         # Complete type system
│   │   └── utils/               # Utility functions
│   │       ├── fontUtils.ts     # Font property calculations
│   │       ├── undoCommands.ts  # Command pattern implementation
│   │       └── index.ts         # Utility exports
│   ├── Dockerfile               # Multi-stage build with Nginx
│   ├── nginx.conf               # Nginx configuration for SPA
│   ├── package.json             # Dependencies and scripts
│   ├── tailwind.config.js       # Tailwind customization
│   ├── tsconfig.json            # Strict TypeScript config
│   └── vite.config.ts           # Vite build configuration
├── backend/                     # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py              # FastAPI app with middleware & events
│   │   ├── config/              # Configuration management
│   │   │   └── settings.py      # Pydantic settings with validation
│   │   ├── domain/              # Domain layer (DDD)
│   │   │   ├── entities/        # Aggregate roots
│   │   │   │   ├── label_session.py # Session aggregate
│   │   │   │   └── text_region.py   # Text region entity
│   │   │   ├── value_objects/   # Immutable value objects
│   │   │   │   ├── rectangle.py, point.py, image_file.py
│   │   │   │   └── session_status.py # Status enum
│   │   │   └── services/        # Domain services
│   │   ├── application/         # Application layer
│   │   │   ├── use_cases/       # Business use cases
│   │   │   │   ├── detect_text_regions.py      # OCR workflow
│   │   │   │   ├── process_text_removal.py     # IOPaint processing
│   │   │   │   ├── generate_text_in_regions.py # Text generation
│   │   │   │   └── update_text_regions.py      # Region updates
│   │   │   ├── dto/             # Data transfer objects
│   │   │   │   └── session_dto.py # Session DTOs
│   │   │   └── interfaces/      # Port definitions
│   │   │       ├── ocr_service.py, image_service.py
│   │   ├── infrastructure/      # Infrastructure layer
│   │   │   ├── ocr/             # OCR integration
│   │   │   │   ├── global_ocr.py        # Singleton OCR instance
│   │   │   │   ├── paddle_ocr_service.py # PaddleOCR service
│   │   │   │   └── ocr_config.py        # OCR configuration
│   │   │   ├── image_processing/ # Image processing services
│   │   │   │   ├── iopaint_service.py   # IOPaint integration
│   │   │   │   ├── text_renderer.py     # Advanced text rendering
│   │   │   │   ├── font_analyzer.py     # Font detection/analysis
│   │   │   │   ├── image_resizer.py     # Image scaling utilities
│   │   │   │   └── document_detector.py # Document detection
│   │   │   ├── storage/         # File management
│   │   │   │   └── file_storage.py      # File operations service
│   │   │   └── api/             # REST API layer
│   │   │       ├── routes.py            # API endpoints
│   │   │       └── models.py            # Pydantic response models
│   │   └── Dockerfile           # Python 3.11 with system deps
│   ├── requirements.txt         # Python dependencies
│   ├── debug_fonts.py          # Font debugging utility
│   ├── uploads/                # Original uploaded images
│   ├── processed/              # Processed result images
│   ├── exports/                # Export directory
│   └── logs/                   # Application logs
├── docker-compose.yml          # Full-stack orchestration
├── README.md                   # Setup and usage documentation
├── CLAUDE.md                   # Development guidelines
├── INITIAL.md                  # Project overview (this file)
├── DOCKER.md                   # Docker deployment guide
└── PRPs/                       # Project requirements and planning
    └── labeltool-text-detection-removal.md
```

## DEPLOYMENT & DEVELOPMENT:

### Current Deployment Method - Docker Compose:
```bash
# Full-stack deployment (recommended)
docker-compose up --build

# Services available at:
# - Frontend: http://localhost:3000 (Nginx + React production build)
# - Backend API: http://localhost:8000 (FastAPI with Python 3.11)
# - API Documentation: http://localhost:8000/docs (OpenAPI/Swagger)
# - Health Check: http://localhost:8000/api/v1/health
```

### Environment Configuration:
- **Docker-based deployment** with persistent volumes for uploads, processed images, and model caches
- **Environment variables** configured in docker-compose.yml for production settings
- **Health checks** implemented for both frontend and backend containers
- **Model caching** with dedicated volumes for PaddleOCR and IOPaint models
- **Log management** with rotation and retention policies

### Current Key Configuration Files:
- `docker-compose.yml` - Full-stack orchestration with health checks and volumes
- `backend/Dockerfile` - Python 3.11 with system dependencies and font support
- `frontend/Dockerfile` - Multi-stage build with Nginx for production serving
- `backend/requirements.txt` - Python dependencies (FastAPI, PaddleOCR, IOPaint, etc.)
- `frontend/package.json` - Node.js dependencies (React 18, Konva.js, Zustand, etc.)
- `frontend/nginx.conf` - Nginx configuration for SPA routing and API proxying
- `backend/app/config/settings.py` - Pydantic settings with environment variable support

### Current API Endpoints (v1):
```
# Core Session Management
POST   /api/v1/sessions                        # Create session with OCR
GET    /api/v1/sessions/{session_id}           # Get complete session details
PUT    /api/v1/sessions/{session_id}/regions   # Update text regions (dual-mode)
DELETE /api/v1/sessions/{session_id}           # Clean up session and files

# Processing Operations
POST   /api/v1/sessions/{session_id}/process   # Text removal with IOPaint
GET    /api/v1/sessions/{session_id}/estimate  # Processing time estimate

# Text Generation Features
POST   /api/v1/sessions/{session_id}/generate-text # Generate custom text
POST   /api/v1/sessions/{session_id}/preview-text  # Preview text generation

# File Operations
GET    /api/v1/sessions/{session_id}/image     # Get original image
GET    /api/v1/sessions/{session_id}/result    # Download processed result

# System Management
GET    /api/v1/health                          # Service health check
GET    /api/v1/info                            # Service configuration
PUT    /api/v1/sessions/{session_id}/restore   # Restore session state (undo)
```

### Current Performance Features:
- **Frontend**: Konva.js hardware acceleration, Zustand optimized state updates, React.memo for components
- **Backend**: Async FastAPI with global OCR instance, IOPaint service lifecycle management
- **Canvas**: Optimized rendering with selective region updates and efficient event handling
- **State Management**: Separate undo histories per mode, command pattern for efficient operations
- **File Handling**: Streaming uploads with progress tracking, automatic cleanup of temporary files

### Current Quality Assurance:
- **Type Safety**: Strict TypeScript configuration with comprehensive type definitions
- **Code Organization**: DDD architecture with clear separation of concerns
- **Error Handling**: Comprehensive error boundaries and structured error responses
- **Logging**: Loguru-based logging with rotation and structured output
- **Container Health**: Docker health checks for both frontend and backend services

### Critical Implementation Notes for AI Assistants:

#### Current Architecture Patterns:
- **Dual-mode system**: OCR editing mode vs. processed image text generation mode with separate region collections
- **Undo/redo system**: Command pattern with separate histories for each mode (ocrHistory, processedHistory)
- **Session state management**: LabelSession aggregate with status transitions and validation
- **Canvas interactions**: Konva.js-based with interactive text regions, drag handles, and real-time updates

#### Key Technology Integrations:
- **IOPaint service**: Requires startup/shutdown lifecycle management with LAMA model
- **PaddleOCR**: Global instance with PP-OCRv5 models and caching for performance
- **Text rendering**: Advanced PIL-based rendering with font analysis and scaling calculations
- **Docker deployment**: Multi-stage builds with persistent volumes for model caching

#### Current Domain Logic:
- **Text regions have multiple text fields**: original_text (OCR), edited_text (OCR mode), user_input_text (processed mode)
- **Status transitions**: Follow SessionStatus enum with validation (uploaded → detecting → detected → editing → processing → completed → generated)
- **Region management**: Separate text_regions (OCR) and processed_text_regions (processed mode) collections
- **File handling**: Upload/processed directory separation with automatic cleanup and volume mounts

This project represents a fully-implemented, production-ready text detection and processing system with advanced AI integration, interactive UI, and comprehensive Docker deployment.
