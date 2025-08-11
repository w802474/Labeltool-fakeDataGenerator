import React from 'react';
import { Upload, CheckCircle2, Loader2 } from 'lucide-react';
import { UploadProgress } from '@/types';
import { Progress } from '@/components/ui/Progress';

export interface FullscreenUploadOverlayProps {
  isVisible: boolean;
  uploadProgress: UploadProgress | null;
  isUploading: boolean;
  onClose?: () => void;
}

export const FullscreenUploadOverlay: React.FC<FullscreenUploadOverlayProps> = ({
  isVisible,
  uploadProgress,
  isUploading,
  onClose,
}) => {
  if (!isVisible) return null;

  const getUploadIcon = () => {
    if (isUploading) {
      return <Loader2 className="h-12 w-12 text-blue-500 animate-spin" />;
    }
    return <Upload className="h-12 w-12 text-gray-400" />;
  };

  const getUploadText = () => {
    if (uploadProgress) {
      return uploadProgress.message;
    }
    if (isUploading) {
      return 'Uploading...';
    }
    return 'Processing your image...';
  };

  const getUploadSubtext = () => {
    if (isUploading) {
      return 'Please wait while we process your image';
    }
    return 'This may take a few moments';
  };

  const getProgressVariant = () => {
    switch (uploadProgress?.stage) {
      case 'uploading':
        return 'default';
      case 'processing':
        return 'gradient';
      case 'detecting':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Black semi-transparent backdrop - no click to close during upload */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
      />
      
      {/* Upload progress content */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-12 text-center max-w-2xl mx-4 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col items-center space-y-4">
          {getUploadIcon()}
          
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {getUploadText()}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {getUploadSubtext()}
            </p>
          </div>

          {uploadProgress && (
            <div className="w-full max-w-xs space-y-2">
              <Progress
                value={uploadProgress.progress}
                variant={getProgressVariant()}
                animated={true}
                showValue
                className="w-full"
              />
              <div className="text-xs text-center text-gray-500 dark:text-gray-400">
                {uploadProgress.stage === 'uploading' && `${uploadProgress.progress}% uploaded`}
                {uploadProgress.stage === 'processing' && 'Processing image...'}
                {uploadProgress.stage === 'detecting' && 'Analyzing text regions...'}
              </div>
            </div>
          )}
          
          {/* Animated background pulse */}
          {isUploading && (
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 rounded-lg animate-pulse" />
          )}
        </div>
      </div>
    </div>
  );
};