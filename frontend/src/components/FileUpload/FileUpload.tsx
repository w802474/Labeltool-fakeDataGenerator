import React, { useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { Upload, Image, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useFileUpload } from '@/hooks/useFileUpload';
import { Progress } from '@/components/ui/Progress';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatFileSize } from '@/utils';

export interface FileUploadProps {
  className?: string;
  onUploadComplete?: () => void;
  autoTrigger?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  className,
  onUploadComplete,
  autoTrigger = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    isUploading,
    uploadProgress,
    resetUpload,
  } = useFileUpload();

  // Auto-trigger file selection when autoTrigger is true
  useEffect(() => {
    if (autoTrigger && !isUploading && !uploadProgress) {
      const timer = setTimeout(() => {
        inputRef.current?.click();
        // Call onUploadComplete to reset the trigger
        onUploadComplete?.();
      }, 100); // Small delay to ensure component is mounted
      
      return () => clearTimeout(timer);
    }
  }, [autoTrigger, isUploading, uploadProgress, onUploadComplete]);

  const getUploadIcon = () => {
    if (isUploading) {
      return <Loader2 className="h-12 w-12 text-blue-500 animate-spin" />;
    }
    if (isDragReject) {
      return <AlertCircle className="h-12 w-12 text-red-500" />;
    }
    if (uploadProgress?.stage === 'complete') {
      return <CheckCircle2 className="h-12 w-12 text-green-500" />;
    }
    return <Upload className="h-12 w-12 text-gray-400" />;
  };

  const getUploadText = () => {
    if (uploadProgress) {
      return uploadProgress.message;
    }
    if (isDragActive) {
      if (isDragReject) {
        return 'Invalid file type';
      }
      if (isDragAccept) {
        return 'Drop the image here';
      }
    }
    if (isUploading) {
      return 'Uploading...';
    }
    return 'Drop an image here, or click to select';
  };

  const getUploadSubtext = () => {
    if (uploadProgress?.stage === 'complete') {
      return 'Ready to detect text regions!';
    }
    if (isDragReject) {
      return 'Please upload a JPEG, PNG, or WebP image';
    }
    if (isUploading) {
      return 'Please wait while we process your image';
    }
    return 'Supports JPEG, PNG, WebP up to 10MB';
  };

  const getProgressVariant = () => {
    switch (uploadProgress?.stage) {
      case 'uploading':
        return 'default';
      case 'processing':
        return 'gradient';
      case 'detecting':
        return 'warning';
      case 'complete':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Card className={clsx('w-full max-w-2xl mx-auto', className)}>
      <CardContent className="p-0">
        <div
          {...getRootProps()}
          className={clsx(
            'relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200',
            {
              'border-blue-300 bg-blue-50 dark:bg-blue-900': isDragAccept,
              'border-red-300 bg-red-50 dark:bg-red-900': isDragReject,
              'border-gray-300 hover:border-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800': 
                !isDragActive && !isUploading,
              'border-blue-500 bg-blue-50 dark:bg-blue-900': isUploading,
              'cursor-not-allowed': isUploading,
            }
          )}
        >
          <input {...getInputProps()} ref={inputRef} />
          
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
                  animated={uploadProgress.stage !== 'complete'}
                  showValue
                  className="w-full"
                />
                <div className="text-xs text-center text-gray-500 dark:text-gray-400">
                  {uploadProgress.stage === 'uploading' && `${uploadProgress.progress}% uploaded`}
                  {uploadProgress.stage === 'processing' && 'Processing image...'}
                  {uploadProgress.stage === 'detecting' && 'Analyzing text regions...'}
                  {uploadProgress.stage === 'complete' && 'Upload complete!'}
                </div>
              </div>
            )}

            {!isUploading && !uploadProgress && (
              <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center space-x-1">
                  <Image className="h-4 w-4" />
                  <span>JPEG, PNG, WebP</span>
                </div>
                <div className="h-4 border-l border-gray-300 dark:border-gray-600" />
                <span>Max {formatFileSize(10 * 1024 * 1024)}</span>
              </div>
            )}

            {!isDragActive && !isUploading && !uploadProgress && (
              <Button
                variant="gradient"
                size="lg"
                className="mt-4 relative z-10"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
              >
                <Upload className="mr-2 h-4 w-4" />
                Choose Image
              </Button>
            )}
          </div>

          {/* Animated background for drag states */}
          {isDragActive && (
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg animate-pulse" />
          )}
        </div>

        {uploadProgress?.stage === 'complete' && (
          <div className="p-4 border-t bg-green-50 dark:bg-green-900">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-green-700 dark:text-green-400">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-medium">Upload successful!</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  resetUpload();
                  onUploadComplete?.();
                }}
              >
                Upload Another
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};