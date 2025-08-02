import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { 
  AppState, 
  LabelSession, 
  TextRegion, 
  Point, 
  Rectangle,
  CanvasState,
  CanvasTool,
  ProcessingProgress,
  ProcessingStage,
  ImageDisplayMode,
  UndoableCommand,
  UndoState
} from '@/types';
import { apiService } from '@/services/api';
import { createAddRegionCommand, createDeleteRegionCommand, createEditTextCommand, createGenerateTextCommand, createMoveRegionCommand, createResizeRegionCommand } from '@/utils/undoCommands';
import { recordOriginalBoxSize, markRegionSizeModified } from '@/utils/fontUtils';

interface AppStore extends AppState {
  // Helper functions
  getCurrentDisplayRegions: () => TextRegion[];
  
  // Actions
  setCurrentSession: (session: LabelSession | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // File upload trigger
  shouldAutoTriggerUpload: boolean;
  setShouldAutoTriggerUpload: (should: boolean) => void;
  
  // Canvas actions
  setCanvasScale: (scale: number) => void;
  setCanvasOffset: (offset: Point) => void;
  setSelectedRegion: (regionId: string | null) => void;
  setCanvasDragging: (isDragging: boolean) => void;
  setSelectionMode: (isSelecting: boolean, start?: Point, end?: Point) => void;
  setActiveTool: (tool: CanvasTool) => void;
  resetCanvasState: () => void;
  
  // Processing actions
  setImageDisplayMode: (mode: ImageDisplayMode) => void;
  setShowRegionOverlay: (show: boolean) => void;
  
  // Settings actions
  setDarkMode: (darkMode: boolean) => void;
  setShowConfidence: (show: boolean) => void;
  setAutoDetectText: (auto: boolean) => void;
  
  // Session actions
  createSession: (file: File, onProgress?: (progress: number) => void) => Promise<LabelSession>;
  updateTextRegions: (regions: TextRegion[], mode?: string, exportCsv?: boolean, manageLoadingState?: boolean) => Promise<void>;
  processTextRemovalAsync: () => Promise<string>; // Returns task ID
  downloadResult: () => Promise<void>;
  downloadRegionsCSV: () => Promise<void>;
  deleteSession: () => Promise<void>;
  generateTextInRegions: () => Promise<void>;
  
  // Async processing state
  currentTaskId: string | null;
  setCurrentTaskId: (taskId: string | null) => void;
  
  // Region actions
  addTextRegion: (region: Omit<TextRegion, 'id'>) => void;
  addTextRegionInternal: (region: TextRegion) => void; // Internal method without undo tracking
  removeTextRegionInternal: (regionId: string) => void; // Internal method without undo tracking
  updateTextRegion: (regionId: string, updates: Partial<TextRegion>) => void;
  updateTextRegionWithUndo: (regionId: string, updates: Partial<TextRegion>) => void;
  moveRegionWithUndo: (regionId: string, oldBounds: Rectangle, newBounds: Rectangle) => void;
  resizeRegionWithUndo: (regionId: string, oldBounds: Rectangle, newBounds: Rectangle) => void;
  removeTextRegion: (regionId: string) => void;
  
  // Undo system actions
  undoLastCommand: () => void;
  canUndo: () => boolean;
  clearUndoHistory: () => void;
  clearOcrHistory: () => void;
  clearProcessedHistory: () => void;
  
  // Utility actions
  reset: () => void;
}

const initialCanvasState: CanvasState = {
  scale: 1,
  offset: { x: 0, y: 0 },
  isDragging: false,
  selectedRegionId: null,
  isSelecting: false,
  selectionStart: null,
  selectionEnd: null,
  activeTool: 'select',
};

const initialUndoState: UndoState = {
  ocrHistory: [],
  processedHistory: [],
  ocrCurrentIndex: -1,
  processedCurrentIndex: -1,
  maxHistorySize: 50,
};

const initialState: AppState = {
  currentSession: null,
  isLoading: false,
  error: null,
  canvasState: initialCanvasState,
  processingState: {
    displayMode: 'original',
    showRegionOverlay: false,
  },
  settings: {
    darkMode: false,
    showConfidence: true,
    autoDetectText: true,
  },
  undoState: initialUndoState,
};

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        shouldAutoTriggerUpload: false,
        currentTaskId: null,

