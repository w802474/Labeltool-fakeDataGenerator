import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ZoomIn, 
  ZoomOut, 
  Download, 
  Play, 
  Trash2,
  Save,
  Upload,
  Maximize2,
  Eye,
  EyeOff,
  Type,
  Undo2
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAppStore } from '@/stores/useAppStore';
import { useCanvas } from '@/hooks/useCanvas';
import { clsx } from 'clsx';

interface ToolbarProps {
  showConfirm?: (options: {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    type?: 'warning' | 'danger' | 'info';
  }) => Promise<boolean>;
  showToast?: (message: string) => void;
  showErrorToast?: (message: string) => void;
  uploadProgress?: any;
  setUploadProgress?: (progress: any) => void;
  isUploading?: boolean;
  setIsUploading?: (uploading: boolean) => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({ 
  showConfirm, 
  showToast, 
  showErrorToast, 
  uploadProgress, 
  setUploadProgress, 
  isUploading, 
  setIsUploading 
}) => {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();
  const {
    currentSession,
    isLoading,
    processTextRemovalAsync,
    currentTaskId,
    setCurrentTaskId,
    downloadResult,
    downloadRegionsCSV,
    deleteSession,
    updateTextRegions,
    removeTextRegion,
    canvasState,
    setSelectedRegion,
    setShouldAutoTriggerUpload,
    processingState,
    setImageDisplayMode,
    setShowRegionOverlay,
    generateTextInRegions,
    getCurrentDisplayRegions,
    undoLastCommand,
    canUndo,
  } = useAppStore();

  const { zoomIn, zoomOut, resetZoom, fitToCanvas } = useCanvas();

  if (!currentSession) return null;

  // Can process if:
  // 1. Initial OCR detection completed OR user is editing regions
  // 2. AND currently viewing original image (not processed)
  const canProcess = 
    (currentSession.status === 'detected' || currentSession.status === 'editing') &&
    processingState.displayMode === 'original';
  const hasRegions = currentSession.text_regions.length > 0;
  
  // hasProcessedImage should be true if we have processed image, regardless of current status
  // This allows switching back to processed view even after editing OCR regions
  const hasProcessedImage = currentSession.processed_image !== null && currentSession.processed_image !== undefined;
  
  // Can download only when in processed mode and have processed image
  const canDownload = (currentSession.status === 'removed' || currentSession.status === 'generated') && 
                      processingState.displayMode === 'processed' && 
                      hasProcessedImage;
  
  // Get current display regions for various operations
  const currentDisplayRegions = getCurrentDisplayRegions();
  
  // Check for user input text from the correct regions based on display mode
  const hasUserInputText = currentDisplayRegions.some(region => region.user_input_text && region.user_input_text.trim().length > 0);
  
  // Generate Text button should only be visible when:
  // 1. We have processed image
  // 2. We have user input text
  // 3. We are in processed mode
  const shouldShowGenerateTextButton = hasUserInputText && 
                                       hasProcessedImage && 
                                       processingState.displayMode === 'processed';

  const handleProcessing = async () => {
    try {
      const taskId = await processTextRemovalAsync();
      // Processing started successfully - no toast needed as progress will be shown in UI
    } catch (error) {
      console.error('Failed to start async processing:', error);
      showErrorToast?.('Failed to start processing. Please try again.');
    }
  };

  const handleDownload = async () => {
    try {
      await downloadResult();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleGenerateText = async () => {
    try {
      await generateTextInRegions(sessionId);
      showToast?.('Successfully generated text in regions!');
    } catch (error) {
      console.error('Text generation failed:', error);
      showErrorToast?.('Failed to generate text. Please ensure you have entered text in the regions.');
    }
  };

  const handleSaveRegions = async () => {
    if (!currentSession) return;
    
    try {
      const regionsToSave = getCurrentDisplayRegions();
      
      // Save regions to backend with CSV export
      await updateTextRegions(regionsToSave, 'auto', true); // Explicitly export CSV
      
      // Automatically download the CSV file
      await downloadRegionsCSV();
      
      // Show success toast
      showToast?.(`Successfully saved and downloaded ${regionsToSave.length} text regions as CSV file.`);
    } catch (error) {
      console.error('Failed to save and download regions:', error);
      
      // Show error toast
      showErrorToast?.('Failed to save and download text regions CSV file. Please try again.');
    }
  };


  const handleToggleImageMode = () => {
    if (hasProcessedImage) {
      const newMode = processingState.displayMode === 'original' ? 'processed' : 'original';
      setImageDisplayMode(newMode);
    }
  };

  const handleToggleRegionOverlay = () => {
    const newShowOverlay = !processingState.showRegionOverlay;
    setShowRegionOverlay(newShowOverlay);
    
    // If hiding regions, clear any selected region
    if (!newShowOverlay) {
      setSelectedRegion(null);
    }
  };

  const handleFitToView = () => {
    if (currentSession) {
      // Assuming a container size - in real implementation, you'd get actual container dimensions
      fitToCanvas(
        currentSession.original_image.dimensions.width,
        currentSession.original_image.dimensions.height,
        1200, // container width
        800   // container height
      );
    }
  };

  const handleNewSession = async () => {
    try {
      // First, save current changes silently
      if (currentSession) {
        const allCurrentRegions = getCurrentDisplayRegions();
        await updateTextRegions(allCurrentRegions, 'auto', false);
      }
      
      // Create and trigger file input for new image selection
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.style.display = 'none';
      
      input.onchange = async (e) => {
        const files = Array.from((e.target as HTMLInputElement).files || []);
        if (files.length === 0) return;
        
        const file = files[0];
        try {
          // Import apiService dynamically to avoid circular imports
          const { apiService } = await import('@/services/api');
          
          setIsUploading?.(true);
          
          // Stage 1: Uploading
          setUploadProgress?.({
            progress: 0,
            stage: 'uploading',
            message: 'Uploading image...',
            managedByToolbar: true,
          });

          // Create new session with progress tracking
          const session = await apiService.createSessionWithProgress(file, (progress) => {
            setUploadProgress?.({
              progress,
              stage: 'uploading',
              message: `Uploading... ${progress}%`,
              managedByToolbar: true,
            });
          });

          // Stage 2: Processing
          setUploadProgress?.({
            progress: 100,
            stage: 'processing',
            message: 'Processing image...',
            managedByToolbar: true,
          });

          // Wait a bit for the backend to process
          await new Promise(resolve => setTimeout(resolve, 500));

          // Stage 3: Text detection
          setUploadProgress?.({
            progress: 100,
            stage: 'detecting',
            message: 'Detecting text regions...',
            managedByToolbar: true,
          });

          // Wait a bit
          await new Promise(resolve => setTimeout(resolve, 300));

          // Navigate to editor page and clear progress
          navigate(`/editor/${session.id}`);
          setUploadProgress?.(null);
          setIsUploading?.(false);
          
        } catch (error) {
          console.error('Failed to process new image:', error);
          const errorMessage = error instanceof Error ? error.message : 'Failed to process new image';
          showErrorToast?.(errorMessage);
          setUploadProgress?.(null);
          setIsUploading?.(false);
        }
        
        // Clean up input
        document.body.removeChild(input);
      };
      
      document.body.appendChild(input);
      input.click();
      
    } catch (error) {
      showErrorToast?.('Failed to save changes. Please try again.');
    }
  };


  const handleUndo = async () => {
    try {
      await undoLastCommand();
    } catch (error) {
      console.error('Undo failed:', error);
      showErrorToast?.('Undo failed. Please try again.');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
      <div className="relative flex items-center justify-between p-3">
        {/* Left Group - File Actions */}
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewSession}
            icon={<Upload className="h-4 w-4" />}
          >
            New Image
          </Button>

          <div className="h-6 border-l border-gray-300 dark:border-gray-600" />

          {/* Save Regions button - only show in original mode */}
          {processingState.displayMode === 'original' && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveRegions}
              disabled={isLoading || !hasRegions}
              icon={<Save className="h-4 w-4" />}
              title="Save regions and download as CSV file"
            >
              Save Regions
            </Button>
          )}
        </div>

        {/* Center Group - Canvas Controls (absolutely positioned at center) */}
        <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center space-x-2">
          {/* Undo button - use visibility instead of conditional rendering for stable layout */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleUndo}
            title="Undo last operation (Ctrl+Z)"
            icon={<Undo2 className="h-4 w-4" />}
            className={`text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900 ${!canUndo() ? 'invisible' : ''}`}
            disabled={!canUndo()}
          />
          
          <div className="flex items-center space-x-1 bg-gray-50 dark:bg-gray-800 rounded-md p-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={zoomOut}
              title="Zoom Out (Ctrl + -)"
              icon={<ZoomOut className="h-4 w-4" />}
            />
            
            <Button
              variant="ghost"
              size="sm"
              onClick={resetZoom}
              title="Reset Zoom (Ctrl + 0)"
              className="min-w-16 text-xs"
            >
              {Math.round(canvasState.scale * 100)}%
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={zoomIn}
              title="Zoom In (Ctrl + +)"
              icon={<ZoomIn className="h-4 w-4" />}
            />
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleFitToView}
            title="Fit to View"
            icon={<Maximize2 className="h-4 w-4" />}
          />

          {/* iOS-style toggle switch for image mode - use visibility for stable layout */}
          <button
            onClick={handleToggleImageMode}
            title={processingState.displayMode === 'original' ? "Switch to Processed Image" : "Switch to Original Image"}
            className={clsx(
              "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
              processingState.displayMode === 'processed' 
                ? "bg-blue-600" 
                : "bg-gray-200 dark:bg-gray-700",
              !hasProcessedImage && "invisible"
            )}
            disabled={!hasProcessedImage}
          >
            <span
              className={clsx(
                "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                processingState.displayMode === 'processed' 
                  ? "translate-x-6" 
                  : "translate-x-1"
              )}
            />
          </button>

          {/* Region overlay toggle button - use visibility for stable layout */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleRegionOverlay}
            title={processingState.showRegionOverlay ? "Hide Text Regions" : "Show Text Regions on Processed Image"}
            icon={processingState.showRegionOverlay ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            className={clsx(
              processingState.showRegionOverlay && "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
              !(hasProcessedImage && processingState.displayMode === 'processed') && "invisible"
            )}
            disabled={!(hasProcessedImage && processingState.displayMode === 'processed')}
          />

        </div>

        {/* Right Group - Processing Actions */}
        <div className="flex items-center space-x-2">
          <Button
            variant="gradient"
            size="sm"
            onClick={handleProcessing}
            disabled={!canProcess || isLoading || !!currentTaskId}
            loading={!!currentTaskId}
            loadingText="Processing"
            icon={<Play className="h-4 w-4" />}
            title="Process Text Removal (Ctrl + P)"
          >
            {!!currentTaskId ? "Processing" : "Process"}
          </Button>

          {shouldShowGenerateTextButton && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateText}
              disabled={isLoading}
              icon={<Type className="h-4 w-4" />}
              title="Generate text in regions"
            >
              Generate
            </Button>
          )}

          <Button
            variant="default"
            size="sm"
            onClick={handleDownload}
            disabled={!canDownload || isLoading}
            icon={<Download className="h-4 w-4" />}
            title="Download Result (Ctrl + D)"
          >
            Download
          </Button>
        </div>
      </div>

      {/* Status Info */}
      <div className="px-3 py-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center space-x-4">
            <span>
              <strong>Status:</strong> {
                currentSession.status === 'generated' 
                  ? 'Text Generated' 
                  : currentSession.status.replace('_', ' ').toLowerCase()
              }
            </span>
            <span>
              <strong>View:</strong> {processingState.displayMode === 'processed' ? 'Processed Image' : 'Original Image'}
            </span>
            <span>
              <strong>Regions:</strong> {getCurrentDisplayRegions().length}
            </span>
            {canvasState.selectedRegionId && !currentTaskId && (
              <span className="text-blue-600 dark:text-blue-400">
                <strong>Selected:</strong> Region {
                  getCurrentDisplayRegions().findIndex(r => r.id === canvasState.selectedRegionId) + 1
                }
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            <span>Use Ctrl+Scroll to zoom, drag to pan</span>
            <span>Press Esc to deselect</span>
          </div>
        </div>
      </div>
    </div>
  );
};