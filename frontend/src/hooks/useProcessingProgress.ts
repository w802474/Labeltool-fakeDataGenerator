/**
 * Hook for bridging WebSocket progress data with LaserScanAnimation
 */
import { useEffect, useRef } from 'react';
import { useWebSocketProgress } from './useWebSocketProgress';
import { useAppStore } from '@/stores/useAppStore';
import { apiService } from '@/services/api';

export interface ProcessingProgressData {
  isActive: boolean;
  progress: number;
  stage: 'preparing' | 'connecting' | 'masking' | 'inpainting' | 'finalizing' | 'starting' | 'processing';
  message: string;
}

interface UseProcessingProgressOptions {
  taskId: string | null;
  onComplete?: (result: any) => void;
  onCancel?: () => void;
  onError?: (error: string) => void;
}

export function useProcessingProgress({
  taskId,
  onComplete,
  onCancel,
  onError
}: UseProcessingProgressOptions): ProcessingProgressData {
  const {
    progress,
    connect,
    disconnect,
    subscribeToTask,
    unsubscribeFromTask,
    cancelTask,
    reset
  } = useWebSocketProgress({
    autoConnect: true,
    debug: import.meta.env.DEV,
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
    if (taskId && !progress.isConnected && !progress.isConnecting) {
      connect();
    }
  }, [taskId, progress.isConnected, progress.isConnecting, connect]);

  // Map WebSocket stage to LaserScanAnimation stage
  const mapStage = (wsStage: string): ProcessingProgressData['stage'] => {
    switch (wsStage) {
      case 'preparing':
      case 'connecting':
        return 'preparing';
      case 'masking':
        return 'masking';
      case 'inpainting':
      case 'processing':
        return 'inpainting';
      case 'finalizing':
        return 'finalizing';
      default:
        return 'processing';
    }
  };

  return {
    isActive: !!taskId && progress.isConnected && !progress.isCompleted && !progress.isFailed && !progress.isCancelled,
    progress: Math.max(0, Math.min(100, progress.progress || 0)),
    stage: mapStage(progress.stage),
    message: progress.message || 'Processing...'
  };
}