        // Helper functions
        getCurrentDisplayRegions: () => {
          const state = get();
          if (!state.currentSession) return [];
          
          const isProcessedMode = state.processingState.displayMode === 'processed';
          
          if (isProcessedMode) {
            // If in processed mode, return processed_text_regions if available
            if (state.currentSession.processed_text_regions && state.currentSession.processed_text_regions.length > 0) {
              return state.currentSession.processed_text_regions;
            } else {
              // If no processed regions exist yet, return OCR regions as fallback
              return state.currentSession.text_regions.map(region => ({
                ...region,
                // Ensure user_input_text is preserved even when returning OCR regions in processed mode
                user_input_text: region.user_input_text || ''
              }));
            }
          }
          return state.currentSession.text_regions;
        },

        // Basic setters
        setCurrentSession: (session) => {
          if (session) {
            const currentState = get();
            
            // Record original box sizes for all regions when setting session
            const processedSession = {
              ...session,
              text_regions: session.text_regions.map(region => recordOriginalBoxSize(region)),
              processed_text_regions: session.processed_text_regions?.map(region => recordOriginalBoxSize(region))
            };
            
            set({ 
              currentSession: processedSession,
              // Preserve current display mode instead of resetting to 'original'
              processingState: {
                ...currentState.processingState,
                isProcessing: false,
                progress: null,
                // Only reset displayMode for truly new sessions, not updates
                displayMode: currentState.currentSession?.id === session.id 
                  ? currentState.processingState.displayMode 
                  : 'original',
                showRegionOverlay: currentState.currentSession?.id === session.id 
                  ? currentState.processingState.showRegionOverlay 
                  : false,
              }
            });
          } else {
            set({ 
              currentSession: session,
              // Also reset processing state when clearing session
              processingState: {
                isProcessing: false,
                progress: null,
                displayMode: 'original',
                showRegionOverlay: false,
              }
            });
          }
        },
        setLoading: (loading) => set({ isLoading: loading }),
        setError: (error) => set({ error }),
        
        // File upload trigger
        setShouldAutoTriggerUpload: (should) => set({ shouldAutoTriggerUpload: should }),

        // Canvas actions
        setCanvasScale: (scale) =>
          set((state) => ({
            canvasState: { ...state.canvasState, scale },
          })),

        setCanvasOffset: (offset) =>
          set((state) => ({
            canvasState: { ...state.canvasState, offset },
          })),

        setSelectedRegion: (regionId) =>
          set((state) => ({
            canvasState: { ...state.canvasState, selectedRegionId: regionId },
          })),

        setCanvasDragging: (isDragging) =>
          set((state) => ({
            canvasState: { ...state.canvasState, isDragging },
          })),

        setSelectionMode: (isSelecting, start, end) =>
          set((state) => ({
            canvasState: {
              ...state.canvasState,
              isSelecting,
              selectionStart: start || null,
              selectionEnd: end || null,
            },
          })),

        setActiveTool: (activeTool) =>
          set((state) => ({
            canvasState: { ...state.canvasState, activeTool },
          })),

        resetCanvasState: () =>
          set((state) => ({
            canvasState: initialCanvasState,
          })),

        // Processing actions
        setImageDisplayMode: (displayMode) =>
          set((state) => ({
            processingState: {
              ...state.processingState,
              displayMode,
            },
          })),

        setShowRegionOverlay: (showRegionOverlay) =>
          set((state) => ({
            processingState: {
              ...state.processingState,
              showRegionOverlay,
            },
          })),

        // Settings actions
        setDarkMode: (darkMode) =>
          set((state) => ({
            settings: { ...state.settings, darkMode },
          })),

        setShowConfidence: (showConfidence) =>
          set((state) => ({
            settings: { ...state.settings, showConfidence },
          })),

        setAutoDetectText: (autoDetectText) =>
          set((state) => ({
            settings: { ...state.settings, autoDetectText },
          })),

        // Session actions
        createSession: async (file, onProgress) => {
          const { setLoading, setError, setCurrentSession, clearUndoHistory } = get();
          
          try {
            setLoading(true);
            setError(null);
            
            // Validate file
            const validation = apiService.validateImageFile(file);
            if (!validation.valid) {
              throw new Error(validation.error);
            }

            const session = await apiService.createSessionWithProgress(file, onProgress);
            setCurrentSession(session);
            clearUndoHistory(); // Clear undo history for new session
            return session;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to create session';
            setError(errorMessage);
            throw error;
          } finally {
            setLoading(false);
          }
        },

