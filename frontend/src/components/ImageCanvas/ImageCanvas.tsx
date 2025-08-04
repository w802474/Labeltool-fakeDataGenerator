import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect, Text, Line } from 'react-konva';
// @ts-ignore
import useImage from 'use-image';
import { useAppStore } from '@/stores/useAppStore';
import { useCanvas } from '@/hooks/useCanvas';
import { TextRegion, Point, Rectangle } from '@/types';
import { clsx } from 'clsx';
import { Card } from '@/components/ui/Card';
import { LaserScanAnimation } from '@/components/ui/LaserScanAnimation';
import { TextClassificationLegend } from '@/components/ui/TextClassificationLegend';
import { useProcessingProgress } from '@/hooks/useProcessingProgress';
import { apiService } from '@/services/api';
import { Loader2 } from 'lucide-react';
import { 
  calculatePreviewFontSize, 
  getFontFamily, 
  getFontColor, 
  getFontWeight, 
  getFontStyle 
} from '@/utils/fontUtils';

interface ImageCanvasProps {
  className?: string;
}

// Dynamic container sizing - fit within the 3/4 grid column
const getContainerDimensions = () => {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  
  // Calculate available space in the 3/4 grid column
  // Container padding + gap + sidebar width (1/4) = ~25% + padding
  const sidebarAndPadding = 350; // Sidebar width + gaps + padding
  const headerAndFooter = 200; // Header, toolbar, status bar heights
  
  const availableWidth = Math.max(600, viewportWidth - sidebarAndPadding);
  const availableHeight = Math.max(400, viewportHeight - headerAndFooter);
  
  return {
    width: Math.min(availableWidth, 1200), // Max width to prevent too large
    height: Math.min(availableHeight, 800), // Max height to prevent too large
  };
};

