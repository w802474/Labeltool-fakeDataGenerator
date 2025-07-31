import { useRef, useCallback } from 'react';

export const useFileUploadTrigger = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const triggerFileSelect = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Simple file handler that just triggers native file dialog
  const handleFileChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    // Reset the input value so the same file can be selected again
    event.target.value = '';
  }, []);

  return {
    triggerFileSelect,
    fileInputRef,
    handleFileChange,
  };
};