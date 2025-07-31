import { UndoableCommand, TextRegion, Rectangle, ImageDisplayMode } from '@/types';
import { v4 as uuidv4 } from 'uuid';

/**
 * Create an undoable command for moving a text region
 */
export const createMoveRegionCommand = (
  regionId: string,
  oldPosition: Rectangle,
  newPosition: Rectangle,
  displayMode: ImageDisplayMode,
  updateFunction: (regionId: string, updates: Partial<TextRegion>) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'move_region',
  displayMode,
  timestamp: Date.now(),
  description: `Move region ${regionId}`,
  execute: () => {
    // Move operation already completed during drag, no need to execute again
  },
  undo: () => {
    updateFunction(regionId, { 
      bounding_box: oldPosition,
      is_user_modified: true 
    });
  }
});

/**
 * Create an undoable command for resizing a text region
 */
export const createResizeRegionCommand = (
  regionId: string,
  oldBounds: Rectangle,
  newBounds: Rectangle,
  displayMode: ImageDisplayMode,
  updateFunction: (regionId: string, updates: Partial<TextRegion>) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'resize_region',
  displayMode,
  timestamp: Date.now(),
  description: `Resize region ${regionId}`,
  execute: () => {
    // Resize operation already completed during drag, no need to execute again
  },
  undo: () => {
    updateFunction(regionId, { 
      bounding_box: oldBounds,
      is_user_modified: true 
    });
  }
});

/**
 * Create an undoable command for adding a text region
 */
export const createAddRegionCommand = (
  region: TextRegion,
  displayMode: ImageDisplayMode,
  addFunction: (region: Omit<TextRegion, 'id'>) => void,
  removeFunction: (regionId: string) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'add_region',
  displayMode,
  timestamp: Date.now(),
  description: `Add region ${region.id}`,
  execute: () => {
    // Region already added, this is just for history tracking
  },
  undo: () => {
    removeFunction(region.id);
  }
});

/**
 * Create an undoable command for deleting a text region
 */
export const createDeleteRegionCommand = (
  region: TextRegion,
  displayMode: ImageDisplayMode,
  addFunction: (region: Omit<TextRegion, 'id'>) => void,
  removeFunction: (regionId: string) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'delete_region',
  displayMode,
  timestamp: Date.now(),
  description: `Delete region ${region.id}`,
  execute: () => {
    removeFunction(region.id);
  },
  undo: () => {
    addFunction(region);
  }
});

/**
 * Create an undoable command for editing text in a region
 */
export const createEditTextCommand = (
  regionId: string,
  oldText: string,
  newText: string,
  textField: 'edited_text' | 'user_input_text',
  displayMode: ImageDisplayMode,
  updateFunction: (regionId: string, updates: Partial<TextRegion>) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'edit_text',
  displayMode,
  timestamp: Date.now(),
  description: `Edit text in region ${regionId}`,
  execute: () => {
    updateFunction(regionId, { 
      [textField]: newText,
      is_user_modified: true 
    });
  },
  undo: () => {
    updateFunction(regionId, { 
      [textField]: oldText,
      is_user_modified: oldText !== ''
    });
  }
});

/**
 * Create an undoable command for text generation
 */
export const createGenerateTextCommand = (
  sessionId: string,
  oldProcessedImage: any | null,
  newProcessedImage: any | null,
  oldProcessedRegions: TextRegion[],
  newProcessedRegions: TextRegion[],
  displayMode: ImageDisplayMode,
  restoreSessionFunction: (sessionData: any) => void
): UndoableCommand => ({
  id: uuidv4(),
  type: 'generate_text',
  displayMode,
  timestamp: Date.now(),
  description: 'Generate text in regions',
  execute: () => {
    // Text generation already executed, this is just for history tracking
  },
  undo: () => {
    restoreSessionFunction({
      processed_image: oldProcessedImage,
      processed_text_regions: oldProcessedRegions,
      keepProcessedMode: true, // Signal to maintain processed mode
      showRegionOverlay: true // Always show regions after undoing Generate Text
    });
  }
});

