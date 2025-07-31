import { useCallback, useRef, useEffect } from 'react';
import { Point, Rectangle, TextRegion } from '@/types';
import { useAppStore } from '@/stores/useAppStore';
import { 
  screenToCanvas, 
  canvasToScreen, 
  rectContainsPoint, 
  clamp,
  normalizeRect 
} from '@/utils';

export interface UseCanvasReturn {
  // Canvas manipulation
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
  fitToCanvas: (imageWidth: number, imageHeight: number, containerWidth: number, containerHeight: number) => void;
  
  // Coordinate conversion
  screenToCanvasCoords: (screenPoint: Point) => Point;
  canvasToScreenCoords: (canvasPoint: Point) => Point;
  
  // Region manipulation
  createRegionFromSelection: (start: Point, end: Point) => Rectangle;
  isPointInRegion: (point: Point, region: TextRegion) => boolean;
  getRegionAtPoint: (point: Point, regions: TextRegion[]) => TextRegion | null;
  
  // Canvas state
  canvasRef: React.RefObject<HTMLDivElement>;
  isDragging: boolean;
  selectedRegionId: string | null;
  scale: number;
  offset: Point;
}

export const useCanvas = (): UseCanvasReturn => {
  const canvasRef = useRef<HTMLDivElement>(null);
  
  const {
    canvasState,
    setCanvasScale,
    setCanvasOffset,
    setCanvasDragging,
    setSelectedRegion,
    currentSession,
  } = useAppStore();

  const { scale, offset, isDragging, selectedRegionId } = canvasState;

  // Zoom controls
  const zoomIn = useCallback(() => {
    const newScale = clamp(scale * 1.2, 0.1, 5);
    setCanvasScale(newScale);
  }, [scale, setCanvasScale]);

  const zoomOut = useCallback(() => {
    const newScale = clamp(scale / 1.2, 0.1, 5);
    setCanvasScale(newScale);
  }, [scale, setCanvasScale]);

  const resetZoom = useCallback(() => {
    setCanvasScale(1);
    setCanvasOffset({ x: 0, y: 0 });
  }, [setCanvasScale, setCanvasOffset]);

  const fitToCanvas = useCallback((
    imageWidth: number,
    imageHeight: number,
    containerWidth: number,
    containerHeight: number
  ) => {
    // Add some padding to ensure image fits comfortably within container
    const padding = 20;
    const availableWidth = containerWidth - padding * 2;
    const availableHeight = containerHeight - padding * 2;
    
    const scaleX = availableWidth / imageWidth;
    const scaleY = availableHeight / imageHeight;
    const fitScale = Math.min(scaleX, scaleY); // Ensure image fits completely
    
    // Clamp scale to reasonable values
    const finalScale = Math.max(0.1, Math.min(fitScale, 2.0));
    
    setCanvasScale(finalScale);
    
    // Center the image in the container
    const scaledWidth = imageWidth * finalScale;
    const scaledHeight = imageHeight * finalScale;
    const offsetX = (containerWidth - scaledWidth) / 2;
    const offsetY = (containerHeight - scaledHeight) / 2;
    
    setCanvasOffset({ x: offsetX, y: offsetY });
  }, [setCanvasScale, setCanvasOffset]);

  // Coordinate conversion
  const screenToCanvasCoords = useCallback((screenPoint: Point): Point => {
    return screenToCanvas(screenPoint, offset, scale);
  }, [offset, scale]);

  const canvasToScreenCoords = useCallback((canvasPoint: Point): Point => {
    return canvasToScreen(canvasPoint, offset, scale);
  }, [offset, scale]);

  // Region utilities
  const createRegionFromSelection = useCallback((start: Point, end: Point): Rectangle => {
    const canvasStart = screenToCanvasCoords(start);
    const canvasEnd = screenToCanvasCoords(end);
    
    return normalizeRect({
      x: Math.min(canvasStart.x, canvasEnd.x),
      y: Math.min(canvasStart.y, canvasEnd.y),
      width: Math.abs(canvasEnd.x - canvasStart.x),
      height: Math.abs(canvasEnd.y - canvasStart.y),
    });
  }, [screenToCanvasCoords]);

  const isPointInRegion = useCallback((point: Point, region: TextRegion): boolean => {
    const canvasPoint = screenToCanvasCoords(point);
    return rectContainsPoint(region.bounding_box, canvasPoint);
  }, [screenToCanvasCoords]);

  const getRegionAtPoint = useCallback((
    point: Point, 
    regions: TextRegion[]
  ): TextRegion | null => {
    // Find regions that contain the point, prioritize smaller regions (on top)
    const containingRegions = regions
      .filter(region => isPointInRegion(point, region))
      .sort((a, b) => {
        const areaA = a.bounding_box.width * a.bounding_box.height;
        const areaB = b.bounding_box.width * b.bounding_box.height;
        return areaA - areaB; // Ascending order (smaller first)
      });
    
    return containingRegions[0] || null;
  }, [isPointInRegion]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '=':
          case '+':
            event.preventDefault();
            zoomIn();
            break;
          case '-':
            event.preventDefault();
            zoomOut();
            break;
          case '0':
            event.preventDefault();
            resetZoom();
            break;
        }
      }
      
      // ESC to deselect
      if (event.key === 'Escape') {
        setSelectedRegion(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [zoomIn, zoomOut, resetZoom, setSelectedRegion]);

  // Mouse wheel zoom with trackpad optimization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let lastZoomTime = 0;
    let zoomAccumulator = 0;

    const handleWheel = (event: WheelEvent) => {
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        
        const now = Date.now();
        const timeSinceLastZoom = now - lastZoomTime;
        
        // Detect if this is likely a trackpad (smaller, more frequent events)
        const isTrackpad = Math.abs(event.deltaY) < 50 && timeSinceLastZoom < 50;
        
        // Different zoom sensitivity for trackpad vs mouse wheel
        let zoomSensitivity;
        if (isTrackpad) {
          // Much more gentle for trackpad
          zoomSensitivity = 0.002;
        } else {
          // Standard sensitivity for mouse wheel
          zoomSensitivity = 0.1;
        }
        
        // Accumulate zoom for smooth trackpad experience
        zoomAccumulator += event.deltaY * zoomSensitivity;
        
        // Apply zoom if enough accumulation or if it's been a while
        if (Math.abs(zoomAccumulator) > 0.02 || timeSinceLastZoom > 100) {
          const rect = canvas.getBoundingClientRect();
          const mousePoint = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          };
          
          const canvasPoint = screenToCanvasCoords(mousePoint);
          
          // Calculate zoom factor from accumulator
          const zoomChange = -zoomAccumulator; // Negative for natural direction
          const zoomFactor = 1 + zoomChange;
          const newScale = clamp(scale * zoomFactor, 0.1, 5);
          
          // Only update if scale actually changed
          if (Math.abs(newScale - scale) > 0.001) {
            // Zoom towards mouse position
            const newOffset = {
              x: mousePoint.x - (canvasPoint.x * newScale),
              y: mousePoint.y - (canvasPoint.y * newScale),
            };
            
            setCanvasScale(newScale);
            setCanvasOffset(newOffset);
          }
          
          // Reset accumulator and update time
          zoomAccumulator = 0;
          lastZoomTime = now;
        }
      }
    };

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, [scale, offset, setCanvasScale, setCanvasOffset, screenToCanvasCoords]);

  return {
    // Canvas manipulation
    zoomIn,
    zoomOut,
    resetZoom,
    fitToCanvas,
    
    // Coordinate conversion
    screenToCanvasCoords,
    canvasToScreenCoords,
    
    // Region manipulation
    createRegionFromSelection,
    isPointInRegion,
    getRegionAtPoint,
    
    // Canvas state
    canvasRef,
    isDragging,
    selectedRegionId,
    scale,
    offset,
  };
};