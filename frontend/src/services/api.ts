import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  LabelSession, 
  TextRegion, 
  HealthResponse, 
  SessionResponse,
  ApiResponse 
} from '@/types';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 120000, // Increase to 2 minutes for OCR processing
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async checkHealth(): Promise<HealthResponse['data']> {
    const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
    return response.data.data;
  }

  // Session management
  async createSession(file: File): Promise<LabelSession> {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<{session_id: string, status: string, message: string}> = await this.client.post(
      '/sessions',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 minutes for file upload + OCR processing
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            console.log(`Upload progress: ${progress}%`);
          }
        },
      }
    );

    // After creating session, get the full session details
    return this.getSession(response.data.session_id);
  }

  async createSessionWithProgress(file: File, onProgress?: (progress: number) => void): Promise<LabelSession> {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<{session_id: string, status: string, message: string}> = await this.client.post(
      '/sessions',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 minutes for file upload + OCR processing
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(progress);
          }
        },
      }
    );

    // After creating session, get the full session details
    return this.getSession(response.data.session_id);
  }

  async getSession(sessionId: string): Promise<LabelSession> {
    const response: AxiosResponse<{session: LabelSession}> = await this.client.get(
      `/sessions/${sessionId}`
    );
    return response.data.session;
  }

  async updateTextRegions(
    sessionId: string, 
    regions: TextRegion[],
    mode: string = 'auto',
    exportCsv: boolean = true
  ): Promise<LabelSession> {
    const response: AxiosResponse<{session: LabelSession}> = await this.client.put(
      `/sessions/${sessionId}/regions`,
      { regions, mode, export_csv: exportCsv }
    );
    return response.data.session;
  }

  // Async text removal processing with WebSocket progress monitoring
  async processTextRemovalAsync(
    sessionId: string, 
    regions?: TextRegion[], 
    inpaintingMethod: string = 'iopaint',
    customRadius?: number
  ): Promise<{
    task_id: string;
    session_id: string;
    status: string;
    message: string;
    websocket_url: string;
    estimated_duration?: number;
  }> {
    // Generate unified task ID that will be used throughout the entire pipeline
    const taskId = crypto.randomUUID();
    
    const requestBody: any = {
      task_id: taskId,
      inpainting_method: inpaintingMethod
    };
    
    if (regions) {
      requestBody.regions = regions;
    }
    
    if (customRadius) {
      requestBody.custom_radius = customRadius;
    }

    const response = await this.client.post(
      `/sessions/${sessionId}/process-async`,
      requestBody,
      {
        timeout: 30000, // Shorter timeout for async start
      }
    );
    
    return response.data;
  }

  // Get async task status
  async getTaskStatus(taskId: string): Promise<{
    task_id: string;
    session_id: string;
    status: string;
    stage: string;
    progress: number;
    message: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    result?: any;
  }> {
    const response = await this.client.get(`/tasks/${taskId}/status`);
    return response.data;
  }

  // Cancel async task
  async cancelTask(taskId: string): Promise<{
    task_id: string;
    status: string;
    message: string;
  }> {
    const response = await this.client.post(`/tasks/${taskId}/cancel`);
    return response.data;
  }

  async downloadResult(sessionId: string): Promise<Blob> {
    const response = await this.client.get(
      `/sessions/${sessionId}/result`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  async downloadRegionsCSV(sessionId: string): Promise<Blob> {
    const response = await this.client.get(
      `/sessions/${sessionId}/export/csv`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/sessions/${sessionId}`);
  }

  async generateTextInRegions(
    sessionId: string, 
    regionsWithText: Array<{region_id: string, user_text: string}>
  ): Promise<LabelSession> {
    const response: AxiosResponse<{
      session_id: string,
      status: string,
      processed_image_url: string,
      regions_processed: number,
      message: string
    }> = await this.client.post(
      `/sessions/${sessionId}/generate-text`,
      { regions_with_text: regionsWithText },
      {
        timeout: 60000, // 1 minute timeout for text generation
      }
    );
    
    // After generating text, get the updated session details
    return this.getSession(sessionId);
  }

  async restoreSessionState(
    sessionId: string,
    processedImage: any | null,
    processedTextRegions: TextRegion[]
  ): Promise<LabelSession> {
    const response: AxiosResponse<{session: LabelSession}> = await this.client.put(
      `/sessions/${sessionId}/restore`,
      {
        processed_image: processedImage,
        processed_text_regions: processedTextRegions
      }
    );
    return response.data.session;
  }

  // Get system info
  async getSystemInfo(): Promise<any> {
    const response = await this.client.get('/system/info');
    return response.data.data;
  }

  // Utility methods

  // Error handling utilities
  private handleApiError(error: any): never {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.message || 'An error occurred';
      throw new Error(`API Error: ${message}`);
    } else if (error.request) {
      // Network error
      throw new Error('Network error: Unable to connect to server');
    } else {
      // Other error
      throw new Error(`Request error: ${error.message}`);
    }
  }

  // Download utilities
  downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // File validation
  validateImageFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please upload a JPEG, PNG, or WebP image.',
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size too large. Please upload an image smaller than 10MB.',
      };
    }

    return { valid: true };
  }
}

// Create singleton instance
export const apiService = new ApiService();
export default apiService;