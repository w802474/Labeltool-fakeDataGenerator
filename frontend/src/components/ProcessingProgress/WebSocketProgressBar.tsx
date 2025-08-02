/**
 * WebSocket-powered real-time progress bar component
 */
import React, { useEffect, useState } from 'react';
import { X, Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { useWebSocketProgress } from '../../hooks/useWebSocketProgress';
import { formatDuration, formatTimeRemaining } from '../../utils/timeUtils';

interface WebSocketProgressBarProps {
  taskId: string | null;
  onComplete?: (result: any) => void;
  onCancel?: () => void;
  onError?: (error: string) => void;
  className?: string;
  showDetails?: boolean;
  allowCancel?: boolean;
  autoConnect?: boolean;
}

export const WebSocketProgressBar: React.FC<WebSocketProgressBarProps> = ({
  taskId,
  onComplete,
  onCancel,
  onError,
  className = '',
  showDetails = true,
  allowCancel = true,
  autoConnect = true
}) => {
  const [startTime] = useState<Date>(new Date());
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number | null>(null);

  const {
    progress,
    connect,
    disconnect,
    subscribeToTask,
    unsubscribeFromTask,
    cancelTask,
    reset
  } = useWebSocketProgress({
    autoConnect,
    debug: import.meta.env.DEV,
    onProgress: (update) => {
      // Calculate estimated time remaining based on progress rate
      if (update.progress > 0 && progress.startTime) {
        const elapsed = Date.now() - progress.startTime.getTime();
        const progressRate = update.progress / elapsed; // progress per ms
        const remaining = (100 - update.progress) / progressRate;
        setEstimatedTimeRemaining(remaining > 0 ? remaining : null);
      }
    },
    onCompleted: (result) => {
      onComplete?.(result);
    },
    onFailed: (error) => {
      onError?.(error.error_message);
    },
    onCancelled: () => {
      onCancel?.();
    }
  });

  // Subscribe to task when taskId changes
  useEffect(() => {
    if (taskId && progress.isConnected) {
      subscribeToTask(taskId);
    }
    
    return () => {
      if (taskId) {
        unsubscribeFromTask(taskId);
      }
    };
  }, [taskId, progress.isConnected, subscribeToTask, unsubscribeFromTask]);

  // Auto-connect if not connected
  useEffect(() => {
    if (autoConnect && !progress.isConnected && !progress.isConnecting) {
      connect();
    }
  }, [autoConnect, progress.isConnected, progress.isConnecting, connect]);

  // Handle cancel click
  const handleCancel = () => {
    if (taskId && allowCancel) {
      cancelTask(taskId);
    }
  };

  // Don't render if no task
  if (!taskId) {
    return null;
  }

  // Get progress bar color based on status
  const getProgressColor = () => {
    if (progress.isFailed) return 'bg-red-500';
    if (progress.isCompleted) return 'bg-green-500';
    if (progress.isCancelled) return 'bg-gray-500';
    return 'bg-blue-500';
  };

  // Get status icon
  const getStatusIcon = () => {
    if (progress.isFailed) {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
    if (progress.isCompleted) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    if (progress.isCancelled) {
      return <X className="w-5 h-5 text-gray-500" />;
    }
    return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
  };

  // Format stage display text
  const getStageText = (stage: string) => {
    const stageMap: Record<string, string> = {
      'preparing': 'Preparing',
      'connecting': 'Connecting',
      'masking': 'Creating Masks',
      'inpainting': 'Processing',
      'finalizing': 'Finalizing',
      'completed': 'Completed',
      'error': 'Error',
      'cancelled': 'Cancelled'
    };
    return stageMap[stage] || stage.charAt(0).toUpperCase() + stage.slice(1);
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg border p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <h3 className="font-medium text-gray-900">
            AI Processing {progress.isCompleted ? 'Complete' : 'Active'}
          </h3>
        </div>
        
        {allowCancel && !progress.isCompleted && !progress.isFailed && !progress.isCancelled && (
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="Cancel processing"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Connection Status */}
      {!progress.isConnected && (
        <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
          {progress.isConnecting ? 'Connecting...' : 'Connection lost - attempting to reconnect'}
        </div>
      )}

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{getStageText(progress.stage)}</span>
          <span>{Math.round(progress.progress)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${Math.min(progress.progress, 100)}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="text-sm text-gray-600 mb-3">
        {progress.message}
      </div>

      {/* Error Message */}
      {progress.error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <strong>Error:</strong> {progress.error}
        </div>
      )}

      {/* Details */}
      {showDetails && (
        <div className="space-y-2 text-xs text-gray-500">
          {/* Task Info */}
          <div className="flex justify-between">
            <span>Task ID:</span>
            <span className="font-mono">{taskId.slice(0, 8)}...</span>
          </div>
          
          {/* Timing Info */}
          {progress.startTime && (
            <div className="flex justify-between">
              <span>Elapsed:</span>
              <span>{formatDuration(Date.now() - progress.startTime.getTime())}</span>
            </div>
          )}
          
          {/* Estimated Time Remaining */}
          {estimatedTimeRemaining && !progress.isCompleted && !progress.isFailed && (
            <div className="flex justify-between">
              <span>Est. Remaining:</span>
              <span className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                {formatTimeRemaining(estimatedTimeRemaining)}
              </span>
            </div>
          )}
          
          {/* Completion Time */}
          {progress.duration && (progress.isCompleted || progress.isFailed) && (
            <div className="flex justify-between">
              <span>Total Time:</span>
              <span>{formatDuration(progress.duration)}</span>
            </div>
          )}
          
          {/* Connection Status */}
          <div className="flex justify-between">
            <span>Connection:</span>
            <span className={progress.isConnected ? 'text-green-600' : 'text-red-600'}>
              {progress.isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {(progress.isCompleted || progress.isFailed || progress.isCancelled) && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => {
                reset();
                disconnect();
              }}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WebSocketProgressBar;