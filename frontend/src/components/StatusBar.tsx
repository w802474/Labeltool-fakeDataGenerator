import React from 'react';
import { useAppStore } from '@/stores/useAppStore';
import { Loader2, CheckCircle2, AlertCircle, Zap } from 'lucide-react';

export const StatusBar: React.FC = () => {
  const { currentSession, isLoading, canvasState, getCurrentDisplayRegions } = useAppStore();

  const getStatusInfo = () => {
    if (!currentSession) {
      return {
        status: 'No session',
        icon: <Zap className="h-4 w-4 text-gray-400" />,
        color: 'text-gray-500',
      };
    }

    switch (currentSession.status.toLowerCase()) {
      case 'uploaded':
        return {
          status: 'Image uploaded',
          icon: <CheckCircle2 className="h-4 w-4 text-blue-500" />,
          color: 'text-blue-600',
        };
      case 'detecting':
        return {
          status: 'Detecting text regions...',
          icon: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
          color: 'text-blue-600',
        };
      case 'detected':
        return {
          status: 'Text regions detected',
          icon: <CheckCircle2 className="h-4 w-4 text-green-500" />,
          color: 'text-green-600',
        };
      case 'editing':
        return {
          status: 'Editing regions',
          icon: <CheckCircle2 className="h-4 w-4 text-blue-500" />,
          color: 'text-blue-600',
        };
      case 'processing':
        return {
          status: 'Processing text removal...',
          icon: <Loader2 className="h-4 w-4 text-orange-500 animate-spin" />,
          color: 'text-orange-600',
        };
      case 'completed':
        return {
          status: 'Processing complete',
          icon: <CheckCircle2 className="h-4 w-4 text-green-500" />,
          color: 'text-green-600',
        };
      case 'error':
        return {
          status: 'Processing failed',
          icon: <AlertCircle className="h-4 w-4 text-red-500" />,
          color: 'text-red-600',
        };
      default:
        return {
          status: 'Unknown status',
          icon: <AlertCircle className="h-4 w-4 text-gray-400" />,
          color: 'text-gray-500',
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <footer className="border-t bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-between text-sm">
          {/* Status */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              {statusInfo.icon}
              <span className={`font-medium ${statusInfo.color}`}>
                {statusInfo.status}
              </span>
              {isLoading && (
                <Loader2 className="h-3 w-3 text-blue-500 animate-spin ml-1" />
              )}
            </div>

            {currentSession && (
              <>
                <div className="text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Regions:</span>{' '}
                  {getCurrentDisplayRegions().length}
                </div>
                
                <div className="text-gray-600 dark:text-gray-400">
                  <span className="font-medium">File:</span>{' '}
                  {currentSession.original_image.filename}
                </div>
              </>
            )}
          </div>

          {/* Canvas Info */}
          <div className="flex items-center space-x-6 text-gray-600 dark:text-gray-400">
            {currentSession && (
              <>
                <div>
                  <span className="font-medium">Zoom:</span>{' '}
                  {Math.round(canvasState.scale * 100)}%
                </div>
                
                <div>
                  <span className="font-medium">Size:</span>{' '}
                  {currentSession.original_image.dimensions.width} × {currentSession.original_image.dimensions.height}
                </div>
              </>
            )}

            <div className="text-xs text-gray-500 dark:text-gray-500">
              LabelTool v1.0.0
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};