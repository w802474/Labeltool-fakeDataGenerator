/**
 * WebSocket client for real-time progress monitoring
 */

export interface ProgressUpdate {
  type: 'progress_update';
  task_id: string;
  session_id: string;
  status: string;
  stage: string;
  progress: number;
  message: string;
  timestamp: string;
  error_message?: string;
  result?: any;
}

export interface TaskCompleted {
  type: 'task_completed';
  task_id: string;
  session_id: string;
  result: {
    processed_image_path: string;
    processing_time: number;
    regions_processed: number;
  };
  timestamp: string;
}

export interface TaskFailed {
  type: 'task_failed';
  task_id: string;
  session_id: string;
  error_message: string;
  timestamp: string;
}

export interface TaskCancelled {
  type: 'task_cancelled';
  task_id: string;
  session_id: string;
  timestamp: string;
}

export interface ConnectionEstablished {
  type: 'connection_established';
  connection_id: string;
  task_id?: string;
  timestamp: string;
}

export interface ErrorMessage {
  type: 'error';
  error: string;
  timestamp: number;
}

export type WebSocketMessage = 
  | ProgressUpdate 
  | TaskCompleted 
  | TaskFailed 
  | TaskCancelled 
  | ConnectionEstablished 
  | ErrorMessage;

export interface WebSocketClientOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
  debug?: boolean;
}

export type WebSocketEventCallback = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private url: string;
  private options: Required<WebSocketClientOptions>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingTimer: NodeJS.Timeout | null = null;
  private isManualClose = false;
  private eventListeners: Map<string, Set<WebSocketEventCallback>> = new Map();
  private isConnecting = false;

  constructor(url: string, options: WebSocketClientOptions = {}) {
    this.url = url;
    this.options = {
      reconnectInterval: options.reconnectInterval ?? 3000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 10,
      pingInterval: options.pingInterval ?? 30000,
      debug: options.debug ?? false
    };

    this.log('WebSocket client initialized', { url, options: this.options });
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<boolean> {
    if (this.isConnecting) {
      this.log('Connection already in progress');
      return false;
    }

    if (this.isConnected()) {
      this.log('Already connected');
      return true;
    }

    this.isConnecting = true;
    this.isManualClose = false;

    try {
      this.log('Connecting to WebSocket server...');
      
      // Create WebSocket connection
      this.socket = new WebSocket(this.url);

      // Set up event handlers
      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);

      // Wait for connection to establish
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          this.log('Connection timeout');
          this.isConnecting = false;
          resolve(false);
        }, 10000);

        const onOpen = () => {
          clearTimeout(timeout);
          this.isConnecting = false;
          resolve(true);
        };

        const onError = () => {
          clearTimeout(timeout);
          this.isConnecting = false;
          resolve(false);
        };

        this.socket!.addEventListener('open', onOpen, { once: true });
        this.socket!.addEventListener('error', onError, { once: true });
      });

    } catch (error) {
      this.log('Failed to create WebSocket connection', error);
      this.isConnecting = false;
      return false;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.log('Disconnecting WebSocket client');
    
    this.isManualClose = true;
    this.clearTimers();
    
    if (this.socket) {
      this.socket.close(1000, 'Manual disconnect');
      this.socket = null;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Send message to server
   */
  send(message: any): boolean {
    if (!this.isConnected()) {
      this.log('Cannot send message: not connected');
      return false;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket!.send(messageStr);
      this.log('Message sent', message);
      return true;
    } catch (error) {
      this.log('Failed to send message', error);
      return false;
    }
  }

  /**
   * Subscribe to task progress updates
   */
  subscribeToTask(taskId: string): boolean {
    return this.send({
      type: 'subscribe_task',
      task_id: taskId
    });
  }

  /**
   * Unsubscribe from task progress updates
   */
  unsubscribeFromTask(taskId: string): boolean {
    return this.send({
      type: 'unsubscribe_task',
      task_id: taskId
    });
  }

  /**
   * Request task status
   */
  getTaskStatus(taskId: string): boolean {
    return this.send({
      type: 'get_task_status',
      task_id: taskId
    });
  }

  /**
   * Cancel task
   */
  cancelTask(taskId: string): boolean {
    return this.send({
      type: 'cancel_task',
      task_id: taskId
    });
  }

  /**
   * Add event listener
   */
  addEventListener(event: string, callback: WebSocketEventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);
  }

  /**
   * Remove event listener
   */
  removeEventListener(event: string, callback: WebSocketEventCallback): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.eventListeners.delete(event);
      }
    }
  }

  /**
   * Remove all event listeners
   */
  removeAllEventListeners(): void {
    this.eventListeners.clear();
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(event: Event): void {
    this.log('WebSocket connected');
    this.reconnectAttempts = 0;
    this.startPingTimer();
    this.emit('connected', { type: 'connected' } as any);
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.log('Message received', message);
      
      // Emit specific event type
      this.emit(message.type, message);
      
      // Emit general message event
      this.emit('message', message);
      
    } catch (error) {
      this.log('Failed to parse WebSocket message', error);
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    this.log('WebSocket closed', { code: event.code, reason: event.reason });
    
    this.clearTimers();
    this.socket = null;
    
    this.emit('disconnected', { type: 'disconnected', code: event.code, reason: event.reason } as any);
    
    // Attempt reconnection if not manual close
    if (!this.isManualClose && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.log('Max reconnection attempts reached');
      this.emit('reconnect_failed', { type: 'reconnect_failed' } as any);
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    this.log('WebSocket error', event);
    this.emit('error', { type: 'error', error: 'WebSocket connection error' } as any);
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.options.reconnectInterval * this.reconnectAttempts, 30000);
    
    this.log(`Scheduling reconnection attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(async () => {
      this.log(`Reconnection attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts}`);
      const connected = await this.connect();
      
      if (connected) {
        this.log('Reconnection successful');
        this.emit('reconnected', { type: 'reconnected' } as any);
      }
    }, delay);
  }

  /**
   * Start ping timer
   */
  private startPingTimer(): void {
    this.clearPingTimer();
    
    this.pingTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'ping',
          timestamp: Date.now()
        });
      }
    }, this.options.pingInterval);
  }

  /**
   * Clear timers
   */
  private clearTimers(): void {
    this.clearReconnectTimer();
    this.clearPingTimer();
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private clearPingTimer(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  /**
   * Emit event to listeners
   */
  private emit(event: string, message: WebSocketMessage): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(message);
        } catch (error) {
          this.log('Error in event listener', error);
        }
      });
    }
  }

  /**
   * Log debug message
   */
  private log(message: string, data?: any): void {
    if (this.options.debug) {
      console.log(`[WebSocketClient] ${message}`, data || '');
    }
  }
}

/**
 * Create WebSocket client for task progress monitoring
 */
export function createProgressWebSocketClient(taskId?: string): WebSocketClient {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const baseUrl = `${protocol}//${host}/api/v1/ws/progress`;
  const url = taskId ? `${baseUrl}/${taskId}` : baseUrl;

  return new WebSocketClient(url, {
    debug: import.meta.env.DEV,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    pingInterval: 30000
  });
}