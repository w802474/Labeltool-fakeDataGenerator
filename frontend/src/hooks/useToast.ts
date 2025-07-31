import { useState, useCallback } from 'react';

interface ToastOptions {
  message: string;
  type?: 'success' | 'error' | 'info';
  duration?: number;
}

export const useToast = () => {
  const [toasts, setToasts] = useState<Array<ToastOptions & { id: string }>>([]);

  const showToast = useCallback((options: ToastOptions) => {
    const id = Math.random().toString(36).substr(2, 9);
    const toast = { ...options, id };
    
    setToasts(prev => [...prev, toast]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const showSuccess = useCallback((message: string, duration?: number) => {
    showToast({ message, type: 'success', duration });
  }, [showToast]);

  const showError = useCallback((message: string, duration?: number) => {
    showToast({ message, type: 'error', duration });
  }, [showToast]);

  const showInfo = useCallback((message: string, duration?: number) => {
    showToast({ message, type: 'info', duration });
  }, [showToast]);

  return {
    toasts,
    showToast,
    removeToast,
    showSuccess,
    showError,
    showInfo,
  };
};