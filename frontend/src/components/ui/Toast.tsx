import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';
import { clsx } from 'clsx';

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info';
  duration?: number;
  onClose: () => void;
  index?: number; // Used to calculate vertical position
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'success',
  duration = 3000,
  onClose,
  index = 0
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isEntering, setIsEntering] = useState(true);

  // Trigger enter animation when component mounts
  useEffect(() => {
    const enterTimer = setTimeout(() => {
      setIsVisible(true);
      setIsEntering(false);
    }, 50); // Short delay before showing to create enter effect

    return () => clearTimeout(enterTimer);
  }, []);

  // Auto-close timer
  useEffect(() => {
    if (!isVisible) return;
    
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 400); // Wait for exit animation to complete
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose, isVisible]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <CheckCircle2 className="h-5 w-5 text-blue-500" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-200';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-200';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-200';
    }
  };

  // Calculate vertical position: each Toast is ~64px height with 12px spacing
  const topOffset = 16 + index * (64 + 12); // 16px initial offset + (Toast height + spacing) * index

  return (
    <div 
      className={clsx(
        'fixed right-4 z-50 flex items-center space-x-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] max-w-[400px]',
        'transition-all duration-400 ease-out transform',
        // Enter animation: slide in from right
        isEntering && 'translate-x-full opacity-0',
        // Visible state: fully visible with correct position
        isVisible && !isEntering && 'translate-x-0 opacity-100',
        // Exit animation: fade out and slide right with scale
        !isVisible && 'translate-x-4 opacity-0 scale-95',
        getStyles()
      )}
      style={{ 
        top: `${topOffset}px`,
        // Add more shadow and border effects, similar to macOS notifications
        boxShadow: '0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.05)'
      }}
    >
      {getIcon()}
      <span className="font-medium flex-1 text-sm leading-5">{message}</span>
      <button
        onClick={() => {
          setIsVisible(false);
          setTimeout(onClose, 400);
        }}
        className="ml-2 hover:opacity-70 transition-opacity flex-shrink-0 p-1 rounded-full hover:bg-black/5"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};