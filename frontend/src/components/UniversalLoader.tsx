import React from 'react';

interface UniversalLoaderProps {
  className?: string;
}

export const UniversalLoader: React.FC<UniversalLoaderProps> = ({ className = '' }) => {
  return (
    <div className={`relative bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 ${className}`}>
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-20 dark:opacity-10">
        <div className="absolute inset-0 bg-grid-pattern bg-[length:32px_32px]"></div>
      </div>
      
      {/* Main Content */}
      <div className="relative flex items-center justify-center py-32">
        <div className="text-center">
          {/* Modern Multi-Ring Spinner */}
          <div className="relative w-24 h-24 mx-auto">
            {/* Outer ring - slow rotation */}
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500/60 border-r-blue-500/40 animate-spin" style={{ animationDuration: '2s' }}></div>
            
            {/* Middle ring - medium rotation */}
            <div className="absolute inset-2 rounded-full border-3 border-transparent border-t-indigo-500/70 border-b-indigo-500/50" style={{ animation: 'spin 1.5s linear infinite reverse' }}></div>
            
            {/* Inner ring - fast rotation */}
            <div className="absolute inset-4 rounded-full border-2 border-transparent border-t-purple-500/80 border-l-purple-500/60 animate-spin" style={{ animationDuration: '1s' }}></div>
            
            {/* Center glow dot */}
            <div className="absolute inset-6 rounded-full bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 shadow-xl flex items-center justify-center animate-pulse">
              <div className="w-2 h-2 bg-white/90 rounded-full shadow-lg animate-ping"></div>
            </div>
          </div>

          {/* Loading text */}
          <div className="mt-8">
            <h2 className="text-xl font-medium text-gray-800 dark:text-gray-200">
              LabelTool
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 animate-pulse">
              Loading workspace...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};