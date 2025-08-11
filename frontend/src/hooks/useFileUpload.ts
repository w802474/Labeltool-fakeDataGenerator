import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAppStore } from '@/stores/useAppStore';
import { apiService } from '@/services/api';
import { UploadProgress } from '@/types';

export interface UseFileUploadReturn {
  // Dropzone props
  getRootProps: () => any;
  getInputProps: () => any;
  isDragActive: boolean;
  isDragAccept: boolean;
  isDragReject: boolean;
  
  // Upload state
  isUploading: boolean;
  uploadProgress: UploadProgress | null;
  
  // Actions
  uploadFiles: (files: File[]) => Promise<void>;
  resetUpload: () => void;
}

export const useFileUpload = (onUploadComplete?: (session: any) => void): UseFileUploadReturn => {
  const { setError } = useAppStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  const uploadFiles = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    
    const file = files[0]; // Only handle first file for now
    
    try {
      setIsUploading(true);
      setError(null);
      
      // Validate file
      const validation = apiService.validateImageFile(file);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // Stage 1: Uploading
      setUploadProgress({
        progress: 0,
        stage: 'uploading',
        message: 'Uploading image...',
      });

      // Create session with progress tracking
      const session = await apiService.createSessionWithProgress(file, (progress) => {
        setUploadProgress({
          progress,
          stage: 'uploading',
          message: `Uploading... ${progress}%`,
        });
      });

      // Stage 2: Processing
      setUploadProgress({
        progress: 100,
        stage: 'processing',
        message: 'Processing image...',
      });

      // Wait a bit for the backend to process
      await new Promise(resolve => setTimeout(resolve, 500));

      // Stage 3: Text detection
      setUploadProgress({
        progress: 100,
        stage: 'detecting',
        message: 'Detecting text regions...',
      });

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 300));

      // Stage 4: Complete
      setUploadProgress({
        progress: 100,
        stage: 'complete',
        message: 'Upload complete!',
      });

      // Call onUploadComplete callback if provided
      if (onUploadComplete) {
        onUploadComplete(session);
      }

      // Clear progress after a delay
      setTimeout(() => {
        setUploadProgress(null);
      }, 2000);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setError(errorMessage);
      setUploadProgress(null);
    } finally {
      setIsUploading(false);
    }
  }, [setError, onUploadComplete]);

  const resetUpload = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(null);
  }, []);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop: uploadFiles,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: isUploading,
    onDropRejected: (fileRejections) => {
      const rejection = fileRejections[0];
      if (rejection) {
        const error = rejection.errors[0];
        if (error.code === 'file-too-large') {
          setError('File is too large. Maximum size is 10MB.');
        } else if (error.code === 'file-invalid-type') {
          setError('Invalid file type. Please upload a JPEG, PNG, or WebP image.');
        } else if (error.code === 'too-many-files') {
          setError('Please upload only one file at a time.');
        } else {
          setError(error.message);
        }
      }
    },
  });

  return {
    // Dropzone props
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    
    // Upload state
    isUploading,
    uploadProgress,
    
    // Actions
    uploadFiles,
    resetUpload,
  };
};