import React from 'react';
import { clsx } from 'clsx';

export interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  indicatorClassName?: string;
  size?: 'sm' | 'default' | 'lg';
  variant?: 'default' | 'gradient' | 'success' | 'warning' | 'danger';
  showValue?: boolean;
  animated?: boolean;
}

const sizeStyles = {
  sm: 'h-2',
  default: 'h-3',
  lg: 'h-4',
};

const variantStyles = {
  default: 'bg-primary',
  gradient: 'bg-gradient-to-r from-blue-500 to-purple-600',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  danger: 'bg-red-500',
};

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  className,
  indicatorClassName,
  size = 'default',
  variant = 'default',
  showValue = false,
  animated = false,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      <div
        className={clsx(
          'relative w-full overflow-hidden rounded-full bg-secondary',
          sizeStyles[size]
        )}
      >
        <div
          className={clsx(
            'h-full transition-all duration-500 ease-in-out',
            variantStyles[variant],
            animated && 'animate-pulse',
            indicatorClassName
          )}
          style={{ width: `${percentage}%` }}
        />
        {animated && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
        )}
      </div>
      {showValue && (
        <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
};