        updateTextRegions: async (regions, mode = 'auto', exportCsv = true, manageLoadingState = true) => {
          const { currentSession, setLoading, setError, setCurrentSession } = get();
          
          if (!currentSession) {
            throw new Error('No active session');
          }

          try {
            if (manageLoadingState) {
              setLoading(true);
              setError(null);
            }
            
            const updatedSession = await apiService.updateTextRegions(
              currentSession.id,
              regions,
              mode,
              exportCsv
            );
            setCurrentSession(updatedSession);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update text regions';
            setError(errorMessage);
            throw error;
          } finally {
            if (manageLoadingState) {
              setLoading(false);
            }
          }
        },

        // Removed deprecated synchronous processing method
        // Use processTextRemovalAsync for better performance and real-time progress

        processTextRemovalAsync: async () => {
          const { 
            currentSession, 
            setError, 
            setCurrentTaskId,
            clearProcessedHistory,
          } = get();
          
          if (!currentSession) {
            throw new Error('No active session');
          }

          try {
            setError(null);
            
            // Clear processed history when starting a new process
            clearProcessedHistory();

            // Start async processing
            const response = await apiService.processTextRemovalAsync(
              currentSession.id, 
              currentSession.text_regions
            );
            
            // Store task ID for progress monitoring
            setCurrentTaskId(response.task_id);
            
            console.log('🚀 Started async processing:', {
              taskId: response.task_id,
              sessionId: response.session_id,
              websocketUrl: response.websocket_url,
              estimatedDuration: response.estimated_duration
            });

            return response.task_id;
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to start async text removal';
            setError(errorMessage);
            throw error;
          }
        },

        setCurrentTaskId: (taskId) => {
          set({ currentTaskId: taskId });
        },

        downloadResult: async () => {
          const { currentSession, setError } = get();
          
          if (!currentSession) {
            throw new Error('No active session');
          }

          try {
            setError(null);
            
            const blob = await apiService.downloadResult(currentSession.id);
            
            // Generate filename based on current state
            const originalName = currentSession.original_image.filename;
            const nameWithoutExt = originalName.replace(/\.[^/.]+$/, ""); // Remove extension
            const extension = originalName.match(/\.[^/.]+$/)?.[0] || '.jpg'; // Get extension or default to .jpg
            
            let filename = `${nameWithoutExt}_textRemoved`;
            
            // More reliable approach: check if current processed_image contains generated text
            // We can detect this by checking if there are regions with user_input_text AND the image path suggests generated content
            const hasRegionsWithUserText = currentSession.processed_text_regions && 
                                          currentSession.processed_text_regions.some(region => 
                                            region.user_input_text && region.user_input_text.trim().length > 0
                                          );
            
            // Check if current processed_image path indicates it has generated text
            // Generated text images typically have different timestamps or identifiers in their paths
            const currentImagePath = currentSession.processed_image?.path || '';
            const imagePathSuggestsGenerated = currentImagePath.includes('generated') || 
                                             (hasRegionsWithUserText && currentSession.status === 'generated');
            
            // Only add generateText suffix if we have user text regions AND image path suggests it's generated content
            if (hasRegionsWithUserText && imagePathSuggestsGenerated) {
              filename += '_generateText';
            }
            
            filename += extension;
            apiService.downloadBlob(blob, filename);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download result';
            setError(errorMessage);
            throw error;
          }
        },

        downloadRegionsCSV: async () => {
          const { currentSession, setError } = get();
          
          if (!currentSession) {
            throw new Error('No active session');
          }

          try {
            setError(null);
            
            const blob = await apiService.downloadRegionsCSV(currentSession.id);
            const filename = `${currentSession.original_image.filename}_regions.csv`;
            apiService.downloadBlob(blob, filename);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download regions CSV';
            setError(errorMessage);
            throw error;
          }
        },

        deleteSession: async () => {
          const { currentSession, setLoading, setError, setCurrentSession } = get();
          
          if (!currentSession) {
            return;
          }

          try {
            setLoading(true);
            setError(null);
            
            await apiService.deleteSession(currentSession.id);
            setCurrentSession(null);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete session';
            setError(errorMessage);
            throw error;
          } finally {
            setLoading(false);
          }
        },

