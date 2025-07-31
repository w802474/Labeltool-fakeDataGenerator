import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './Button';
import { clsx } from 'clsx';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
  className?: string;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning',
  className
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return {
          iconColor: 'text-red-500',
          titleColor: 'text-red-900 dark:text-red-100',
          confirmVariant: 'destructive' as const
        };
      case 'warning':
        return {
          iconColor: 'text-yellow-500',
          titleColor: 'text-yellow-900 dark:text-yellow-100',
          confirmVariant: 'gradient' as const
        };
      case 'info':
        return {
          iconColor: 'text-blue-500',
          titleColor: 'text-blue-900 dark:text-blue-100',
          confirmVariant: 'default' as const
        };
      default:
        return {
          iconColor: 'text-yellow-500',
          titleColor: 'text-yellow-900 dark:text-yellow-100',
          confirmVariant: 'gradient' as const
        };
    }
  };

  const styles = getTypeStyles();

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className={clsx(
          'bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700',
          'w-full max-w-md mx-auto transform transition-all',
          'animate-in fade-in-0 zoom-in-95 duration-200',
          className
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 pb-4">
            <div className="flex items-center space-x-3">
              <div className={clsx(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                type === 'danger' ? 'bg-red-100 dark:bg-red-900/20' :
                type === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/20' :
                'bg-blue-100 dark:bg-blue-900/20'
              )}>
                <AlertTriangle className={clsx('h-5 w-5', styles.iconColor)} />
              </div>
              <h3 className={clsx(
                'text-lg font-semibold',
                styles.titleColor
              )}>
                {title}
              </h3>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 pb-4">
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {message}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 p-6 pt-4 bg-gray-50 dark:bg-gray-700/50 rounded-b-lg">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              {cancelText}
            </Button>
            <Button
              variant={styles.confirmVariant}
              size="sm"
              onClick={handleConfirm}
            >
              {confirmText}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};