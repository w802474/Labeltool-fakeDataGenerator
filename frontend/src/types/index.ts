// Core application types
export interface Point {
  x: number;
  y: number;
}

export interface Rectangle {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TextRegion {
  id: string;
  bounding_box: Rectangle;
  confidence: number;
  corners: Point[];
  is_selected: boolean;
  is_user_modified: boolean;
  original_text?: string;
  edited_text?: string; // User-modified text, if different from original_text
  user_input_text?: string; // User-provided text for text regeneration
  font_properties?: Record<string, any>; // Estimated font properties for text rendering
  original_box_size?: Rectangle; // Original bounding box size for scaling calculations
  is_size_modified?: boolean; // Whether the user has modified the box size
  text_category?: string; // Text classification category
  category_config?: {
    category: string;
    color: string;
    bgColor: string;
    label: string;
    description: string;
  }; // Category color and display configuration
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface ImageFile {
  id: string;
  filename: string;
  path: string;
  mime_type: string;
  size: number;
  dimensions: Dimensions;
}

export interface SessionData {
  id: string;
  original_image: ImageFile;
  processed_image: ImageFile | null;
  text_regions: TextRegion[];
  processed_text_regions?: TextRegion[];
  status: string;
  upload_timestamp: string;
  processing_timestamp?: string;
  completion_timestamp?: string;
}

export type SessionStatus = 
  | 'uploaded'
  | 'detecting'
  | 'detected' 
  | 'editing'
  | 'processing'
  | 'removed'
  | 'generated'
  | 'error';

export interface LabelSession {
  id: string;
  original_image: ImageFile;
  text_regions: TextRegion[];  // OCR detected regions (immutable positions)
  processed_text_regions?: TextRegion[];  // User-modified regions for processed image
  processed_image?: ImageFile;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message: string;
  status: 'success' | 'error';
}

export interface SessionResponse extends ApiResponse<LabelSession> {}

export interface HealthResponse extends ApiResponse<{
  status: string;
  timestamp: string;
  ocr: {
    available: boolean;
    device: string;
  };
  storage: {
    upload_dir: boolean;
    processed_dir: boolean;
  };
  sessions: {
    total_sessions: number;
    completed_sessions: number;
    failed_sessions: number;
  };
}> {}

// Tool types
export type CanvasTool = 'select' | 'pan' | 'create-region';

// UI State types
export interface CanvasState {
  scale: number;
  offset: Point;
  isDragging: boolean;
  selectedRegionId: string | null;
  isSelecting: boolean;
  selectionStart: Point | null;
  selectionEnd: Point | null;
  activeTool: CanvasTool;
}

export interface AppState {
  currentSession: LabelSession | null;
  isLoading: boolean;
  error: string | null;
  canvasState: CanvasState;
  processingState: {
    displayMode: ImageDisplayMode;
    showRegionOverlay: boolean;
  };
  settings: {
    darkMode: boolean;
    showConfidence: boolean;
    autoDetectText: boolean;
  };
  undoState: UndoState;
}

// Event types
export interface RegionUpdateEvent {
  regionId: string;
  bbox: Rectangle;
}

export interface RegionSelectEvent {
  regionId: string | null;
}

// Canvas interaction types
export interface CanvasInteraction {
  type: 'select' | 'move' | 'resize' | 'create';
  target: 'region' | 'canvas' | 'handle';
  data?: any;
}

// File upload types
export interface UploadProgress {
  progress: number;
  stage: 'uploading' | 'processing' | 'detecting' | 'complete';
  message: string;
}

// Removed deprecated processing types - now handled by WebSocket progress system

export type ImageDisplayMode = 'original' | 'processed';

// Toolbar types
export interface ToolbarAction {
  id: string;
  label: string;
  icon: React.ComponentType;
  action: () => void;
  disabled?: boolean;
  shortcut?: string;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Export utility types
export type DeepPartial<T> = {
  [P in keyof T]?: DeepPartial<T[P]>;
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Undo system types
export type UndoableCommandType = 
  | 'move_region' 
  | 'resize_region' 
  | 'add_region' 
  | 'delete_region' 
  | 'edit_text' 
  | 'generate_text';

export interface UndoableCommand {
  id: string;
  type: UndoableCommandType;
  execute: () => void;
  undo: () => void;
  timestamp: number;
  description: string;
  displayMode: ImageDisplayMode; // Track which mode this command was executed in
}

export interface UndoState {
  ocrHistory: UndoableCommand[];
  processedHistory: UndoableCommand[];
  ocrCurrentIndex: number;
  processedCurrentIndex: number;
  maxHistorySize: number;
}