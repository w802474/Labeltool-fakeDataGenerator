import React, { useEffect, useState } from 'react';
import { Upload, Check, X, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/stores/useAppStore';
import { FileUpload } from '@/components/FileUpload';
import { SessionGallery } from '@/components/SessionGallery';
import { UniversalLoader } from '@/components/UniversalLoader';
import { FullscreenUploadOverlay } from '@/components/FullscreenUploadOverlay';
import { apiService } from '@/services/api';

interface HomePageProps {
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

export const HomePage: React.FC<HomePageProps> = ({ 
  showConfirm, 
  showToast, 
  showErrorToast 
}) => {
  const navigate = useNavigate();
  
  const { 
    error, 
    setError, 
    shouldAutoTriggerUpload, 
    setShouldAutoTriggerUpload,
    // Initialization state
    isInitializing,
    hasCheckedDatabase,
    initializeApp,
    // Historical sessions state
    historicalSessions,
    historicalSessionsLoading,
    historicalSessionsError,
    loadHistoricalSessions,
    loadMoreHistoricalSessions,
    deleteHistoricalSession,
    deleteHistoricalSessions,
    // Pagination state
    pagination
  } = useAppStore();
  
  
  // Upload state for gallery
  const [isGalleryUploading, setIsGalleryUploading] = useState(false);
  const [galleryUploadProgress, setGalleryUploadProgress] = useState<any>(null);
  

  // Gallery selection state
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());

  // Initialize app on start
  useEffect(() => {
    if (!hasCheckedDatabase) {
      initializeApp().catch(err => {
        console.error('Failed to initialize app:', err);
      });
    }
  }, [hasCheckedDatabase, initializeApp]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, setError]);


  // Refresh gallery when upload completes (gallery only)
  useEffect(() => {
    if (galleryUploadProgress === null && !isGalleryUploading) {
      // After gallery upload is completed and cleared, refresh the session list
      const timer = setTimeout(() => {
        loadHistoricalSessions().catch(console.error);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [galleryUploadProgress, isGalleryUploading, loadHistoricalSessions]);

  // Handle historical session selection
  const handleSessionSelect = async (sessionId: string) => {
    try {
      // Navigate to editor page
      navigate(`/editor/${sessionId}`);
    } catch (err) {
      console.error('Failed to navigate to session:', err);
    }
  };

  // Handle upload button click for gallery
  const handleUploadButtonClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none';
    
    input.onchange = async (e) => {
      const files = Array.from((e.target as HTMLInputElement).files || []);
      if (files.length === 0) return;
      
      const file = files[0];
      try {
        setIsGalleryUploading(true);
        
        // Stage 1: Uploading
        setGalleryUploadProgress({
          progress: 0,
          stage: 'uploading',
          message: 'Uploading image...',
        });

        // Use apiService to upload with progress
        const session = await apiService.createSessionWithProgress(file, (progress) => {
          setGalleryUploadProgress({
            progress,
            stage: 'uploading',
            message: `Uploading... ${progress}%`,
          });
        });

        // Stage 2: Processing
        setGalleryUploadProgress({
          progress: 100,
          stage: 'processing',
          message: 'Processing image...',
        });

        // Wait a bit for the backend to process
        await new Promise(resolve => setTimeout(resolve, 500));

        // Stage 3: Text detection
        setGalleryUploadProgress({
          progress: 100,
          stage: 'detecting',
          message: 'Detecting text regions...',
        });

        // Wait a bit
        await new Promise(resolve => setTimeout(resolve, 300));

        // Navigate to editor page and clear progress
        navigate(`/editor/${session.id}`);
        setGalleryUploadProgress(null);
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        setError(errorMessage);
        setGalleryUploadProgress(null);
        setIsGalleryUploading(false);
      }
      
      // Clean up input
      document.body.removeChild(input);
    };
    
    document.body.appendChild(input);
    input.click();
  };

  // Handle selection mode toggle
  const handleToggleSelectMode = () => {
    setIsSelectMode(!isSelectMode);
    if (isSelectMode) {
      setSelectedSessions(new Set()); // Clear selections when exiting select mode
    }
  };

  // Handle individual session selection
  const handleToggleSessionSelect = (sessionId: string) => {
    const newSelected = new Set(selectedSessions);
    if (newSelected.has(sessionId)) {
      newSelected.delete(sessionId);
    } else {
      newSelected.add(sessionId);
    }
    setSelectedSessions(newSelected);
  };

  // Handle select all/none
  const handleSelectAll = () => {
    if (selectedSessions.size === historicalSessions.length) {
      setSelectedSessions(new Set()); // Deselect all if all are selected
    } else {
      setSelectedSessions(new Set(historicalSessions.map(s => s.session_id))); // Select all
    }
  };

  // Handle single session delete
  const handleSessionDelete = async (sessionId: string) => {
    try {
      if (showConfirm && await showConfirm({
        title: 'Delete Confirmation',
        message: 'Are you sure you want to delete this item? This action cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        type: 'danger'
      })) {
        await deleteHistoricalSession(sessionId);
        showToast?.('Item deleted successfully');
      }
    } catch (err) {
      showErrorToast?.('Delete failed. Please try again.');
    }
  };

  // Handle bulk delete
  const handleBulkDelete = async () => {
    if (selectedSessions.size === 0) return;
    
    const selectedCount = selectedSessions.size;
    
    try {
      if (showConfirm && await showConfirm({
        title: 'Bulk Delete Confirmation',
        message: `Are you sure you want to delete ${selectedCount} selected items? This action cannot be undone.`,
        confirmText: 'Delete',
        cancelText: 'Cancel',
        type: 'danger'
      })) {
        await deleteHistoricalSessions(Array.from(selectedSessions));
        setSelectedSessions(new Set());
        setIsSelectMode(false);
        showToast?.(`Successfully deleted ${selectedCount} items`);
      }
    } catch (err) {
      showErrorToast?.('Bulk delete failed. Please try again.');
    }
  };

  // Determine what to show based on initialization and data state
  const shouldShowLoader = isInitializing || !hasCheckedDatabase;
  const shouldShowGallery = hasCheckedDatabase && historicalSessions.length > 0;
  const shouldShowUpload = hasCheckedDatabase && historicalSessions.length === 0;

  return (
    <div className="container mx-auto px-4 py-6">
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

      {shouldShowLoader ? (
        /* Universal Loading State */
        <UniversalLoader />
      ) : shouldShowGallery ? (
        /* Historical Sessions Gallery View */
        <div className="space-y-6 animate-scale-in">
          {/* Gallery Toolbar - matching OCR page toolbar style */}
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
            <div className="flex items-center justify-between p-3">
              {/* Left Group - File Actions */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleUploadButtonClick}
                  className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  New Image
                </button>
              </div>

              {/* Center Group - Empty space for future features */}
              <div className="flex-1"></div>

              {/* Right Group - View Controls */}
              <div className="flex items-center space-x-2">
                {/* Selection mode toggle */}
                <button
                  onClick={handleToggleSelectMode}
                  className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md border transition-colors ${
                    isSelectMode 
                      ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700' 
                      : 'text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  title={isSelectMode ? 'Exit Selection Mode' : 'Enter Selection Mode'}
                >
                  {isSelectMode ? (
                    <>
                      <X className="w-4 h-4 mr-2" />
                      Cancel
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Select
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Bulk action bar - shown when in selection mode */}
          {isSelectMode && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {selectedSessions.size} items selected
                  </span>
                  <button
                    onClick={handleSelectAll}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                  >
                    {selectedSessions.size === historicalSessions.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleBulkDelete}
                    disabled={selectedSessions.size === 0}
                    className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-red-100 border border-red-300 rounded-md hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Selected
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Historical Sessions Gallery */}
          <SessionGallery 
            sessions={historicalSessions}
            loading={historicalSessionsLoading}
            error={historicalSessionsError}
            hasNextPage={pagination.hasNextPage}
            isLoadingMore={pagination.isLoadingMore}
            onSessionSelect={handleSessionSelect}
            onLoadMore={loadMoreHistoricalSessions}
            onRefresh={loadHistoricalSessions}
            onSessionDelete={handleSessionDelete}
            isSelectable={isSelectMode}
            selectedSessions={selectedSessions}
            onToggleSelect={handleToggleSessionSelect}
            className="max-w-7xl mx-auto"
          />
        </div>
      ) : shouldShowUpload ? (
        /* Default Upload State - No Historical Sessions */
        <div className="flex flex-col items-center justify-center min-h-[600px] space-y-8 animate-slide-up">
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
            onUploadComplete={(session) => {
              setShouldAutoTriggerUpload(false);
              // Navigate to editor page
              navigate(`/editor/${session.id}`);
              // Refresh historical sessions after upload completes
              loadHistoricalSessions().catch(console.error);
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
      ) : null}

      {/* Fullscreen Upload Overlay for Gallery upload */}
      <FullscreenUploadOverlay
        isVisible={isGalleryUploading || !!galleryUploadProgress}
        uploadProgress={galleryUploadProgress}
        isUploading={isGalleryUploading}
        onClose={() => {
          setGalleryUploadProgress(null);
          setIsGalleryUploading(false);
        }}
      />
    </div>
  );
};