        generateTextInRegions: async () => {
          const { currentSession, setLoading, setError, setCurrentSession, setImageDisplayMode, setShowRegionOverlay, updateTextRegions, processingState } = get();
          
          if (!currentSession) {
            throw new Error('No active session');
          }

          try {
            setLoading(true);
            setError(null);
            
            // Store old state for undo
            const oldProcessedImage = currentSession.processed_image 
              ? JSON.parse(JSON.stringify(currentSession.processed_image))
              : null;
            const oldProcessedRegions = currentSession.processed_text_regions 
              ? JSON.parse(JSON.stringify(currentSession.processed_text_regions))
              : [];
            
            // Get the regions to work with based on current display mode - use getCurrentDisplayRegions for consistency
            const regionsToSync = get().getCurrentDisplayRegions();
            
            // Determine which mode to use for the update
            const updateMode = processingState.displayMode === 'processed' ? 'processed' : 'ocr';
            
            // First, sync current regions to backend to ensure coordinates are up-to-date (without CSV export)
            await updateTextRegions(regionsToSync, updateMode, false, false);
            
            // Wait a bit for state synchronization
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Get fresh regions after sync to ensure we have the latest state
            const freshRegions = get().getCurrentDisplayRegions();
            
            // Collect regions with user input text from fresh display regions (where user fills text)
            const regionsWithText = freshRegions
              .filter(region => region.user_input_text && region.user_input_text.trim().length > 0)
              .map(region => ({
                region_id: region.id,
                user_text: region.user_input_text!
              }));

            if (regionsWithText.length === 0) {
              throw new Error('No regions with user input text to generate');
            }

            const updatedSession = await apiService.generateTextInRegions(
              currentSession.id,
              regionsWithText
            );
            
            // Create undo command for text generation
            const generateCommand = createGenerateTextCommand(
              currentSession.id,
              oldProcessedImage,
              updatedSession.processed_image || null,
              oldProcessedRegions,
              updatedSession.processed_text_regions || [],
              processingState.displayMode,
              async (sessionData: any) => {
                // Get the latest session state and update it with restored data
                const { currentSession, setCurrentSession, setImageDisplayMode, setShowRegionOverlay } = get();
                if (currentSession) {
                  console.log('Undo text generation - restore previous state:', {
                    current_processed_image: currentSession.processed_image?.path,
                    restore_to_processed_image: sessionData.processed_image?.path,
                    keepProcessedMode: sessionData.keepProcessedMode,
                    showRegionOverlay: sessionData.showRegionOverlay
                  });
                  
                  try {
                    // Call the new restore API to sync backend state
                    const restoredSession = await apiService.restoreSessionState(
                      currentSession.id,
                      sessionData.processed_image,
                      sessionData.processed_text_regions || []
                    );
                    
                    // Update frontend with the restored session
                    setCurrentSession({
                      ...restoredSession,
                      updated_at: new Date().toISOString() // Force timestamp update for image reload
                    });
                    
                    // Ensure we stay in processed mode and show regions if specified
                    if (sessionData.keepProcessedMode) {
                      console.log('🔄 Setting display mode to processed');
                      setImageDisplayMode('processed');
                    }
                    
                    if (sessionData.showRegionOverlay) {
                      console.log('👁️ Setting showRegionOverlay to true');
                      // Use the store's set function directly to ensure the update works
                      set((state) => ({
                        processingState: {
                          ...state.processingState,
                          showRegionOverlay: true
                        }
                      }));
                    }
                    
                    console.log('✅ Backend session state successfully restored with display mode preserved');
                  } catch (error) {
                    console.error('❌ Failed to restore session:', error);
                    // Fallback to frontend-only update
                    const updatedSession = {
                      ...currentSession,
                      processed_image: sessionData.processed_image,
                      processed_text_regions: sessionData.processed_text_regions,
                      updated_at: new Date().toISOString()
                    };
                    setCurrentSession(updatedSession);
                    
                    // Apply display mode changes even in fallback
                    if (sessionData.keepProcessedMode) {
                      console.log('🔄 [Fallback] Setting display mode to processed');
                      setImageDisplayMode('processed');
                    }
                    
                    if (sessionData.showRegionOverlay) {
                      console.log('👁️ [Fallback] Setting showRegionOverlay to true');
                      // Use the store's set function directly to ensure the update works
                      set((state) => ({
                        processingState: {
                          ...state.processingState,
                          showRegionOverlay: true
                        }
                      }));
                    }
                  }
                }
              }
            );
            
            // Add to undo history only
            set((state) => {
              const isOcrMode = processingState.displayMode === 'original';
              
              if (isOcrMode) {
                const newHistory = [
                  ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                  generateCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    ocrHistory: newHistory,
                    ocrCurrentIndex: newHistory.length - 1
                  }
                };
              } else {
                const newHistory = [
                  ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                  generateCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    processedHistory: newHistory,
                    processedCurrentIndex: newHistory.length - 1
                  }
                };
              }
            });
            
