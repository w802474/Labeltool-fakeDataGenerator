import React, { useEffect } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useRegionSync } from '@/hooks/useRegionSync';
import { useConfirmDialog } from '@/hooks/useConfirmDialog';
import { useFileUploadTrigger } from '@/hooks/useFileUploadTrigger';
import { useToast } from '@/hooks/useToast';
import { FileUpload } from '@/components/FileUpload';
import { ImageCanvas } from '@/components/ImageCanvas';
import { Toolbar } from '@/components/Toolbar';
import { StatusBar } from '@/components/StatusBar';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Header } from '@/components/Header';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Toast } from '@/components/ui/Toast';
import { EditableText } from '@/components/EditableText';

function App() {
  const { currentSession, error, setError, canvasState, setSelectedRegion, shouldAutoTriggerUpload, setShouldAutoTriggerUpload, updateTextRegion, updateTextRegionWithUndo, processingState, getCurrentDisplayRegions, addTextRegion, removeTextRegion } = useAppStore();
  
  // Initialize keyboard shortcuts
  useKeyboardShortcuts();
  
  // Sync region selection between canvas and list
  useRegionSync(canvasState.selectedRegionId);
  
  // Initialize confirm dialog
  const { isOpen, options, showConfirm, handleConfirm, handleCancel } = useConfirmDialog();
  
  // Initialize file upload trigger (only for hidden input)
  const { 
    triggerFileSelect, 
    fileInputRef, 
    handleFileChange
  } = useFileUploadTrigger();
  
  // Initialize toast notifications
  const { toasts, removeToast, showSuccess, showError } = useToast();

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, setError]);

  // Handle adding new region
  const handleAddRegion = () => {
    addTextRegion({
      confidence: 1.0,
      is_selected: true,
      is_user_modified: true,
      user_input_text: "",
      original_text: ""
    });
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
        {/* Header */}
        <Header showConfirm={showConfirm} />
        
        {/* Main Content */}
        <main className="container mx-auto px-4 py-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-5 w-5 text-red-500">⚠️</div>
                  <span className="text-red-700 dark:text-red-400 font-medium">
                    {error}
                  </span>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-500 hover:text-red-700 dark:hover:text-red-300"
                >
                  ×
                </button>
              </div>
            </div>
          )}

          {!currentSession ? (
            /* Upload State */
            <div className="flex flex-col items-center justify-center min-h-[600px] space-y-8">
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Intelligent Text Detection & Removal
                </h1>
                <p className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl">
                  Upload an image to automatically detect text regions, 
                  manually adjust boundaries, and generate clean images 
                  with advanced inpainting technology.
                </p>
              </div>
              
              <FileUpload 
                className="w-full max-w-2xl"
                autoTrigger={shouldAutoTriggerUpload}
                onUploadComplete={() => {
                  // Reset auto trigger after upload starts
                  setShouldAutoTriggerUpload(false);
                }}
              />
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl text-center">
                <div className="space-y-2">
                  <div className="text-3xl">🔍</div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Auto Detection</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    AI-powered text region detection with high precision
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="text-3xl">✏️</div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Manual Adjustment</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Fine-tune text boundaries with intuitive controls
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="text-3xl">🎨</div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Smart Removal</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Advanced inpainting preserves background textures
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Editor State */
            <div className="space-y-6">
              {/* Toolbar */}
              <Toolbar showConfirm={showConfirm} showToast={showSuccess} showErrorToast={showError} />
              
              {/* Main Editor */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Canvas Area */}
                <div className="lg:col-span-3">
                  <ImageCanvas />
                </div>
                
                {/* Sidebar */}
                <div className="space-y-4">
                  {/* Session Info */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h3 className="font-semibold mb-2 text-gray-900 dark:text-gray-100">Session Info</h3>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">File:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">{currentSession.original_image.filename}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Size:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">{currentSession.original_image.dimensions.width} × {currentSession.original_image.dimensions.height}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>{' '}
                        <span className={`capitalize ${
                          currentSession.status === 'generated' 
                            ? 'text-green-600 dark:text-green-400 font-medium' 
                            : 'text-gray-900 dark:text-gray-100'
                        }`}>
                          {currentSession.status === 'generated' ? 'Text Generated' : currentSession.status.toLowerCase()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Regions:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">{getCurrentDisplayRegions().length}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Text Regions List - show based on display mode and overlay settings */}
                  {(processingState.displayMode === 'original' || 
                    (processingState.displayMode === 'processed' && processingState.showRegionOverlay)) && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Text Regions ({getCurrentDisplayRegions().length})</h3>
                        <div className="flex items-center space-x-2">
                          {/* Delete selected region button */}
                          <button
                            onClick={() => {
                              if (canvasState.selectedRegionId) {
                                const selectedId = canvasState.selectedRegionId;
                                removeTextRegion(selectedId);
                                setSelectedRegion(null);
                              }
                            }}
                            className={`w-6 h-6 rounded bg-red-600 hover:bg-red-700 text-white text-sm font-bold flex items-center justify-center transition-colors ${!canvasState.selectedRegionId ? 'invisible' : ''}`}
                            title="Delete selected region"
                            disabled={!canvasState.selectedRegionId}
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                          {/* Add new region button */}
                          <button
                            onClick={handleAddRegion}
                            className="w-6 h-6 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold flex items-center justify-center transition-colors"
                            title="Add new text region"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    <div className="space-y-2 max-h-80 overflow-y-auto p-2" id="text-regions-list">
                      {getCurrentDisplayRegions().length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          No text regions detected
                        </p>
                      ) : (
                        getCurrentDisplayRegions().map((region, index) => {
                          const isSelected = canvasState.selectedRegionId === region.id;
                          const isProcessedMode = processingState.displayMode === 'processed';
                          
                          // Different logic for processed mode (text generation) vs original mode (text editing)
                          const isTextModified = isProcessedMode 
                            ? (region.user_input_text && region.user_input_text.trim().length > 0)
                            : (region.edited_text && region.edited_text !== region.original_text);
                          
                          const displayText = isProcessedMode 
                            ? (region.user_input_text || '')
                            : (region.edited_text || region.original_text || 'No text detected');
                          
                          const placeholderText = isProcessedMode 
                            ? (region.original_text || 'Enter new text...')
                            : '';
                          
                          const handleTextChange = (newText: string) => {
                            if (isProcessedMode) {
                              // In processed mode, update user_input_text
                              updateTextRegionWithUndo(region.id, {
                                user_input_text: newText,
                                is_user_modified: newText.trim() !== ''
                              });
                            } else {
                              // In original mode, update edited_text
                              updateTextRegionWithUndo(region.id, {
                                edited_text: newText,
                                is_user_modified: newText !== region.original_text
                              });
                            }
                          };
                          
                          return (
                            <div
                              key={region.id}
                              className={`p-3 border rounded-lg text-xs space-y-2 cursor-pointer transition-all duration-200 hover:shadow-md ${
                                isSelected 
                                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900 dark:border-blue-400 shadow-md' 
                                  : isTextModified
                                  ? 'border-orange-300 bg-orange-50 dark:bg-orange-900/30 dark:border-orange-400 hover:border-orange-400 dark:hover:border-orange-300'
                                  : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-500'
                              }`}
                              onClick={() => {
                                setSelectedRegion(isSelected ? null : region.id);
                              }}
                              id={`region-item-${region.id}`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <div className="font-medium text-gray-900 dark:text-gray-100">Region {index + 1}</div>
                                  {isTextModified && (
                                    <div className="w-2 h-2 bg-orange-500 rounded-full" title="Text modified by user"></div>
                                  )}
                                </div>
                                <div className={`text-xs px-2 py-1 rounded ${
                                  region.confidence >= 0.8 ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' :
                                  region.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' :
                                  'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
                                }`}>
                                  {Math.round(region.confidence * 100)}%
                                </div>
                              </div>
                              <EditableText
                                text={displayText}
                                onTextChange={handleTextChange}
                                isModified={isTextModified}
                                placeholder={placeholderText || "No text detected"}
                              />
                              <div className="text-gray-400 dark:text-gray-500 text-[10px]">
                                Position: {Math.round(region.bounding_box.x)}, {Math.round(region.bounding_box.y)} • 
                                Size: {Math.round(region.bounding_box.width)}×{Math.round(region.bounding_box.height)}
                                {isTextModified && (
                                  <span className="ml-2 text-orange-500">• Modified</span>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
        
        {/* Status Bar */}
        <StatusBar />
        
        {/* Confirm Dialog */}
        <ConfirmDialog
          isOpen={isOpen}
          onClose={handleCancel}
          onConfirm={handleConfirm}
          title={options.title}
          message={options.message}
          confirmText={options.confirmText}
          cancelText={options.cancelText}
          type={options.type}
        />
        
        {/* Toast Notifications */}
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
          />
        ))}
        
        {/* Hidden file input for triggering file selection */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>
    </ErrorBoundary>
  );
}

export default App;