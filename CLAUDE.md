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
- **Backend**: FastAPI + Python 3.11 + Pydantic v2
- **OCR Engine**: PaddleOCR (latest version with PP-OCRv5 models)
- **Text Inpainting**: IOPaint with LAMA model for advanced text removal
- **Image Processing**: OpenCV + Pillow + Konva.js (canvas interactions)
- **State Management**: Zustand with persistence and undo/redo system
- **File Upload**: React-Dropzone with progress tracking
- **UI Components**: Custom Tailwind components + Lucide React icons
- **Container**: Docker + Docker Compose for full-stack deployment
- **Testing**: Jest + React Testing Library (Frontend), Pytest (Backend)

## 🧱 Code Structure & Modularity

### Current Directory Structure
```
labeltool/
├── frontend/                    # React TypeScript Frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ImageCanvas/     # Konva.js-based canvas with text regions
│   │   │   ├── FileUpload/      # Drag-and-drop file upload with progress
│   │   │   ├── Toolbar/         # Action buttons and processing controls
│   │   │   ├── EditableText/    # Inline text editing component
│   │   │   └── ui/              # Reusable UI components (Button, Toast, etc.)
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useCanvas.ts     # Canvas interaction logic
│   │   │   ├── useFileUpload.ts # File upload handling
│   │   │   ├── useKeyboardShortcuts.ts # Keyboard shortcuts
│   │   │   └── useToast.ts      # Toast notification system
│   │   ├── stores/              # Zustand state management
│   │   │   └── useAppStore.ts   # Main application state with undo/redo
│   │   ├── services/            # API communication services
│   │   │   └── api.ts           # RESTful API client
│   │   ├── types/               # TypeScript type definitions
│   │   │   └── index.ts         # Core application types
│   │   └── utils/               # Utility functions
│   │       ├── fontUtils.ts     # Font property utilities
│   │       └── undoCommands.ts  # Undo/redo command implementations
│   ├── Dockerfile               # Multi-stage build with Nginx
│   ├── nginx.conf               # Nginx configuration for SPA
│   └── package.json             # Dependencies and build scripts
├── backend/                     # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config/              # Configuration management
│   │   │   └── settings.py      # Pydantic settings with env support
│   │   ├── domain/              # Domain models and business logic
│   │   │   ├── entities/        # Core entities (LabelSession, TextRegion)
│   │   │   ├── value_objects/   # Value objects (Rectangle, Point, etc.)
│   │   │   └── services/        # Domain services
│   │   ├── application/         # Application layer
│   │   │   ├── use_cases/       # Use case implementations
│   │   │   │   ├── detect_text_regions.py      # OCR text detection
│   │   │   │   ├── process_text_removal.py     # IOPaint processing
│   │   │   │   ├── generate_text_in_regions.py # Text generation
│   │   │   │   └── update_text_regions.py      # Region updates
│   │   │   ├── dto/             # Data transfer objects
│   │   │   └── interfaces/      # Port definitions
│   │   ├── infrastructure/      # Infrastructure layer
│   │   │   ├── ocr/             # PaddleOCR integration
│   │   │   │   ├── global_ocr.py      # Global OCR instance
│   │   │   │   └── paddle_ocr_service.py # OCR service implementation
│   │   │   ├── image_processing/ # Image processing services
│   │   │   │   ├── iopaint_service.py # IOPaint text removal
│   │   │   │   ├── text_renderer.py   # Text generation rendering
│   │   │   │   └── font_analyzer.py   # Font detection
│   │   │   ├── storage/         # File system operations
│   │   │   │   └── file_storage.py    # File management service
│   │   │   └── api/             # FastAPI routes and models
│   │   │       ├── routes.py    # API endpoint definitions
│   │   │       └── models.py    # Pydantic response models
│   │   └── Dockerfile           # Python 3.11 with system dependencies
│   ├── requirements.txt         # Python dependencies
│   ├── uploads/                 # Original uploaded images
│   ├── processed/               # Processed result images
│   └── logs/                    # Application logs
├── docker-compose.yml           # Full-stack orchestration
└── README.md                    # Project documentation
```

### Code Organization Rules
- **Never create a file longer than 500 lines of code.** If approaching this limit, refactor into smaller modules.
- **Organize code into clearly separated modules** grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python-dotenv and load_dotenv()** for environment variables.
- **Follow DDD patterns**: Entities, Value Objects, Domain Services, Use Cases, and Infrastructure adapters.

## 🏗️ Core Domain Models & Architecture

