import { useState, useCallback } from 'react';

interface ConfirmDialogOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}

export const useConfirmDialog = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmDialogOptions>({
    title: '',
    message: ''
  });
  const [resolveCallback, setResolveCallback] = useState<((value: boolean) => void) | null>(null);

  const showConfirm = useCallback((opts: ConfirmDialogOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setOptions(opts);
      setResolveCallback(() => resolve);
      setIsOpen(true);
    });
  }, []);

  const handleConfirm = useCallback(() => {
    if (resolveCallback) {
      resolveCallback(true);
      setResolveCallback(null);
    }
    setIsOpen(false);
  }, [resolveCallback]);

  const handleCancel = useCallback(() => {
    if (resolveCallback) {
      resolveCallback(false);
      setResolveCallback(null);
    }
    setIsOpen(false);
  }, [resolveCallback]);

  return {
    isOpen,
    options,
    showConfirm,
    handleConfirm,
    handleCancel
  };
};