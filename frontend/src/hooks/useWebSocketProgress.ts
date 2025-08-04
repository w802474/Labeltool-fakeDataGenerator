/**
 * React hook for WebSocket progress monitoring
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { 
  WebSocketClient, 
  WebSocketMessage, 
  ProgressUpdate, 
  TaskCompleted, 
  TaskFailed, 
  createProgressWebSocketClient 
} from '../services/websocket';

export interface ProgressState {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  
  // Task state
  taskId: string | null;
  sessionId: string | null;
  status: string;
  stage: string;
  progress: number;
  message: string;
  
  // Task result
  isCompleted: boolean;
  isFailed: boolean;
  isCancelled: boolean;
  error: string | null;
  result: any | null;
  
  // Timing
  startTime: Date | null;
  endTime: Date | null;
  duration: number | null;
  
  // Update frequency tracking
  updateFrequency: number;
  lastUpdateTime: number;
  recentUpdates: number[];
}

export interface UseWebSocketProgressOptions {
  autoConnect?: boolean;
  debug?: boolean;
  onProgress?: (update: ProgressUpdate) => void;
  onCompleted?: (result: TaskCompleted) => void;
  onFailed?: (error: TaskFailed) => void;
  onCancelled?: () => void;
}

export interface UseWebSocketProgressReturn {
  // State
  progress: ProgressState;
  
  // Actions
  connect: () => Promise<boolean>;
  disconnect: () => void;
  subscribeToTask: (taskId: string) => boolean;
  unsubscribeFromTask: (taskId: string) => boolean;
  cancelTask: (taskId: string) => boolean;
  reset: () => void;
  
  // Client reference (for advanced usage)
  client: WebSocketClient | null;
}

const initialProgressState: ProgressState = {
  isConnected: false,
  isConnecting: false,
  connectionError: null,
  taskId: null,
  sessionId: null,
  status: 'idle',
  stage: 'idle',
  progress: 0,
  message: 'Ready',
  isCompleted: false,
  isFailed: false,
  isCancelled: false,
  error: null,
  result: null,
  startTime: null,
  endTime: null,
  duration: null,
  updateFrequency: 0,
  lastUpdateTime: 0,
  recentUpdates: []
};

export function useWebSocketProgress(
  options: UseWebSocketProgressOptions = {}
): UseWebSocketProgressReturn {
  const {
    autoConnect = true,
    debug = false,
    onProgress,
    onCompleted,
    onFailed,
    onCancelled
  } = options;

  const [progress, setProgress] = useState<ProgressState>(initialProgressState);
  const clientRef = useRef<WebSocketClient | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  // Calculate update frequency
  const calculateUpdateFrequency = useCallback((prevState: ProgressState): { frequency: number; recentUpdates: number[] } => {
    const now = Date.now();
    
    // Add current update time and keep only recent updates (last 2 seconds)
    const recentUpdates = [...prevState.recentUpdates, now].filter(
      time => now - time <= 2000
    );
    
    // Calculate frequency (updates per second)
    const timeSpan = recentUpdates.length > 1 
      ? (now - recentUpdates[0]) / 1000 
      : 1;
    const frequency = recentUpdates.length / Math.max(timeSpan, 0.1);
    
    return { frequency, recentUpdates };
  }, []);

  // Initialize WebSocket client
  useEffect(() => {
    if (!clientRef.current) {
      clientRef.current = createProgressWebSocketClient();
      
      // Set up event listeners
      setupEventListeners();
      
      if (autoConnect) {
        connect();
      }
    }

    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
        clientRef.current.removeAllEventListeners();
        clientRef.current = null;
      }
    };
  }, []);

  // Set up WebSocket event listeners
  const setupEventListeners = useCallback(() => {
    const client = clientRef.current;
    if (!client) return;

    // Connection events
    client.addEventListener('connected', () => {
      setProgress(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        connectionError: null
      }));
      
      if (debug) console.log('[WebSocketProgress] Connected');
    });

    client.addEventListener('disconnected', () => {
      setProgress(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false
      }));
      
      if (debug) console.log('[WebSocketProgress] Disconnected');
    });

    client.addEventListener('reconnected', () => {
      setProgress(prev => ({
        ...prev,
        isConnected: true,
        connectionError: null
      }));
      
      // Resubscribe to all tasks
      subscriptionsRef.current.forEach(taskId => {
        client.subscribeToTask(taskId);
      });
      
      if (debug) console.log('[WebSocketProgress] Reconnected');
    });

    client.addEventListener('error', (message) => {
      const errorMsg = 'error' in message ? message.error : 'Unknown WebSocket error';
      setProgress(prev => ({
        ...prev,
        connectionError: errorMsg,
        isConnecting: false
      }));
      
      if (debug) console.log('[WebSocketProgress] Error:', errorMsg);
    });

    // Progress events
    client.addEventListener('progress_update', (message) => {
      const update = message as ProgressUpdate;
      
      // Robust NaN checking and sanitization
      let safeProgress = 0;
      if (typeof update.progress === 'number' && !Number.isNaN(update.progress) && Number.isFinite(update.progress)) {
        safeProgress = Math.max(0, Math.min(100, update.progress));
      } else {
        console.warn('[WebSocketProgress] Invalid progress value received:', update.progress, typeof update.progress);
        console.warn('[WebSocketProgress] Full update message:', update);
        safeProgress = 0;
      }
      
      setProgress(prev => {
        const { frequency, recentUpdates } = calculateUpdateFrequency(prev);
        const now = Date.now();
        
        return {
          ...prev,
          taskId: update.task_id,
          sessionId: update.session_id,
          status: update.status,
          stage: update.stage,
          progress: safeProgress,
          message: update.message,
          error: update.error_message || null,
          startTime: prev.startTime || new Date(),
          updateFrequency: frequency,
          lastUpdateTime: now,
          recentUpdates: recentUpdates
        };
      });
      
      onProgress?.(update);
      
      if (debug) console.log('[WebSocketProgress] Progress update:', { ...update, sanitizedProgress: safeProgress });
    });

    // Task completion events
    client.addEventListener('task_completed', (message) => {
      const completed = message as TaskCompleted;
      
      setProgress(prev => ({
        ...prev,
        status: 'completed',
        stage: 'completed',
        progress: 100,
        message: 'Processing completed successfully',
        isCompleted: true,
        result: completed.result,
        endTime: new Date(),
        duration: prev.startTime ? Date.now() - prev.startTime.getTime() : null
      }));
      
      onCompleted?.(completed);
      
      if (debug) console.log('[WebSocketProgress] Task completed:', completed);
    });

    // Task failure events
    client.addEventListener('task_failed', (message) => {
      const failed = message as TaskFailed;
      
      setProgress(prev => ({
        ...prev,
        status: 'failed',
        stage: 'error',
        message: 'Processing failed',
        isFailed: true,
        error: failed.error_message,
        endTime: new Date(),
        duration: prev.startTime ? Date.now() - prev.startTime.getTime() : null
      }));
      
      onFailed?.(failed);
      
      if (debug) console.log('[WebSocketProgress] Task failed:', failed);
    });

    // Task cancellation events
    client.addEventListener('task_cancelled', (message) => {
      setProgress(prev => ({
        ...prev,
        status: 'cancelled',
        stage: 'cancelled',
        message: 'Processing cancelled',
        isCancelled: true,
        endTime: new Date(),
        duration: prev.startTime ? Date.now() - prev.startTime.getTime() : null
      }));
      
      onCancelled?.();
      
      if (debug) console.log('[WebSocketProgress] Task cancelled:', message);
    });

  }, [debug, onProgress, onCompleted, onFailed, onCancelled]);

  // Connect to WebSocket
  const connect = useCallback(async (): Promise<boolean> => {
    const client = clientRef.current;
    if (!client) return false;

    setProgress(prev => ({ ...prev, isConnecting: true, connectionError: null }));
    
    try {
      const connected = await client.connect();
      if (!connected) {
        setProgress(prev => ({
          ...prev,
          isConnecting: false,
          connectionError: 'Failed to connect to WebSocket server'
        }));
      }
      return connected;
    } catch (error) {
      setProgress(prev => ({
        ...prev,
        isConnecting: false,
        connectionError: error instanceof Error ? error.message : 'Connection error'
      }));
      return false;
    }
  }, []);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    const client = clientRef.current;
    if (!client) return;

    client.disconnect();
    subscriptionsRef.current.clear();
    
    setProgress(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false
    }));
  }, []);

  // Subscribe to task progress
  const subscribeToTask = useCallback((taskId: string): boolean => {
    const client = clientRef.current;
    if (!client) return false;

    const success = client.subscribeToTask(taskId);
    if (success) {
      subscriptionsRef.current.add(taskId);
      
      setProgress(prev => ({
        ...prev,
        taskId,
        status: 'pending',
        stage: 'preparing',
        progress: 0,
        message: 'Subscribing to task progress...',
        startTime: new Date()
      }));
      
      if (debug) console.log('[WebSocketProgress] Subscribed to task:', taskId);
    }
    
    return success;
  }, [debug]);

  // Unsubscribe from task progress
  const unsubscribeFromTask = useCallback((taskId: string): boolean => {
    const client = clientRef.current;
    if (!client) return false;

    const success = client.unsubscribeFromTask(taskId);
    if (success) {
      subscriptionsRef.current.delete(taskId);
      
      if (debug) console.log('[WebSocketProgress] Unsubscribed from task:', taskId);
    }
    
    return success;
  }, [debug]);

  // Cancel task
  const cancelTask = useCallback((taskId: string): boolean => {
    const client = clientRef.current;
    if (!client) return false;

    const success = client.cancelTask(taskId);
    
    if (success && debug) {
      console.log('[WebSocketProgress] Cancel requested for task:', taskId);
    }
    
    return success;
  }, [debug]);

  // Reset progress state
  const reset = useCallback(() => {
    setProgress(initialProgressState);
    subscriptionsRef.current.clear();
  }, []);

  return {
    progress,
    connect,
    disconnect,
    subscribeToTask,
    unsubscribeFromTask,
    cancelTask,
    reset,
    client: clientRef.current
  };
}