            // Update session state with fresh timestamp to force UI refresh
            setCurrentSession({
              ...updatedSession,
              updated_at: new Date().toISOString()
            });
            
            // Automatically switch to processed image view to show the generated text
            setImageDisplayMode('processed');
            // Hide region overlay by default after text generation to show clean result
            setShowRegionOverlay(false);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to generate text';
            setError(errorMessage);
            throw error;
          } finally {
            setLoading(false);
          }
        },

        // Region actions
        addTextRegion: (region) => {
          const { processingState, removeTextRegionInternal, setSelectedRegion } = get();
          let newRegion: TextRegion;
          
          set((state) => {
            if (!state.currentSession) return state;

            // Generate sequential ID by finding the highest existing region number
            const existingRegions = state.currentSession.text_regions;
            const regionNumbers = existingRegions
              .map(r => {
                const match = r.id.match(/region_(\d+)/);
                return match ? parseInt(match[1], 10) : 0;
              })
              .filter(num => !isNaN(num));
            
            const nextRegionNumber = regionNumbers.length > 0 ? Math.max(...regionNumbers) + 1 : 1;
            const newRegionId = `region_${nextRegionNumber}`;

            // Calculate center position and 10% size
            const imageWidth = state.currentSession.original_image.dimensions.width;
            const imageHeight = state.currentSession.original_image.dimensions.height;
            
            const regionWidth = imageWidth * 0.1;
            const regionHeight = imageHeight * 0.1;
            const centerX = (imageWidth - regionWidth) / 2;
            const centerY = (imageHeight - regionHeight) / 2;

            const regionBbox = region.bounding_box || {
              x: centerX,
              y: centerY,
              width: regionWidth,
              height: regionHeight
            };

            newRegion = {
              ...region,
              id: newRegionId,
              bounding_box: regionBbox,
              corners: region.corners || [
                { x: centerX, y: centerY },
                { x: centerX + regionWidth, y: centerY },
                { x: centerX + regionWidth, y: centerY + regionHeight },
                { x: centerX, y: centerY + regionHeight }
              ],
              confidence: region.confidence || 1.0,
              is_selected: true, // Make new region selected by default
              is_user_modified: true,
              user_input_text: region.user_input_text || "",
              original_text: region.original_text || "",
              // Record original box size for new region
              original_box_size: { ...regionBbox },
              is_size_modified: false
            };

            const isOriginalMode = state.processingState.displayMode === 'original';
            let updatedSession;
            
            if (isOriginalMode) {
              // Add to OCR text_regions
              updatedSession = {
                ...state.currentSession,
                text_regions: [...state.currentSession.text_regions, newRegion],
              };
              
              // Change status to editing when adding OCR regions
              if (state.currentSession.status === 'completed' || state.currentSession.status === 'generated') {
                updatedSession.status = 'editing';
              }
            } else {
              // Add to processed_text_regions
              let processedRegions = state.currentSession.processed_text_regions;
              
              // If processed_text_regions doesn't exist, create it from OCR regions
              if (!processedRegions) {
                processedRegions = JSON.parse(JSON.stringify(state.currentSession.text_regions));
              }
                
              updatedSession = {
                ...state.currentSession,
                processed_text_regions: [...processedRegions, newRegion],
              };
            }

            // Update canvas selected region and add region
            const updatedState = {
              currentSession: updatedSession,
              canvasState: {
                ...state.canvasState,
                selectedRegionId: newRegionId
              }
            };

            return updatedState;
          });

          // Create undo command after the state is updated
          const addCommand = createAddRegionCommand(
            newRegion,
            processingState.displayMode,
            () => {}, // addFunction is not needed since region is already added
            removeTextRegionInternal
          );

          // Add to undo history only
          set((state) => {
            const isOcrMode = processingState.displayMode === 'original';
            
            if (isOcrMode) {
              const newHistory = [
                ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                addCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  ocrHistory: newHistory,
                  ocrCurrentIndex: newHistory.length - 1
                }
              };
            } else {
              const newHistory = [
                ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                addCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  processedHistory: newHistory,
                  processedCurrentIndex: newHistory.length - 1
                }
              };
            }
          });
        },

        // Internal method to add region without undo tracking (used by undo system)
        addTextRegionInternal: (region) => {
          set((state) => {
            if (!state.currentSession) return state;

            const isOriginalMode = state.processingState.displayMode === 'original';
            
            let updatedSession;
            
            if (isOriginalMode) {
              // Add to OCR text_regions
              updatedSession = {
                ...state.currentSession,
                text_regions: [...state.currentSession.text_regions, region],
              };
              
              // Change status to editing when adding OCR regions
              if (state.currentSession.status === 'completed' || state.currentSession.status === 'generated') {
                updatedSession.status = 'editing';
              }
            } else {
              // Add to processed_text_regions
              let processedRegions = state.currentSession.processed_text_regions;
              
              // If processed_text_regions doesn't exist, create it from OCR regions
              if (!processedRegions) {
                processedRegions = JSON.parse(JSON.stringify(state.currentSession.text_regions));
              }
                
              updatedSession = {
                ...state.currentSession,
                processed_text_regions: [...processedRegions, region],
              };
            }

            return {
              currentSession: updatedSession,
              canvasState: {
                ...state.canvasState,
                selectedRegionId: region.id
              }
            };
          });
        },

        // Internal method to remove region without undo tracking (used by undo system)
        removeTextRegionInternal: (regionId) => {
          set((state) => {
            if (!state.currentSession) return state;

            const isOriginalMode = state.processingState.displayMode === 'original';
            
            let updatedSession;
            
            if (isOriginalMode) {
              // Remove from OCR text_regions
              updatedSession = {
                ...state.currentSession,
                text_regions: state.currentSession.text_regions.filter(
                  (region) => region.id !== regionId
                ),
              };
              
              // Change status to editing when removing OCR regions
              if (state.currentSession.status === 'completed' || state.currentSession.status === 'generated') {
                updatedSession.status = 'editing';
              }
            } else {
              // Remove from processed_text_regions
              let processedRegions = state.currentSession.processed_text_regions;
              
              // If processed_text_regions doesn't exist, create it from OCR regions
              if (!processedRegions) {
                processedRegions = JSON.parse(JSON.stringify(state.currentSession.text_regions));
              }
                
              updatedSession = {
                ...state.currentSession,
                processed_text_regions: processedRegions.filter(
                  (region) => region.id !== regionId
                ),
              };
            }

            return {
              currentSession: updatedSession,
              canvasState: {
                ...state.canvasState,
                selectedRegionId: state.canvasState.selectedRegionId === regionId ? null : state.canvasState.selectedRegionId
              }
            };
          });
        },

        updateTextRegion: (regionId, updates) =>
          set((state) => {
            if (!state.currentSession) return state;

            const isOriginalMode = state.processingState.displayMode === 'original';
            
            let updatedSession;
            
            if (isOriginalMode) {
              // Update OCR text_regions (for original image)
              updatedSession = {
                ...state.currentSession,
                text_regions: state.currentSession.text_regions.map((region) => {
                  if (region.id === regionId) {
                    let updatedRegion = { ...region, ...updates, is_user_modified: true };
                    // If bounding_box is being updated, mark as size modified
                    if (updates.bounding_box) {
                      updatedRegion = markRegionSizeModified(updatedRegion);
                    }
                    return updatedRegion;
                  }
                  return region;
                }),
              };

              // Change status to editing when modifying OCR regions structure, but not for simple text updates
              if ((state.currentSession.status === 'completed' || state.currentSession.status === 'generated') && 
                  (updates.bounding_box || updates.corners)) {
                updatedSession.status = 'editing';
              }
              // Allow text editing without changing status (for annotation purposes)
              // Only position/structure changes trigger editing status
            } else {
              // Update processed_text_regions (for processed image)
              let processedRegions = state.currentSession.processed_text_regions;
              
              // If processed_text_regions doesn't exist, create it from OCR regions
              if (!processedRegions) {
                processedRegions = JSON.parse(JSON.stringify(state.currentSession.text_regions));
              }
                
              updatedSession = {
                ...state.currentSession,
                processed_text_regions: processedRegions.map((region) => {
                  if (region.id === regionId) {
                    let updatedRegion = { ...region, ...updates, is_user_modified: true };
                    // If bounding_box is being updated, mark as size modified
                    if (updates.bounding_box) {
                      updatedRegion = markRegionSizeModified(updatedRegion);
                    }
                    return updatedRegion;
                  }
                  return region;
                }),
              };
              
              // Don't change status when updating processed regions - they're for display/text generation only
            }

            return {
              currentSession: updatedSession,
            };
          }),

        removeTextRegion: (regionId) => {
          const { processingState, addTextRegionInternal } = get();
          let deletedRegion: TextRegion | null = null;
          
          set((state) => {
            if (!state.currentSession) return state;

            const isOriginalMode = state.processingState.displayMode === 'original';
            
            let updatedSession;
            
            if (isOriginalMode) {
              // Find the region to delete
              deletedRegion = state.currentSession.text_regions.find(r => r.id === regionId) || null;
              
              // Remove from OCR text_regions
              updatedSession = {
                ...state.currentSession,
                text_regions: state.currentSession.text_regions.filter(
                  (region) => region.id !== regionId
                ),
              };
              
              // Change status to editing when removing OCR regions
              if (state.currentSession.status === 'completed' || state.currentSession.status === 'generated') {
                updatedSession.status = 'editing';
              }
            } else {
              // Remove from processed_text_regions
              let processedRegions = state.currentSession.processed_text_regions;
              
              // If processed_text_regions doesn't exist, create it from OCR regions
              if (!processedRegions) {
                processedRegions = JSON.parse(JSON.stringify(state.currentSession.text_regions));
              }
              
              // Find the region to delete
              deletedRegion = processedRegions.find(r => r.id === regionId) || null;
                
              updatedSession = {
                ...state.currentSession,
                processed_text_regions: processedRegions.filter(
                  (region) => region.id !== regionId
                ),
              };
              
              // Don't change status when removing from processed regions
            }

            return {
              currentSession: updatedSession,
              canvasState: {
                ...state.canvasState,
                selectedRegionId: state.canvasState.selectedRegionId === regionId ? null : state.canvasState.selectedRegionId
              }
            };
          });
          
          // Create undo command if region was found
          if (deletedRegion) {
            const deleteCommand = createDeleteRegionCommand(
              deletedRegion,
              processingState.displayMode,
              addTextRegionInternal, // Use internal method to avoid creating new undo commands
              (id: string) => {} // removeFunction not needed since already removed
            );
            
            // Add to undo history only
            set((state) => {
              const isOcrMode = processingState.displayMode === 'original';
              
              if (isOcrMode) {
                const newHistory = [
                  ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                  deleteCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    ocrHistory: newHistory,
                    ocrCurrentIndex: newHistory.length - 1
                  }
                };
              } else {
                const newHistory = [
                  ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                  deleteCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    processedHistory: newHistory,
                    processedCurrentIndex: newHistory.length - 1
                  }
                };
              }
            });
          }
        },

        updateTextRegionWithUndo: (regionId, updates) => {
          const { processingState, updateTextRegion, getCurrentDisplayRegions } = get();
          
          // Find the current region to get old values
          const currentRegions = getCurrentDisplayRegions();
          const currentRegion = currentRegions.find(r => r.id === regionId);
          
          if (!currentRegion) return;
          
          const isProcessedMode = processingState.displayMode === 'processed';
          
          // Determine which text field is being updated
          let textField: 'edited_text' | 'user_input_text';
          let oldText: string;
          let newText: string;
          
          if (isProcessedMode) {
            textField = 'user_input_text';
            oldText = currentRegion.user_input_text || '';
            newText = updates.user_input_text || '';
          } else {
            textField = 'edited_text';
            oldText = currentRegion.edited_text || currentRegion.original_text || '';
            newText = updates.edited_text || '';
          }
          
          // Only create undo command if text actually changed
          if (oldText !== newText) {
            const editCommand = createEditTextCommand(
              regionId,
              oldText,
              newText,
              textField,
              processingState.displayMode,
              updateTextRegion
            );
            
            // Add to undo history only
            set((state) => {
              const isOcrMode = processingState.displayMode === 'original';
              
              if (isOcrMode) {
                const newHistory = [
                  ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                  editCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    ocrHistory: newHistory,
                    ocrCurrentIndex: newHistory.length - 1
                  }
                };
              } else {
                const newHistory = [
                  ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                  editCommand
                ];
                
                if (newHistory.length > state.undoState.maxHistorySize) {
                  newHistory.shift();
                }
                
                return {
                  undoState: {
                    ...state.undoState,
                    processedHistory: newHistory,
                    processedCurrentIndex: newHistory.length - 1
                  }
                };
              }
            });
          }
          
          // Apply the update
          updateTextRegion(regionId, updates);
        },

        moveRegionWithUndo: (regionId, oldBounds, newBounds) => {
          const { processingState, updateTextRegion } = get();
          
          // Only create undo command if bounds actually changed
          if (oldBounds.x === newBounds.x && oldBounds.y === newBounds.y && 
              oldBounds.width === newBounds.width && oldBounds.height === newBounds.height) {
            return; // No change, no need to create undo command
          }
          
          const moveCommand = createMoveRegionCommand(
            regionId,
            oldBounds,
            newBounds,
            processingState.displayMode,
            updateTextRegion
          );
          
          // Add to undo history
          set((state) => {
            const isOcrMode = processingState.displayMode === 'original';
            
            if (isOcrMode) {
              const newHistory = [
                ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                moveCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  ocrHistory: newHistory,
                  ocrCurrentIndex: newHistory.length - 1
                }
              };
            } else {
              const newHistory = [
                ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                moveCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  processedHistory: newHistory,
                  processedCurrentIndex: newHistory.length - 1
                }
              };
            }
          });
        },

        resizeRegionWithUndo: (regionId, oldBounds, newBounds) => {
          const { processingState, updateTextRegion } = get();
          
          // Only create undo command if bounds actually changed
          if (oldBounds.x === newBounds.x && oldBounds.y === newBounds.y && 
              oldBounds.width === newBounds.width && oldBounds.height === newBounds.height) {
            return; // No change, no need to create undo command
          }
          
          const resizeCommand = createResizeRegionCommand(
            regionId,
            oldBounds,
            newBounds,
            processingState.displayMode,
            updateTextRegion
          );
          
          // Add to undo history only
          set((state) => {
            const isOcrMode = processingState.displayMode === 'original';
            
            if (isOcrMode) {
              const newHistory = [
                ...state.undoState.ocrHistory.slice(0, state.undoState.ocrCurrentIndex + 1),
                resizeCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  ocrHistory: newHistory,
                  ocrCurrentIndex: newHistory.length - 1
                }
              };
            } else {
              const newHistory = [
                ...state.undoState.processedHistory.slice(0, state.undoState.processedCurrentIndex + 1),
                resizeCommand
              ];
              
              if (newHistory.length > state.undoState.maxHistorySize) {
                newHistory.shift();
              }
              
              return {
                undoState: {
                  ...state.undoState,
                  processedHistory: newHistory,
                  processedCurrentIndex: newHistory.length - 1
                }
              };
            }
          });
        },

        // Undo system actions
        undoLastCommand: async () => {
          const state = get();
          const { processingState } = state;
          const isOcrMode = processingState.displayMode === 'original';
          
          if (isOcrMode && state.undoState.ocrCurrentIndex >= 0) {
            const command = state.undoState.ocrHistory[state.undoState.ocrCurrentIndex];
            await command.undo();
            
            set((prevState) => ({
              undoState: {
                ...prevState.undoState,
                ocrCurrentIndex: prevState.undoState.ocrCurrentIndex - 1
              }
            }));
          } else if (!isOcrMode && state.undoState.processedCurrentIndex >= 0) {
            const command = state.undoState.processedHistory[state.undoState.processedCurrentIndex];
            await command.undo();
            
            set((prevState) => ({
              undoState: {
                ...prevState.undoState,
                processedCurrentIndex: prevState.undoState.processedCurrentIndex - 1
              }
            }));
          }
        },

        canUndo: () => {
          const state = get();
          const { processingState } = state;
          const isOcrMode = processingState.displayMode === 'original';
          
          return isOcrMode ? 
            state.undoState.ocrCurrentIndex >= 0 : 
            state.undoState.processedCurrentIndex >= 0;
        },

        clearUndoHistory: () => {
          set((state) => ({
            undoState: {
              ...state.undoState,
              ocrHistory: [],
              processedHistory: [],
              ocrCurrentIndex: -1,
              processedCurrentIndex: -1
            }
          }));
        },

        clearOcrHistory: () => {
          set((state) => ({
            undoState: {
              ...state.undoState,
              ocrHistory: [],
              ocrCurrentIndex: -1
            }
          }));
        },

        clearProcessedHistory: () => {
          set((state) => ({
            undoState: {
              ...state.undoState,
              processedHistory: [],
              processedCurrentIndex: -1
            }
          }));
        },

        // Utility actions
        reset: () => set(initialState),
      }),
      {
        name: 'labeltool-storage',
        partialize: (state) => ({
          settings: state.settings,
          canvasState: {
            scale: state.canvasState.scale,
            offset: state.canvasState.offset,
          },
          // processingState.displayMode should not be persisted
          // as it's session-specific and should reset for new sessions
          // undoState should not be persisted as it's session-specific
        }),
      }
    ),
    {
      name: 'LabelTool Store',
    }
  )
);