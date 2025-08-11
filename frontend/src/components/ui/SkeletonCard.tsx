import React from 'react';

interface SkeletonCardProps {
  className?: string;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({ className = '' }) => {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm h-full ${className}`}>
      {/* Image placeholder with standard ratio */}
      <div className="bg-gray-200 dark:bg-gray-700 shimmer relative" style={{ aspectRatio: '4/3' }}>
        {/* Status badge placeholder */}
        <div className="absolute top-1 right-1">
          <div className="h-4 w-12 bg-gray-300 dark:bg-gray-600 rounded shimmer"></div>
        </div>
      </div>
      
      {/* Content */}
      <div className="p-2 space-y-1">
        {/* Title placeholder */}
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded shimmer"></div>
        
        {/* Date and regions row */}
        <div className="flex items-center justify-between">
          {/* Date placeholder */}
          <div className="h-2.5 w-16 bg-gray-200 dark:bg-gray-700 rounded shimmer"></div>
          
          {/* Regions placeholder */}
          <div className="h-2.5 w-6 bg-gray-200 dark:bg-gray-700 rounded shimmer"></div>
        </div>
        
        {/* Dimensions placeholder */}
        <div className="h-2.5 w-20 bg-gray-200 dark:bg-gray-700 rounded shimmer"></div>
      </div>
    </div>
  );
};