### Current Backend Domain Models (Python)
```python
# Core Domain Entity - LabelSession (Aggregate Root)
@dataclass
class LabelSession:
    """Aggregate root for a labeling session with dual-mode support"""
    id: str
    original_image: ImageFile
    text_regions: List[TextRegion]                    # OCR detected regions (immutable positions)
    processed_text_regions: Optional[List[TextRegion]] = None  # User-modified regions for processed image
    processed_image: Optional[ImageFile] = None
    status: SessionStatus = SessionStatus.UPLOADED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

# Enhanced TextRegion Entity
@dataclass
class TextRegion:
    """Text region entity with advanced text editing capabilities"""
    id: str
    bounding_box: Rectangle
    confidence: float
    corners: List[Point]
    is_selected: bool = False
    is_user_modified: bool = False
    original_text: Optional[str] = None               # OCR detected text
    edited_text: Optional[str] = None                 # User-edited text (OCR mode)
    user_input_text: Optional[str] = None            # User-provided text (processed mode)
    font_properties: Optional[dict] = None           # Estimated font properties
    original_box_size: Optional[Rectangle] = None    # Original size for scaling
    is_size_modified: bool = False                   # Size modification tracking

# Value Objects
@dataclass(frozen=True)
class Rectangle:
    x: float
    y: float
    width: float
    height: float

@dataclass(frozen=True)
class Point:
    x: float
    y: float

# Session Status Enum
class SessionStatus(Enum):
    UPLOADED = "uploaded"
    DETECTING = "detecting"
    DETECTED = "detected"
    EDITING = "editing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    GENERATED = "generated"     # After text generation
    ERROR = "error"
```

### Current Frontend Domain Models (TypeScript)
```typescript
// Core Application State
interface LabelSession {
  id: string;
  original_image: ImageFile;
  text_regions: TextRegion[];                    // OCR regions
  processed_text_regions?: TextRegion[];        // Processed mode regions
  processed_image?: ImageFile;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

// Enhanced TextRegion Interface
interface TextRegion {
  id: string;
  bounding_box: Rectangle;
  confidence: number;
  corners: Point[];
  is_selected: boolean;
  is_user_modified: boolean;
  original_text?: string;                       // OCR detected text
  edited_text?: string;                         // User-edited text (OCR mode)
  user_input_text?: string;                     // User-provided text (processed mode)
  font_properties?: Record<string, any>;       // Font estimation data
  original_box_size?: Rectangle;                // Original bounding box
  is_size_modified?: boolean;                   // Size modification flag
}

// Application State with Undo System
interface AppState {
  currentSession: LabelSession | null;
  isLoading: boolean;
  error: string | null;
  canvasState: CanvasState;                     // Canvas interaction state
  processingState: {
    isProcessing: boolean;
    progress: ProcessingProgress | null;
    displayMode: 'original' | 'processed';     // Dual-mode support
    showRegionOverlay: boolean;
  };
  settings: UserSettings;
  undoState: UndoState;                         // Separate undo history per mode
}

// Undo System
interface UndoState {
  ocrHistory: UndoableCommand[];                // Undo history for OCR mode
  processedHistory: UndoableCommand[];          // Undo history for processed mode
  ocrCurrentIndex: number;
  processedCurrentIndex: number;
  maxHistorySize: number;
}

type SessionStatus = 
  | 'uploaded' | 'detecting' | 'detected' | 'editing' 
  | 'processing' | 'completed' | 'generated' | 'error';
```

## 🧪 Testing & Reliability
- **Always create Pytest unit tests for new backend features** (use cases, domain services, API endpoints).
- **Always create Jest/RTL tests for new frontend components** and custom hooks.
- **After updating any logic**, check whether existing tests need updates.
- **Tests should live in `/tests` folder** mirroring the main app structure.
- **Include at least**:
  - 1 test for expected behavior
  - 1 edge case test
  - 1 error/failure case test

### Testing Examples
```python
# Backend testing example
@pytest.mark.asyncio
async def test_detect_text_regions_use_case():
    use_case = DetectTextRegionsUseCase(mock_ocr_service, mock_image_service)
    result = await use_case.execute(mock_upload_file)
    
    assert result.status == SessionStatus.DETECTED
    assert len(result.text_regions) > 0
    assert all(region.confidence > 0 for region in result.text_regions)
```

```typescript
// Frontend testing example
test('TextRegionBox renders with correct dimensions', () => {
  const mockRegion = createMockTextRegion();
  render(<TextRegionBox region={mockRegion} onUpdate={jest.fn()} />);
  
  const box = screen.getByTestId('text-region-box');
  expect(box).toHaveStyle({
    width: `${mockRegion.boundingBox.width}px`,
    height: `${mockRegion.boundingBox.height}px`
  });
});
```

## ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- **Add new sub-tasks or TODOs** discovered during development to `TASK.md` under a "Discovered During Work" section.
- **Always test OCR accuracy** after making changes to image preprocessing or PaddleOCR configuration.
- **Always verify text removal quality** visually and programmatically after implementing new inpainting algorithms.

## 📎 Style & Conventions

### Python Backend Standards
- **Use Python 3.9+** as the primary language.
- **Follow PEP8** with `black` formatting and `isort` for imports.
- **Use Pydantic v2** for data validation and serialization.
- **Use FastAPI** for all API endpoints with proper OpenAPI documentation.
- **Use type hints everywhere** including return types and complex generics.
- **Write Google-style docstrings** for every function:

```python
async def detect_text_regions(self, image_path: str) -> List[TextRegion]:
    """
    Detect text regions in an image using PaddleOCR.

    Args:
        image_path (str): Path to the image file to process.

    Returns:
        List[TextRegion]: List of detected text regions with bounding boxes
                         and confidence scores.
        
    Raises:
        OCRProcessingError: If PaddleOCR fails to process the image.
        FileNotFoundError: If the image file doesn't exist.
    """
```

### TypeScript Frontend Standards
- **Use strict TypeScript configuration** with no implicit any.
- **Prefer functional components** with hooks over class components.
- **Use custom hooks** for complex state logic and side effects.
- **Follow React best practices**: memo, useMemo, useCallback for performance.
- **Use Tailwind CSS** for styling with consistent design tokens.

```typescript
// Good: Custom hook with proper typing
const useTextRegionEditor = (initialRegions: TextRegion[]) => {
  const [regions, setRegions] = useState<TextRegion[]>(initialRegions);
  
  const updateRegion = useCallback((regionId: string, updates: Partial<TextRegion>) => {
    setRegions(prev => prev.map(region => 
      region.id === regionId 
        ? { ...region, ...updates, isUserModified: true }
        : region
    ));
  }, []);

  return { regions, updateRegion };
};
```

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

### Color Scheme
```css
:root {
  --primary: #3B82F6;      /* Blue - primary actions */
  --secondary: #10B981;    /* Green - success states */
  --accent: #F59E0B;       /* Yellow - warnings */
  --danger: #EF4444;       /* Red - destructive actions */
  --neutral-50: #F9FAFB;   /* Background */
  --neutral-900: #111827;  /* Text */
}
```

## 🔧 Core Business Logic & Key Features

### Current Key Use Cases Implementation

#### 1. Text Detection with OCR (detect_text_regions.py)
```python
class DetectTextRegionsUseCase:
    """Use case for OCR text detection in images."""
    
    def __init__(self, ocr_service: OCRServicePort, image_service: ImageServicePort):
        self.ocr_service = ocr_service
        self.image_service = image_service
    
    async def execute(self, file_data: bytes, filename: str) -> LabelSession:
        """Execute text detection workflow with validation."""
        # Save uploaded image with validation
        image_file = await self.image_service.save_uploaded_image(file_data, filename)
        
        # Create new session
        session = LabelSession.create(image_file)
        session.transition_to_status(SessionStatus.DETECTING)
        
        # Detect text regions using PaddleOCR
        detected_regions = await self.ocr_service.detect_text_regions(image_file.path)
        
        # Add detected regions to session
        if detected_regions:
            session.add_text_regions(detected_regions)
        else:
            session.transition_to_status(SessionStatus.DETECTED)
            
        return session
```

#### 2. Advanced Text Removal with IOPaint (process_text_removal.py)
```python
class ProcessTextRemovalUseCase:
    """Use case for advanced text removal using IOPaint."""
    
    def __init__(self, inpainting_service: IOPaintService, file_service: FileStorageService):
        self.inpainting_service = inpainting_service
        self.file_service = file_service
    
    async def execute(self, session: LabelSession, inpainting_method: str = "iopaint") -> LabelSession:
        """Execute text removal with IOPaint service."""
        session.transition_to_status(SessionStatus.PROCESSING)
        
        # Start IOPaint service
        await self.inpainting_service.start_service()
        
        try:
            # Process text removal using IOPaint LAMA model
            processed_image_path = await self.inpainting_service.remove_text_regions(
                session.original_image.path,
                session.text_regions
            )
            
            # Save processed image
            processed_image = await self.file_service.save_processed_image(processed_image_path)
            session.set_processed_image(processed_image)
            
        finally:
            # Clean up IOPaint service
            await self.inpainting_service.stop_service()
        
        return session
```