export const ImageCanvas: React.FC<ImageCanvasProps> = ({ className }) => {
  const { 
    currentSession, 
    setSelectedRegion, 
    canvasState, 
    updateTextRegion, 
    moveRegionWithUndo,
    resizeRegionWithUndo,
    settings,
    processingState,
    getCurrentDisplayRegions,
    currentTaskId,
    setCurrentTaskId,
    setCurrentSession,
    setImageDisplayMode
  } = useAppStore();
  const { 
    canvasRef, 
    scale, 
    offset, 
    screenToCanvasCoords, 
    getRegionAtPoint,
    fitToCanvas 
  } = useCanvas();
  
  const stageRef = useRef<any>(null);

  // Processing progress data for laser scan animation
  const progressData = useProcessingProgress({
    taskId: currentTaskId,
    onComplete: async (result) => {
      console.log('✅ Processing completed:', result);
      
      // Refresh session to get the latest data (including processed image)
      if (currentSession) {
        try {
          const updatedSession = await apiService.getSession(currentSession.id);
          setCurrentSession(updatedSession);
          setImageDisplayMode('processed');
        } catch (error) {
          console.error('Failed to refresh session after completion:', error);
          // Still switch to processed mode even if refresh fails
          setImageDisplayMode('processed');
        }
      }
      
      // Clear task ID
      setCurrentTaskId(null);
    },
    onCancel: () => {
      console.log('❌ Processing cancelled');
      setCurrentTaskId(null);
    },
    onError: (error) => {
      console.error('💥 Processing failed:', error);
      setCurrentTaskId(null);
    }
  });
  
  // Determine image URL based on display mode and session state
  const getImageUrl = () => {
    if (!currentSession) return '';
    
    // If display mode is 'processed' and we have a processed image, show it
    if (processingState.displayMode === 'processed' && currentSession.processed_image) {
      // Add cache-busting parameter using the session's updated timestamp
      const timestamp = new Date(currentSession.updated_at).getTime();
      return `/api/v1/sessions/${currentSession.id}/result?t=${timestamp}`;
    }
    
    // Otherwise show original image
    return `/api/v1/sessions/${currentSession.id}/image`;
  };
  
  const [image] = useImage(getImageUrl());
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<Point | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);
  const [clickedRegionId, setClickedRegionId] = useState<string | null>(null);
  const [containerDimensions, setContainerDimensions] = useState(getContainerDimensions());
  const [actualContainerSize, setActualContainerSize] = useState({ width: 800, height: 600 });
  const [isImageDragging, setIsImageDragging] = useState(false);
  const [imageDragStart, setImageDragStart] = useState<Point | null>(null);
  const [lastOffset, setLastOffset] = useState<Point>({ x: 0, y: 0 });
  
  // Region manipulation states
  const [draggedRegionId, setDraggedRegionId] = useState<string | null>(null);
  const [draggedHandle, setDraggedHandle] = useState<string | null>(null); // 'tl', 'tr', 'bl', 'br', 'move'
  const [initialRegionBounds, setInitialRegionBounds] = useState<Rectangle | null>(null);
  const [regionDragStart, setRegionDragStart] = useState<Point | null>(null);
  
  // Cursor state management
  const [currentCursor, setCurrentCursor] = useState<string>('default');
  
  // Track if we just finished a drag operation to prevent unwanted clicks
  const [justFinishedDragging, setJustFinishedDragging] = useState(false);
  
  // Track if user is currently interacting (dragging regions or image)
  const [isUserInteracting, setIsUserInteracting] = useState(false);
  

  // Get the current display regions based on the display mode
  // Removed useMemo to ensure fresh data on every render
  const currentDisplayRegions = getCurrentDisplayRegions();

  // Grid rendering with dynamic scaling
  const renderGrid = useMemo(() => {
    if (!currentSession) return [];

    const baseGridSpacing = 20; // Base grid spacing at 1x scale
    const gridSpacing = baseGridSpacing * scale;
    
    // Only render if grid spacing is reasonable (not too small or too large)
    if (gridSpacing < 5 || gridSpacing > 200) return [];

    const lines = [];
    const containerWidth = actualContainerSize.width;
    const containerHeight = actualContainerSize.height;

    // Calculate visible grid area
    const padding = gridSpacing * 2;
    
    // Calculate grid boundaries in screen coordinates
    const minX = -padding;
    const maxX = containerWidth + padding;
    const minY = -padding;
    const maxY = containerHeight + padding;

    // Grid line color based on theme
    const gridColor = settings.darkMode ? '#475569' : '#cbd5e1'; // Dark mode: slate-600, Light mode: slate-300
    const gridOpacity = 0.4;

    // Generate vertical lines
    // Start from a grid-aligned position and extend across the entire visible area
    const firstVerticalLine = Math.floor(minX / gridSpacing) * gridSpacing;
    const lastVerticalLine = Math.ceil(maxX / gridSpacing) * gridSpacing;
    
    for (let x = firstVerticalLine; x <= lastVerticalLine; x += gridSpacing) {
      lines.push(
        <Line
          key={`v-${x}`}
          points={[x, minY, x, maxY]}
          stroke={gridColor}
          strokeWidth={1}
          opacity={gridOpacity}
          listening={false}
        />
      );
    }

    // Generate horizontal lines
    const firstHorizontalLine = Math.floor(minY / gridSpacing) * gridSpacing;
    const lastHorizontalLine = Math.ceil(maxY / gridSpacing) * gridSpacing;
    
    for (let y = firstHorizontalLine; y <= lastHorizontalLine; y += gridSpacing) {
      lines.push(
        <Line
          key={`h-${y}`}
          points={[minX, y, maxX, y]}
          stroke={gridColor}
          strokeWidth={1}
          opacity={gridOpacity}
          listening={false}
        />
      );
    }

    return lines;
  }, [scale, offset, actualContainerSize, currentSession, settings.darkMode]);

  // Measure actual container size
  useEffect(() => {
    const updateActualSize = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        const newSize = {
          width: Math.floor(rect.width) || 800,
          height: containerDimensions.height
        };
        setActualContainerSize(newSize);
        
        // Only re-fit image to new container size if there's a significant size change
        // and user is not currently interacting with the image/regions
        if (image && currentSession && imageLoaded && !isUserInteracting) {
          const sizeDiffThreshold = 50; // Only refit if size changes by more than 50px
          const widthDiff = Math.abs(newSize.width - actualContainerSize.width);
          
          if (widthDiff > sizeDiffThreshold) {
            fitToCanvas(
              currentSession.original_image.dimensions.width,
              currentSession.original_image.dimensions.height,
              newSize.width,
              newSize.height
            );
          }
        }
      }
    };
    
    // Initial measurement
    updateActualSize();
    
    // Handle window resize
    const handleResize = () => {
      const newDimensions = getContainerDimensions();
      setContainerDimensions(newDimensions);
      setTimeout(updateActualSize, 0); // Measure after layout update
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [image, currentSession, fitToCanvas, imageLoaded, containerDimensions, isUserInteracting]);

  // Fit image to canvas when first loaded
  useEffect(() => {
    if (image && currentSession && !imageLoaded && actualContainerSize.width > 0) {
      fitToCanvas(
        currentSession.original_image.dimensions.width,
        currentSession.original_image.dimensions.height,
        actualContainerSize.width,
        actualContainerSize.height
      );
      setImageLoaded(true);
    }
  }, [image, currentSession, fitToCanvas, imageLoaded, actualContainerSize]);

  // Handle canvas click
  const handleCanvasClick = useCallback((e: any) => {
    const pos = e.target.getStage().getPointerPosition();
    if (!pos || !currentSession) return;

    // Don't handle click if we were dragging anything (image or region)
    if (isImageDragging || draggedRegionId) return;

    // Don't handle click if we just finished dragging (prevents unwanted deselection)
    if (justFinishedDragging) {
      setJustFinishedDragging(false);
      return;
    }

    // Check if regions should be interactive before detecting clicks
    const shouldRegionsBeInteractive = (() => {
      if (processingState.displayMode === 'original' || !!currentTaskId) {
        return true;
      }
      if (processingState.displayMode === 'processed') {
        return processingState.showRegionOverlay;
      }
      return false;
    })();

    if (shouldRegionsBeInteractive) {
      const clickedRegion = getRegionAtPoint(pos, currentDisplayRegions);
      if (clickedRegion) {
        // Toggle clicked region for persistent text display
        setClickedRegionId(prev => prev === clickedRegion.id ? null : clickedRegion.id);
        setSelectedRegion(clickedRegion.id);
      } else {
        // Only clear selection if we're actually clicking on empty space
        // Not if this is triggered by ending a drag operation
        setSelectedRegion(null);
        setClickedRegionId(null);
      }
    } else {
      // If regions are not interactive, always clear selection
      setSelectedRegion(null);
      setClickedRegionId(null);
    }
  }, [currentSession, getRegionAtPoint, setSelectedRegion, isImageDragging, draggedRegionId, justFinishedDragging]);
  
  // Handle double click to fit image
  const handleDoubleClick = useCallback(() => {
    if (currentSession) {
      fitToCanvas(
        currentSession.original_image.dimensions.width,
        currentSession.original_image.dimensions.height,
        actualContainerSize.width,
        actualContainerSize.height
      );
    }
  }, [currentSession, fitToCanvas, actualContainerSize]);

  // Check if point is within a resize handle
  const getResizeHandle = useCallback((point: Point, region: TextRegion): string | null => {
    const screenBbox = {
      x: region.bounding_box.x * scale + offset.x,
      y: region.bounding_box.y * scale + offset.y,
      width: region.bounding_box.width * scale,
      height: region.bounding_box.height * scale,
    };

    const handleSize = 8;
    const tolerance = 4;

    // Check each corner handle
    const handles = [
      { name: 'tl', x: screenBbox.x - handleSize/2, y: screenBbox.y - handleSize/2 },
      { name: 'tr', x: screenBbox.x + screenBbox.width - handleSize/2, y: screenBbox.y - handleSize/2 },
      { name: 'bl', x: screenBbox.x - handleSize/2, y: screenBbox.y + screenBbox.height - handleSize/2 },
      { name: 'br', x: screenBbox.x + screenBbox.width - handleSize/2, y: screenBbox.y + screenBbox.height - handleSize/2 },
    ];

    for (const handle of handles) {
      if (
        point.x >= handle.x - tolerance &&
        point.x <= handle.x + handleSize + tolerance &&
        point.y >= handle.y - tolerance &&
        point.y <= handle.y + handleSize + tolerance
      ) {
        return handle.name;
      }
    }

    return null;
  }, [scale, offset]);

  // Convert screen coordinates to canvas coordinates
  const screenToCanvasPoint = useCallback((screenPoint: Point): Point => {
    return {
      x: (screenPoint.x - offset.x) / scale,
      y: (screenPoint.y - offset.y) / scale,
    };
  }, [scale, offset]);

  // Constrain bounds within image boundaries
  const constrainToImageBounds = useCallback((
    bounds: Rectangle, 
    dragHandle?: string | null,
    originalBounds?: Rectangle
  ): Rectangle => {
    if (!currentSession) return bounds;

    const imageWidth = currentSession.original_image.dimensions.width;
    const imageHeight = currentSession.original_image.dimensions.height;
    
    const constrainedBounds = { ...bounds };

    // For resize operations, we need to handle each direction carefully
    if (dragHandle && dragHandle !== 'move' && originalBounds) {
      const minSize = 10;

      switch (dragHandle) {
        case 'tl': // Top-left: constraining top and left
          // Constrain top edge
          if (constrainedBounds.y < 0) {
            constrainedBounds.height = constrainedBounds.height + constrainedBounds.y;
            constrainedBounds.y = 0;
          }
          // Constrain left edge
          if (constrainedBounds.x < 0) {
            constrainedBounds.width = constrainedBounds.width + constrainedBounds.x;
            constrainedBounds.x = 0;
          }
          // Ensure minimum size
          if (constrainedBounds.width < minSize) {
            constrainedBounds.x = constrainedBounds.x + constrainedBounds.width - minSize;
            constrainedBounds.width = minSize;
          }
          if (constrainedBounds.height < minSize) {
            constrainedBounds.y = constrainedBounds.y + constrainedBounds.height - minSize;
            constrainedBounds.height = minSize;
          }
          break;

        case 'tr': // Top-right: constraining top and right
          // Constrain top edge
          if (constrainedBounds.y < 0) {
            constrainedBounds.height = constrainedBounds.height + constrainedBounds.y;
            constrainedBounds.y = 0;
          }
          // Constrain right edge
          if (constrainedBounds.x + constrainedBounds.width > imageWidth) {
            constrainedBounds.width = imageWidth - constrainedBounds.x;
          }
          // Ensure minimum size
          if (constrainedBounds.width < minSize) {
            constrainedBounds.width = minSize;
          }
          if (constrainedBounds.height < minSize) {
            constrainedBounds.y = constrainedBounds.y + constrainedBounds.height - minSize;
            constrainedBounds.height = minSize;
          }
          break;

        case 'bl': // Bottom-left: constraining bottom and left
          // Constrain left edge
          if (constrainedBounds.x < 0) {
            constrainedBounds.width = constrainedBounds.width + constrainedBounds.x;
            constrainedBounds.x = 0;
          }
          // Constrain bottom edge
          if (constrainedBounds.y + constrainedBounds.height > imageHeight) {
            constrainedBounds.height = imageHeight - constrainedBounds.y;
          }
          // Ensure minimum size
          if (constrainedBounds.width < minSize) {
            constrainedBounds.x = constrainedBounds.x + constrainedBounds.width - minSize;
            constrainedBounds.width = minSize;
          }
          if (constrainedBounds.height < minSize) {
            constrainedBounds.height = minSize;
          }
          break;

        case 'br': // Bottom-right: constraining bottom and right
          // Constrain right edge
          if (constrainedBounds.x + constrainedBounds.width > imageWidth) {
            constrainedBounds.width = imageWidth - constrainedBounds.x;
          }
          // Constrain bottom edge
          if (constrainedBounds.y + constrainedBounds.height > imageHeight) {
            constrainedBounds.height = imageHeight - constrainedBounds.y;
          }
          // Ensure minimum size
          if (constrainedBounds.width < minSize) {
            constrainedBounds.width = minSize;
          }
          if (constrainedBounds.height < minSize) {
            constrainedBounds.height = minSize;
          }
          break;
      }
    } else {
      // For move operations, constrain normally
      constrainedBounds.x = Math.max(0, Math.min(constrainedBounds.x, imageWidth - constrainedBounds.width));
      constrainedBounds.y = Math.max(0, Math.min(constrainedBounds.y, imageHeight - constrainedBounds.height));
      constrainedBounds.width = Math.max(10, Math.min(constrainedBounds.width, imageWidth - constrainedBounds.x));
      constrainedBounds.height = Math.max(10, Math.min(constrainedBounds.height, imageHeight - constrainedBounds.y));
    }

    return constrainedBounds;
  }, [currentSession]);

  // Get cursor style based on current interaction
  const getCursorStyle = useCallback((pos?: Point): string => {
    // If we're actively dragging a region
    if (draggedRegionId && draggedHandle) {
      switch (draggedHandle) {
        case 'tl': return 'nw-resize';
        case 'tr': return 'ne-resize';
        case 'bl': return 'sw-resize';
        case 'br': return 'se-resize';
        case 'move': return 'grabbing';
        default: return 'default';
      }
    }

    // If we're dragging the image
    if (isImageDragging) {
      return 'grabbing';
    }

    // Determine if regions should be interactive
    const shouldRegionsBeInteractive = (() => {
      if (processingState.displayMode === 'original' || !!currentTaskId) {
        return true;
      }
      if (processingState.displayMode === 'processed') {
        return processingState.showRegionOverlay;
      }
      return false;
    })();

    // Check for hover states (only if regions should be interactive)
    if (pos && currentSession && shouldRegionsBeInteractive) {
      const selectedRegion = currentDisplayRegions.find(r => r.id === canvasState.selectedRegionId);
      if (selectedRegion) {
        const handle = getResizeHandle(pos, selectedRegion);
        if (handle) {
          switch (handle) {
            case 'tl': return 'nw-resize';
            case 'tr': return 'ne-resize';
            case 'bl': return 'sw-resize';
            case 'br': return 'se-resize';
            default: return 'default';
          }
        }

        // Check if hovering over selected region for move
        const screenBbox = {
          x: selectedRegion.bounding_box.x * scale + offset.x,
          y: selectedRegion.bounding_box.y * scale + offset.y,
          width: selectedRegion.bounding_box.width * scale,
          height: selectedRegion.bounding_box.height * scale,
        };
        
        if (
          pos.x >= screenBbox.x && pos.x <= screenBbox.x + screenBbox.width &&
          pos.y >= screenBbox.y && pos.y <= screenBbox.y + screenBbox.height
        ) {
          return 'grab';
        }
      }

      // Check for hovering over any region
      const hoveredRegion = getRegionAtPoint(pos, currentDisplayRegions);
      if (hoveredRegion) {
        return 'pointer';
      }
    }

    return 'default';
  }, [draggedRegionId, draggedHandle, isImageDragging, currentSession, canvasState.selectedRegionId, getResizeHandle, scale, offset, getRegionAtPoint, processingState]);

  // Handle mouse down for potential dragging
  const handleMouseDown = useCallback((e: any) => {
    const pos = e.target.getStage().getPointerPosition();
    if (!pos || !currentSession) return;

    // Determine if regions should be interactive
    const shouldRegionsBeInteractive = (() => {
      if (processingState.displayMode === 'original' || !!currentTaskId) {
        return true;
      }
      if (processingState.displayMode === 'processed') {
        return processingState.showRegionOverlay;
      }
      return false;
    })();

    // PRIORITY 1: Check if clicking on resize handles of the currently selected region
    // This has the highest priority to ensure proper layer handling
    if (canvasState.selectedRegionId && shouldRegionsBeInteractive) {
      const selectedRegion = currentDisplayRegions.find(r => r.id === canvasState.selectedRegionId);
      if (selectedRegion) {
        const handle = getResizeHandle(pos, selectedRegion);
        if (handle) {
          // Start resize operation - highest priority
          setIsUserInteracting(true);
          setDraggedRegionId(selectedRegion.id);
          setDraggedHandle(handle);
          setInitialRegionBounds(selectedRegion.bounding_box);
          setRegionDragStart(pos);
          return;
        }

        // Check if clicking within the selected region bounds for move operation
        const screenBbox = {
          x: selectedRegion.bounding_box.x * scale + offset.x,
          y: selectedRegion.bounding_box.y * scale + offset.y,
          width: selectedRegion.bounding_box.width * scale,
          height: selectedRegion.bounding_box.height * scale,
        };
        
        if (
          pos.x >= screenBbox.x && pos.x <= screenBbox.x + screenBbox.width &&
          pos.y >= screenBbox.y && pos.y <= screenBbox.y + screenBbox.height
        ) {
          // Start move operation for selected region
          setIsUserInteracting(true);
          setDraggedRegionId(selectedRegion.id);
          setDraggedHandle('move');
          setInitialRegionBounds(selectedRegion.bounding_box);
          setRegionDragStart(pos);
          return;
        }
      }
    }

    // PRIORITY 2: Check if clicked on other regions (for selection/interaction)
    // But only if regions should be interactive

    if (shouldRegionsBeInteractive) {
      const clickedRegion = getRegionAtPoint(pos, currentDisplayRegions);
      if (clickedRegion) {
        // If clicking on a different region, check for move operation
        const screenBbox = {
          x: clickedRegion.bounding_box.x * scale + offset.x,
          y: clickedRegion.bounding_box.y * scale + offset.y,
          width: clickedRegion.bounding_box.width * scale,
          height: clickedRegion.bounding_box.height * scale,
        };
        
        if (
          pos.x >= screenBbox.x && pos.x <= screenBbox.x + screenBbox.width &&
          pos.y >= screenBbox.y && pos.y <= screenBbox.y + screenBbox.height
        ) {
          // Start move operation for other region
          setIsUserInteracting(true);
          setDraggedRegionId(clickedRegion.id);
          setDraggedHandle('move');
          setInitialRegionBounds(clickedRegion.bounding_box);
          setRegionDragStart(pos);
          return;
        }
        
        // Just selecting the region
        setSelectedRegion(clickedRegion.id);
        setClickedRegionId(clickedRegion.id);
        setDragStart(pos);
        setIsDragging(false);
        return;
      }
    }
    
    // PRIORITY 3: Clicking on empty space or image - start image dragging
    setIsUserInteracting(true);
    setImageDragStart(pos);
    setLastOffset(offset);
    setIsImageDragging(false);
  }, [currentSession, getRegionAtPoint, offset, canvasState.selectedRegionId, getResizeHandle, scale, setSelectedRegion, setClickedRegionId, processingState]);

  // Handle mouse move for dragging and hover
  const handleMouseMove = useCallback((e: any) => {
    const pos = e.target.getStage().getPointerPosition();
    if (!pos || !currentSession) return;

    // Handle region manipulation (resize or move)
    if (regionDragStart && draggedRegionId && draggedHandle && initialRegionBounds) {
      const deltaX = (pos.x - regionDragStart.x) / scale;
      const deltaY = (pos.y - regionDragStart.y) / scale;
      
      let newBounds = { ...initialRegionBounds };

      if (draggedHandle === 'move') {
        // Move the entire region
        newBounds.x = initialRegionBounds.x + deltaX;
        newBounds.y = initialRegionBounds.y + deltaY;
      } else {
        // Resize based on which handle is being dragged
        switch (draggedHandle) {
          case 'tl': // Top-left
            newBounds.x = initialRegionBounds.x + deltaX;
            newBounds.y = initialRegionBounds.y + deltaY;
            newBounds.width = initialRegionBounds.width - deltaX;
            newBounds.height = initialRegionBounds.height - deltaY;
            break;
          case 'tr': // Top-right
            newBounds.y = initialRegionBounds.y + deltaY;
            newBounds.width = initialRegionBounds.width + deltaX;
            newBounds.height = initialRegionBounds.height - deltaY;
            break;
          case 'bl': // Bottom-left
            newBounds.x = initialRegionBounds.x + deltaX;
            newBounds.width = initialRegionBounds.width - deltaX;
            newBounds.height = initialRegionBounds.height + deltaY;
            break;
          case 'br': // Bottom-right
            newBounds.width = initialRegionBounds.width + deltaX;
            newBounds.height = initialRegionBounds.height + deltaY;
            break;
        }

        // Ensure minimum size
        const minSize = 10;
        if (newBounds.width < minSize) {
          if (draggedHandle.includes('l')) {
            newBounds.x = newBounds.x + newBounds.width - minSize;
          }
          newBounds.width = minSize;
        }
        if (newBounds.height < minSize) {
          if (draggedHandle.includes('t')) {
            newBounds.y = newBounds.y + newBounds.height - minSize;
          }
          newBounds.height = minSize;
        }
      }

      // Apply boundary constraints
      const constrainedBounds = constrainToImageBounds(newBounds, draggedHandle, initialRegionBounds);

      // Update the region bounds in the store
      updateTextRegion(draggedRegionId, { bounding_box: constrainedBounds });
      return;
    }

    // Handle image dragging
    if (imageDragStart) {
      const distance = Math.sqrt(
        Math.pow(pos.x - imageDragStart.x, 2) + Math.pow(pos.y - imageDragStart.y, 2)
      );

      if (distance > 5) {
        setIsImageDragging(true);
        
        // Calculate new offset based on mouse movement
        const deltaX = pos.x - imageDragStart.x;
        const deltaY = pos.y - imageDragStart.y;
        
        const { setCanvasOffset } = useAppStore.getState();
        setCanvasOffset({
          x: lastOffset.x + deltaX,
          y: lastOffset.y + deltaY,
        });
      }
      return;
    }

    // Handle region dragging (legacy)
    if (dragStart) {
      const distance = Math.sqrt(
        Math.pow(pos.x - dragStart.x, 2) + Math.pow(pos.y - dragStart.y, 2)
      );

      if (distance > 5 && !isDragging) {
        setIsDragging(true);
      }
    }

    // Handle hover for text display (only if not dragging and regions should be interactive)
    if (!isDragging && !isImageDragging && !draggedRegionId) {
      const shouldRegionsBeInteractive = (() => {
        if (processingState.displayMode === 'original' || !!currentTaskId) {
          return true;
        }
        if (processingState.displayMode === 'processed') {
          return processingState.showRegionOverlay;
        }
        return false;
      })();

      if (shouldRegionsBeInteractive) {
        const hoveredRegion = getRegionAtPoint(pos, currentDisplayRegions);
        setHoveredRegionId(hoveredRegion?.id || null);
      } else {
        setHoveredRegionId(null);
      }
    }

    // Update cursor based on current position and state
    const newCursor = getCursorStyle(pos);
    if (newCursor !== currentCursor) {
      setCurrentCursor(newCursor);
    }
  }, [
    dragStart, isDragging, isImageDragging, imageDragStart, lastOffset, currentSession, getRegionAtPoint,
    regionDragStart, draggedRegionId, draggedHandle, initialRegionBounds, scale, updateTextRegion,
    constrainToImageBounds, getCursorStyle, currentCursor
  ]);

  // Handle mouse up
  const handleMouseUp = useCallback((e?: any) => {
    // Prevent event bubbling to avoid multiple calls (Konva events)
    if (e && e.evt && e.evt.stopPropagation) {
      e.evt.stopPropagation();
    } else if (e && e.stopPropagation) {
      e.stopPropagation();
    }
    
    
    // Remember the currently selected region before clearing drag states
    const wasDraggingRegion = draggedRegionId;
    const wasDraggingImage = isImageDragging;
    const wasDraggedHandle = draggedHandle;
    const wasInitialBounds = initialRegionBounds;
    
    // If we were dragging a region, create undo command
    if (wasDraggingRegion && wasDraggedHandle && wasInitialBounds && currentSession) {
      const currentRegion = currentDisplayRegions.find(r => r.id === wasDraggingRegion);
      if (currentRegion) {
        const newBounds = currentRegion.bounding_box;
        
        // Only create undo command if bounds actually changed
        if (wasInitialBounds.x !== newBounds.x || 
            wasInitialBounds.y !== newBounds.y ||
            wasInitialBounds.width !== newBounds.width ||
            wasInitialBounds.height !== newBounds.height) {
          
          
          if (wasDraggedHandle === 'move') {
            moveRegionWithUndo(wasDraggingRegion, wasInitialBounds, newBounds);
          } else {
            resizeRegionWithUndo(wasDraggingRegion, wasInitialBounds, newBounds);
          }
        }
      }
    }
    
    setDragStart(null);
    setIsDragging(false);
    setImageDragStart(null);
    setIsImageDragging(false);
    
    // Clear region manipulation states
    setDraggedRegionId(null);
    setDraggedHandle(null);
    setInitialRegionBounds(null);
    setRegionDragStart(null);
    
    // Reset user interaction state
    setIsUserInteracting(false);
    
    // If we were dragging something, mark it to prevent unwanted clicks
    if (wasDraggingRegion || wasDraggingImage) {
      setJustFinishedDragging(true);
      // Clear this flag after a short delay and reset processed flag
      setTimeout(() => {
        setJustFinishedDragging(false);
      }, 50);
    }
    
    // If we were dragging a region, keep it selected
    // Don't clear the selection just because we stopped dragging
    if (wasDraggingRegion && canvasState.selectedRegionId !== wasDraggingRegion) {
      setSelectedRegion(wasDraggingRegion);
    }
    
    // Reset cursor to default after drag operations
    setCurrentCursor('default');
  }, [
    draggedRegionId, 
    isImageDragging, 
    draggedHandle, 
    initialRegionBounds, 
    currentSession,
    currentDisplayRegions,
    moveRegionWithUndo,
    resizeRegionWithUndo,
    canvasState.selectedRegionId, 
    setSelectedRegion
  ]);

  // Container-level mouse event handlers for when mouse leaves stage area
  const handleContainerMouseMove = useCallback((e: React.MouseEvent) => {
    if ((draggedRegionId || isImageDragging) && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const pos = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
      
      // Create a synthetic Konva-like event
      const syntheticEvent = {
        target: {
          getStage: () => ({
            getPointerPosition: () => pos
          })
        }
      };
      
      handleMouseMove(syntheticEvent);
    }
  }, [draggedRegionId, isImageDragging, handleMouseMove]);

  const handleContainerMouseUp = useCallback(() => {
    if (draggedRegionId || isImageDragging) {
      handleMouseUp();
    }
  }, [draggedRegionId, isImageDragging, handleMouseUp]);

  const handleContainerMouseLeave = useCallback(() => {
    // Don't clear selection when mouse leaves, just stop any active dragging
    if (draggedRegionId || isImageDragging) {
      handleMouseUp();
    }
  }, [draggedRegionId, isImageDragging, handleMouseUp]);

  // Render text region
  const renderTextRegion = (region: TextRegion, index: number) => {
    const isSelected = canvasState.selectedRegionId === region.id;
    const isHovered = hoveredRegionId === region.id;
    const isClicked = clickedRegionId === region.id;
    const shouldShowText = isHovered || isClicked;
    const isTextModified = region.edited_text && region.edited_text !== region.original_text;
    
    // Determine if regions should be interactive based on display mode and overlay settings
    const shouldBeInteractive = (() => {
      // Always interactive in original mode or when processing
      if (processingState.displayMode === 'original' || !!currentTaskId) {
        return true;
      }
      // In processed mode, only interactive if overlay is enabled
      if (processingState.displayMode === 'processed') {
        return processingState.showRegionOverlay;
      }
      return false;
    })();

    // Validate region data to prevent rendering issues
    const bbox = region.bounding_box;
    if (!bbox || 
        typeof bbox.x !== 'number' || 
        typeof bbox.y !== 'number' || 
        typeof bbox.width !== 'number' || 
        typeof bbox.height !== 'number' ||
        isNaN(bbox.x) || isNaN(bbox.y) || isNaN(bbox.width) || isNaN(bbox.height) ||
        bbox.width <= 0 || bbox.height <= 0) {
      console.warn(`Invalid region data for region ${region.id}:`, bbox);
      return null;
    }

    const screenBbox = {
      x: bbox.x * scale + offset.x,
      y: bbox.y * scale + offset.y,
      width: bbox.width * scale,
      height: bbox.height * scale,
    };

    // Additional validation for screen coordinates
    if (isNaN(screenBbox.x) || isNaN(screenBbox.y) || 
        isNaN(screenBbox.width) || isNaN(screenBbox.height) ||
        screenBbox.width <= 0 || screenBbox.height <= 0) {
      console.warn(`Invalid screen coordinates for region ${region.id}:`, screenBbox, 'scale:', scale, 'offset:', offset);
      return null;
    }

    // Check if region is extremely far outside the visible area (likely a data issue)
    const canvasWidth = actualContainerSize.width || 800;
    const canvasHeight = actualContainerSize.height || 600;
    const buffer = Math.max(canvasWidth, canvasHeight) * 5; // Allow 5x canvas size buffer
    
    if (screenBbox.x < -buffer || screenBbox.y < -buffer || 
        screenBbox.x > canvasWidth + buffer || screenBbox.y > canvasHeight + buffer) {
      console.warn(`Region ${region.id} is far outside visible area:`, {
        screenBbox,
        canvasSize: { width: canvasWidth, height: canvasHeight },
        originalBbox: bbox
      });
      // Don't return null here - just warn, as the region might be valid but off-screen
    }

    // Choose colors based on state and text classification with enhanced contrast
    let fillColor, strokeColor, strokeWidth;
    if (isSelected) {
      fillColor = 'rgba(59, 130, 246, 0.25)';
      strokeColor = '#3b82f6';
      strokeWidth = 3; // Thicker border for selected
    } else if (region.category_config && region.category_config.color) {
      // Use text classification color with standard visibility
      const categoryColor = region.category_config.color;
      const bgColor = region.category_config.bgColor;
      fillColor = bgColor || `${categoryColor}25`; // Slightly more opaque for better visibility
      strokeColor = categoryColor;
      strokeWidth = 2; // Standard border for all classified regions
    } else if (isTextModified) {
      fillColor = 'rgba(249, 115, 22, 0.2)';
      strokeColor = '#f97316';
      strokeWidth = 2;
    } else {
      fillColor = 'rgba(239, 68, 68, 0.2)';
      strokeColor = '#ef4444';
      strokeWidth = 1; // Thinner border for unclassified
    }

    return (
      <React.Fragment key={region.id}>
        {/* Main region rectangle with enhanced styling */}
        <Rect
          x={screenBbox.x}
          y={screenBbox.y}
          width={screenBbox.width}
          height={screenBbox.height}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          dash={isSelected ? [] : isTextModified ? [4, 2] : (region.category_config && region.text_category !== 'other') ? [] : [5, 5]}
          listening={shouldBeInteractive}
          onClick={shouldBeInteractive ? handleCanvasClick : undefined}
          onMouseDown={shouldBeInteractive ? handleMouseDown : undefined}
          onMouseMove={shouldBeInteractive ? handleMouseMove : undefined}
        />

        {/* Region label - only show on hover or click */}
        {shouldShowText && (region.edited_text || region.original_text) && (
          <>
            {(() => {
              const text = region.edited_text || region.original_text || 'No text detected';
              const fontSize = 12;
              const padding = 8;
              
              // Measure actual text width more accurately
              let actualTextWidth;
              try {
                // Try to use canvas to measure text width accurately
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                if (ctx) {
                  ctx.font = `${fontSize}px Arial`;
                  actualTextWidth = ctx.measureText(text).width;
                } else {
                  actualTextWidth = text.length * fontSize * 0.6;
                }
              } catch (e) {
                // Fallback to estimation if canvas fails
                actualTextWidth = text.length * fontSize * 0.6;
              }
              
              // Background width based on actual text measurement
              const bgWidth = actualTextWidth + padding * 2;
              const bgHeight = 22;
              
              // Position tooltip above the region, centered
              let tooltipX = screenBbox.x + screenBbox.width / 2 - bgWidth / 2;
              let tooltipY = screenBbox.y - bgHeight - 6;
              
              // Keep within canvas bounds
              const canvasWidth = stageRef.current?.width() || 800;
              if (tooltipX < 5) tooltipX = 5;
              if (tooltipX + bgWidth > canvasWidth - 5) tooltipX = canvasWidth - bgWidth - 5;
              if (tooltipY < 5) tooltipY = screenBbox.y + screenBbox.height + 6;
              
              return (
                <>
                  {/* Background */}
                  <Rect
                    x={tooltipX}
                    y={tooltipY}
                    width={bgWidth}
                    height={bgHeight}
                    fill="rgba(50, 50, 50, 0.9)"
                    cornerRadius={4}
                    shadowColor="rgba(0, 0, 0, 0.25)"
                    shadowBlur={2}
                    shadowOffset={{ x: 0, y: 1 }}
                  />
                  
                  {/* Text - perfectly centered */}
                  <Text
                    x={tooltipX + bgWidth / 2}
                    y={tooltipY + bgHeight / 2}
                    text={text}
                    fontSize={fontSize}
                    fill="white"
                    fontFamily="Arial"
                    offsetX={actualTextWidth / 2}
                    offsetY={fontSize / 2}
                  />
                </>
              );
            })()}
          </>
        )}

        {/* Region index - always show */}
        <Text
          x={screenBbox.x}
          y={screenBbox.y - 8}
          text={`${index + 1}`}
          fontSize={10}
          fill={isSelected ? '#3b82f6' : '#ef4444'}
          fontFamily="Inter, sans-serif"
          fontStyle="bold"
        />


        {/* Resize handles for selected region */}
        {isSelected && (
          <>
            {/* Top-left handle */}
            <Rect
              x={screenBbox.x - 4}
              y={screenBbox.y - 4}
              width={8}
              height={8}
              fill="#3b82f6"
              stroke="#ffffff"
              strokeWidth={1}
              listening={shouldBeInteractive}
              onMouseDown={shouldBeInteractive ? handleMouseDown : undefined}
              onMouseMove={shouldBeInteractive ? handleMouseMove : undefined}
            />
            {/* Top-right handle */}
            <Rect
              x={screenBbox.x + screenBbox.width - 4}
              y={screenBbox.y - 4}
              width={8}
              height={8}
              fill="#3b82f6"
              stroke="#ffffff"
              strokeWidth={1}
              listening={shouldBeInteractive}
              onMouseDown={shouldBeInteractive ? handleMouseDown : undefined}
              onMouseMove={shouldBeInteractive ? handleMouseMove : undefined}
            />
            {/* Bottom-left handle */}
            <Rect
              x={screenBbox.x - 4}
              y={screenBbox.y + screenBbox.height - 4}
              width={8}
              height={8}
              fill="#3b82f6"
              stroke="#ffffff"
              strokeWidth={1}
              listening={shouldBeInteractive}
              onMouseDown={shouldBeInteractive ? handleMouseDown : undefined}
              onMouseMove={shouldBeInteractive ? handleMouseMove : undefined}
            />
            {/* Bottom-right handle */}
            <Rect
              x={screenBbox.x + screenBbox.width - 4}
              y={screenBbox.y + screenBbox.height - 4}
              width={8}
              height={8}
              fill="#3b82f6"
              stroke="#ffffff"
              strokeWidth={1}
              listening={shouldBeInteractive}
              onMouseDown={shouldBeInteractive ? handleMouseDown : undefined}
              onMouseMove={shouldBeInteractive ? handleMouseMove : undefined}
            />
          </>
        )}
      </React.Fragment>
    );
  };

  if (!currentSession) {
    return (
      <Card className={clsx('flex items-center justify-center h-96', className)}>
        <div className="text-center text-muted-foreground">
          <p>No image loaded</p>
        </div>
      </Card>
    );
  }

  if (!image) {
    return (
      <Card className={clsx('flex items-center justify-center h-96', className)}>
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-muted-foreground">Loading image...</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={clsx('overflow-hidden relative', className)}>
      <div
        ref={canvasRef}
        className="w-full relative bg-slate-50 dark:bg-slate-900"
        style={{ 
          width: '100%', // Fill the grid column (3/4 width)
          height: containerDimensions.height,
          maxWidth: '100%', // Don't exceed the grid column
          maxHeight: '80vh', // Reasonable max height
          minHeight: '400px', // Minimum usable height
          cursor: currentCursor,
        }}
        onMouseMove={handleContainerMouseMove}
        onMouseLeave={handleContainerMouseLeave}
      >
        <Stage
          ref={stageRef}
          width={actualContainerSize.width}
          height={actualContainerSize.height}
          onClick={handleCanvasClick}
          onDblClick={handleDoubleClick}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          draggable={false}
        >
          {/* Grid layer - rendered behind everything */}
          <Layer listening={false}>
            {renderGrid}
          </Layer>

          {/* Main content layer */}
          <Layer>
            {/* Main image */}
            <KonvaImage
              image={image}
              x={offset.x}
              y={offset.y}
              scaleX={scale}
              scaleY={scale}
              listening={false}
            />

            {/* Text regions - show based on display mode and overlay settings */}
            {(() => {
              // Always show in original mode or when processing
              if (processingState.displayMode === 'original' || !!currentTaskId) {
                return true;
              }
              // In processed mode, only show if overlay is enabled
              if (processingState.displayMode === 'processed') {
                return processingState.showRegionOverlay;
              }
              return false;
            })() && 
              currentDisplayRegions.map((region, index) => {
                const renderedRegion = renderTextRegion(region, index);
                
                // Only log rendering failures in development
                if (process.env.NODE_ENV === 'development' && 
                    region.bounding_box && 
                    region.bounding_box.width > 0 && 
                    region.bounding_box.height > 0 && 
                    renderedRegion === null) {
                  console.warn(`Failed to render region ${region.id}:`, {
                    bbox: region.bounding_box,
                    scale,
                    offset
                  });
                }
                
                return renderedRegion;
              })}
              
            {/* Text preview layer - only show in processed mode when user has input text and regions are visible */}
            {processingState.displayMode === 'processed' && 
              processingState.showRegionOverlay &&
              currentDisplayRegions
                .filter(region => region.user_input_text && region.user_input_text.trim().length > 0)
                .map((region) => {
                  const bbox = region.bounding_box;
                  
                  // Validate region data
                  if (!bbox || bbox.width <= 0 || bbox.height <= 0) {
                    return null;
                  }
                  
                  const screenBbox = {
                    x: bbox.x * scale + offset.x,
                    y: bbox.y * scale + offset.y,
                    width: bbox.width * scale,
                    height: bbox.height * scale,
                  };
                  
                  // Calculate font size for preview (matches backend logic exactly)
                  // calculatePreviewFontSize returns actual pixel font size, need to scale for display
                  const actualFontSize = calculatePreviewFontSize(region, region.user_input_text);
                  const previewFontSize = actualFontSize * scale;
                  
                  // Get font properties, passing text for intelligent font selection
                  const fontFamily = getFontFamily(region, region.user_input_text);
                  const fontColor = getFontColor(region);
                  const fontWeight = getFontWeight(region);
                  const fontStyle = getFontStyle(region);
                  
                  return (
                    <Text
                      key={`preview-${region.id}`}
                      x={screenBbox.x}
                      y={screenBbox.y}
                      width={screenBbox.width}
                      height={screenBbox.height}
                      text={region.user_input_text}
                      fontSize={Math.max(4 * scale, previewFontSize)} // Ensure minimum readable size (match backend min)
                      fontFamily={fontFamily}
                      fontStyle={fontStyle}
                      fontWeight={fontWeight}
                      fill={fontColor}
                      align="center"
                      verticalAlign="middle"
                      wrap="word"
                      ellipsis={true}
                      listening={false} // Don't interfere with region interactions
                      opacity={0.8} // Slightly transparent to indicate it's a preview
                    />
                  );
                })}
            
          </Layer>
        </Stage>

        {/* Overlay info - positioned within container bounds */}
        <div className="absolute bg-black/80 text-white px-2 py-1 rounded text-xs z-10"
             style={{
               top: '4px',
               left: '4px',
               fontSize: '11px'
             }}>
          <div>Zoom: {Math.round(scale * 100)}%</div>
          <div>Regions: {currentDisplayRegions.length}</div>
          {canvasState.selectedRegionId && (
            <div className="text-blue-300">
              Selected: Region {
                currentDisplayRegions.findIndex(r => r.id === canvasState.selectedRegionId) + 1
              }
            </div>
          )}
        </div>

        {/* Text Classification Legend - positioned within container bounds */}
        <div 
          className="absolute"
          style={{
            bottom: '4px',
            right: '4px',
          }}
        >
          <TextClassificationLegend />
        </div>

        {/* Laser Scan Animation - overlay when processing */}
        <LaserScanAnimation
          isActive={progressData.isActive}
          progress={progressData.progress}
          stage={progressData.stage}
          message={progressData.message}
        />
      </div>
    </Card>
  );
};