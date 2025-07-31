import React from 'react';
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
}

export const Toolbar: React.FC<ToolbarProps> = ({ showConfirm, showToast, showErrorToast }) => {
  const {
    currentSession,
    isLoading,
    processTextRemoval,
    downloadResult,
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
  const canDownload = currentSession.status === 'completed' || currentSession.status === 'generated';
  const hasRegions = currentSession.text_regions.length > 0;
  
  // hasProcessedImage should be true if we have processed image, regardless of current status
  // This allows switching back to processed view even after editing OCR regions
  const hasProcessedImage = currentSession.processed_image !== null && currentSession.processed_image !== undefined;
  
  // Get current display regions for various operations
  const currentDisplayRegions = getCurrentDisplayRegions();
  
  // Check for user input text from the correct regions based on display mode
  const hasUserInputText = currentDisplayRegions.some(region => region.user_input_text && region.user_input_text.trim().length > 0);

  const handleProcessing = async () => {
    try {
      await processTextRemoval();
    } catch (error) {
      console.error('Processing failed:', error);
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
      await generateTextInRegions();
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
      console.log('Saving regions for session:', currentSession.id);
      await updateTextRegions(regionsToSave, 'auto', true); // Explicitly export CSV
      console.log('Regions saved successfully');
      
      // Show success toast
      showToast?.(`Successfully saved ${regionsToSave.length} text regions to CSV file.`);
    } catch (error) {
      console.error('Failed to save regions:', error);
      
      // Show error toast
      showErrorToast?.('Failed to save text regions to CSV file. Please try again.');
    }
  };

  const handleToggleImageMode = () => {
    if (hasProcessedImage) {
      const newMode = processingState.displayMode === 'original' ? 'processed' : 'original';
      setImageDisplayMode(newMode);
    }
  };

  const handleToggleRegionOverlay = () => {
    setShowRegionOverlay(!processingState.showRegionOverlay);
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
    if (showConfirm) {
      const confirmed = await showConfirm({
        title: 'Start New Session',
        message: 'Are you sure you want to start a new session? Current progress will be lost.',
        confirmText: 'Yes, Go to Home',
        cancelText: 'Cancel',
        type: 'warning'
      });
      
      if (confirmed) {
        deleteSession();
        // Trigger auto upload when returning to home page
        setShouldAutoTriggerUpload(true);
      }
    } else {
      // Fallback to native confirm if showConfirm is not available
      if (confirm('Are you sure you want to start a new session? Current progress will be lost.')) {
        deleteSession();
        setShouldAutoTriggerUpload(true);
      }
    }
  };


  const handleUndo = () => {
    try {
      undoLastCommand();
    } catch (error) {
      console.error('Undo failed:', error);
      showErrorToast?.('Undo failed. Please try again.');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
      <div className="flex items-center justify-between p-3">
        {/* Left Group - File Actions */}
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewSession}
            icon={<Upload className="h-4 w-4" />}
            title="Select a new image file"
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
            >
              Save Regions
            </Button>
          )}
        </div>

        {/* Center Group - Canvas Controls */}
        <div className="flex items-center space-x-2">
          {/* Undo button - only show when there are operations to undo */}
          {canUndo() && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleUndo}
              title="Undo last operation (Ctrl+Z)"
              icon={<Undo2 className="h-4 w-4" />}
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900"
            />
          )}
          
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

          {/* iOS-style toggle switch for image mode */}
          {hasProcessedImage && (
            <button
              onClick={handleToggleImageMode}
              title={processingState.displayMode === 'original' ? "Switch to Processed Image" : "Switch to Original Image"}
              className={clsx(
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                processingState.displayMode === 'processed' 
                  ? "bg-blue-600" 
                  : "bg-gray-200 dark:bg-gray-700"
              )}
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
          )}

          {/* Region overlay toggle button - only show when viewing processed image */}
          {hasProcessedImage && processingState.displayMode === 'processed' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleRegionOverlay}
              title={processingState.showRegionOverlay ? "Hide Text Regions" : "Show Text Regions on Processed Image"}
              icon={processingState.showRegionOverlay ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              className={clsx(
                processingState.showRegionOverlay && "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
              )}
            />
          )}

          {canvasState.selectedRegionId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                // Remove selected region using the store's removeTextRegion method
                const selectedId = canvasState.selectedRegionId;
                if (selectedId) {
                  removeTextRegion(selectedId);
                  setSelectedRegion(null);
                }
              }}
              title="Delete Selected Region (Delete)"
              icon={<Trash2 className="h-4 w-4" />}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900"
            />
          )}
        </div>

        {/* Right Group - Processing Actions */}
        <div className="flex items-center space-x-2">
          <Button
            variant="gradient"
            size="sm"
            onClick={handleProcessing}
            disabled={!canProcess || isLoading || processingState.isProcessing}
            loading={processingState.isProcessing}
            loadingText="Processing"
            icon={<Play className="h-4 w-4" />}
            title="Process Text Removal (Ctrl + P)"
          >
            {processingState.isProcessing ? "Processing" : "Process"}
          </Button>

          {hasUserInputText && hasProcessedImage && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateText}
              disabled={isLoading}
              icon={<Type className="h-4 w-4" />}
              title="Generate text in regions"
            >
              Generate Text
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
            {processingState.isProcessing && processingState.progress && (
              <span className="text-blue-600 dark:text-blue-400">
                <strong>Progress:</strong> {Math.round(processingState.progress.progress)}%
              </span>
            )}
            {canvasState.selectedRegionId && !processingState.isProcessing && (
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