#### 3. Text Generation and Replacement (generate_text_in_regions.py)
```python
class GenerateTextInRegionsUseCase:
    """Use case for generating custom text in processed images."""
    
    async def execute(self, session: LabelSession, regions_with_text: List[dict]) -> LabelSession:
        """Generate user-provided text in specified regions."""
        if not session.processed_image:
            raise ValueError("Session must have a processed image")
        
        # Initialize processed text regions if not exists
        session.initialize_processed_regions()
        
        # Render text using advanced text renderer
        text_renderer = TextRenderer(debug_positioning=True)
        
        generated_image_path = await text_renderer.render_text_in_regions(
            session.processed_image.path,
            regions_with_text,
            session.processed_text_regions,
            output_dir="processed"
        )
        
        # Update session with generated image
        generated_image = ImageFile.from_path(generated_image_path)
        session.processed_image = generated_image
        session.transition_to_status(SessionStatus.GENERATED)
        
        return session
```

#### 4. Dual-Mode Region Management (Frontend - useAppStore.ts)
```typescript
// Dual-mode region management with separate undo histories
const useAppStore = create<AppStore>()((set, get) => ({
  getCurrentDisplayRegions: () => {
    const state = get();
    if (!state.currentSession) return [];
    
    const isProcessedMode = state.processingState.displayMode === 'processed';
    if (isProcessedMode) {
      // Return processed_text_regions for text generation mode
      return state.currentSession.processed_text_regions || state.currentSession.text_regions;
    }
    // Return OCR text_regions for editing mode
    return state.currentSession.text_regions;
  },

  updateTextRegionWithUndo: (regionId, updates) => {
    const { processingState, updateTextRegion, getCurrentDisplayRegions } = get();
    const currentRegions = getCurrentDisplayRegions();
    const currentRegion = currentRegions.find(r => r.id === regionId);
    
    if (!currentRegion) return;
    
    const isProcessedMode = processingState.displayMode === 'processed';
    
    // Create appropriate undo command based on mode
    const editCommand = createEditTextCommand(
      regionId,
      isProcessedMode ? currentRegion.user_input_text : currentRegion.edited_text,
      isProcessedMode ? updates.user_input_text : updates.edited_text,
      isProcessedMode ? 'user_input_text' : 'edited_text',
      processingState.displayMode,
      updateTextRegion
    );
    
    // Add to appropriate undo history
    const historyType = isProcessedMode ? 'processedHistory' : 'ocrHistory';
    // ... undo history management
    
    updateTextRegion(regionId, updates);
  }
}));
```

## 🚀 Current API Design

### RESTful Endpoints (routes.py)
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

# Session State Management
PUT    /api/v1/sessions/{session_id}/restore   # Restore session state (undo support)
```

### Current API Response Models (models.py)
```python
class SessionDetailResponse(BaseModel):
    """Complete session details with dual-mode regions."""
    session: LabelSessionDTO

class LabelSessionDTO(BaseModel):
    """Enhanced session DTO with processed regions support."""
    id: str
    original_image: ImageFileDTO
    text_regions: List[TextRegionDTO]                # OCR regions
    processed_text_regions: Optional[List[TextRegionDTO]] = None  # Processed mode regions
    processed_image: Optional[ImageFileDTO] = None
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

class TextRegionDTO(BaseModel):
    """Enhanced text region with multiple text fields."""
    id: str
    bounding_box: RectangleDTO
    confidence: float
    corners: List[PointDTO]
    is_selected: bool = False
    is_user_modified: bool = False
    original_text: Optional[str] = None              # OCR detected text
    edited_text: Optional[str] = None                # User-edited text (OCR mode) 
    user_input_text: Optional[str] = None           # User-provided text (processed mode)
    font_properties: Optional[dict] = None          # Font estimation data
    original_box_size: Optional[RectangleDTO] = None
    is_size_modified: bool = False

class GenerateTextRequest(BaseModel):
    """Request model for text generation."""
    regions_with_text: List[RegionTextInput]

class RegionTextInput(BaseModel):
    region_id: str
    user_text: str

class ProcessingProgressResponse(BaseModel):
    """Enhanced processing progress with IOPaint stages."""
    session_id: str
    stage: Literal['starting', 'processing', 'finalizing']
    progress: float  # 0.0 to 100.0
    message: str
    start_time: Optional[float] = None
    estimated_time_remaining: Optional[int] = None

class HealthCheckResponse(BaseModel):
    """System health check with service details."""
    status: str
    timestamp: datetime
    version: str
    services: dict  # OCR, Storage, IOPaint status
```

## 📚 Documentation & Explainability
- **Update `README.md`** when adding new features, changing dependencies, or modifying setup steps.
- **Comment non-obvious algorithms** especially OCR parameter tuning and image processing logic.
- **Add inline `# Reason:` comments** for complex business rules and optimization decisions.
- **Document PaddleOCR configuration** parameters and their effects on detection accuracy.

### OCR Configuration Documentation
```python
# OCR service configuration with detailed parameter explanations
OCR_CONFIG = {
    "det_db_thresh": 0.3,        # Text detection threshold (lower = more sensitive)
    "det_db_box_thresh": 0.6,    # Bounding box threshold (higher = more precise)
    "det_limit_side_len": 1920,  # Max image dimension for processing
    "use_angle_cls": True,       # Enable text angle classification
    "lang": "en"                 # Primary language for recognition
}
```

## 🧠 AI Behavior Rules & Current Implementation Notes

### Critical Implementation Details
- **Dual-mode architecture**: The system supports both OCR editing mode and processed image text generation mode with separate region collections and undo histories.
- **IOPaint integration**: Text removal uses IOPaint service with LAMA model, requiring service startup/shutdown management.
- **Advanced text rendering**: Text generation includes font analysis, scaling calculations, and precise positioning with PIL anchoring.
- **Undo/redo system**: Separate command histories for OCR mode and processed mode with different command types.
- **Canvas interactions**: Uses Konva.js for interactive text region manipulation with drag-and-drop support.

### Technology-Specific Guidelines
- **Never assume missing context about current libraries**: IOPaint (1.6.0), PaddleOCR (latest with PP-OCRv5), Konva.js, Zustand.
- **Never hallucinate API endpoints or response models** – refer to the documented routes.py and models.py implementations.
- **Always use Docker for deployment** and reference docker-compose.yml for service configuration.
- **Session management**: Use in-memory session storage with proper cleanup for development.
- **File handling**: Use proper upload/processed directory separation with volume mounts.
- **Status transitions**: Follow the defined SessionStatus enum transitions in domain logic.

### Current Architecture Constraints
- **Backend uses DDD patterns** with clear domain/application/infrastructure separation.
- **Frontend uses Zustand** for state management with persistence and undo/redo.
- **Canvas rendering** uses Konva.js for interactive image editing capabilities.
- **Text regions have dual purposes**: OCR editing vs. text generation with different text fields.
- **Processing pipeline**: Upload → OCR → Edit → IOPaint → Generate → Download.

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
# - API Documentation: http://localhost:8000/docs (Swagger UI)

# Individual service development:
# Backend only
docker-compose up backend

# Frontend only (requires backend running)
cd frontend && npm run dev  # Development server on port 5173
```

### Local Development Setup (Alternative)
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup  
cd frontend
npm install
npm run dev

# Start services
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Current Docker Configuration
```yaml
# docker-compose.yml highlights
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - PADDLEOCR_DEVICE=cpu
      - IOPAINT_DEVICE=cpu
      - MAX_FILE_SIZE=52428800  # 50MB
    volumes:
      - backend_uploads:/app/uploads
      - backend_processed:/app/processed
      - huggingface_cache:/root/.cache/huggingface  # IOPaint model cache
      - paddlex_cache:/root/.paddlex              # PaddleOCR model cache
    
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on:
      backend: { condition: service_healthy }
```

### Adding New Features
1. **Create task in `TASK.md`** with clear acceptance criteria
2. **Write tests first** (TDD approach) for both frontend and backend
3. **Implement domain logic** following DDD patterns
4. **Add API endpoints** with proper validation and error handling
5. **Update frontend components** with new functionality
6. **Test OCR accuracy** and text removal quality manually
7. **Update documentation** including API docs and README

### Quality Checklist Before Commits
- [ ] All tests pass (frontend and backend)
- [ ] OCR detection works on sample images
- [ ] Text removal preserves background quality
- [ ] UI is responsive and accessible
- [ ] API endpoints return proper error codes
- [ ] No hardcoded file paths or secrets
- [ ] Code follows style guidelines (black, eslint)
- [ ] Documentation is updated

This CLAUDE.md serves as the definitive guide for developing the LabelTool application. Follow these guidelines consistently to maintain code quality, performance, and user experience standards.