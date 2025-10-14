/**
 * Core API Service
 * Handles HTTP requests with authentication, retry logic, and error handling
 */

import axios from 'axios';
import { AuthService } from './auth';

class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.version = process.env.REACT_APP_API_VERSION || 'v1';
    this.timeout = 30000; // 30 seconds
    this.maxRetries = 3;
    this.retryDelay = 1000;

    // Create axios instance
    this.client = axios.create({
      baseURL: `${this.baseURL}/api/${this.version}`,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = AuthService.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add timestamp to prevent caching
        config.headers['X-Request-Time'] = Date.now();
        
        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Handle successful responses
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await AuthService.refreshToken();
            const newToken = AuthService.getToken();
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            AuthService.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle 429 Too Many Requests - rate limiting
        if (error.response?.status === 429) {
          const retryAfter = parseInt(error.response.headers['retry-after'] || '5');
          await this.delay(retryAfter * 1000);
          return this.client(originalRequest);
        }

        // Handle network errors with retry
        if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
          return this.retryRequest(originalRequest);
        }

        // Handle server errors (5xx) with retry
        if (error.response?.status >= 500) {
          return this.retryRequest(originalRequest);
        }

        return Promise.reject(this.normalizeError(error));
      }
    );

    // API endpoints
    this.endpoints = {
      // Authentication
      AUTH: {
        LOGIN: '/auth/login',
        LOCAL_LOGIN: '/auth/local/login',
        LOGOUT: '/auth/logout',
        REFRESH: '/auth/refresh',
        MICROSOFT: '/auth/microsoft',
        MICROSOFT_CALLBACK: '/auth/microsoft/callback',
        PROFILE: '/auth/profile',
      },

      // Documents
      DOCUMENTS: {
        LIST: '/documents',
        CREATE: '/documents',
        GET: (id) => `/documents/${id}`,
        UPDATE: (id) => `/documents/${id}`,
        DELETE: (id) => `/documents/${id}`,
        UPLOAD: '/documents/upload',
        DOWNLOAD: (id) => `/documents/${id}/download`,
        PREVIEW: (id) => `/documents/${id}/preview`,
        METADATA: (id) => `/documents/${id}/metadata`,
      },

      // Document Types
      DOCUMENT_TYPES: {
        LIST: '/document-types',
        CREATE: '/document-types',
        GET: (id) => `/document-types/${id}`,
        UPDATE: (id) => `/document-types/${id}`,
        DELETE: (id) => `/document-types/${id}`,
      },

      // QR Codes
      QR_CODES: {
        LIST: '/qr-codes',
        CREATE: '/qr-codes',
        GET: (id) => `/qr-codes/${id}`,
        UPDATE: (id) => `/qr-codes/${id}`,
        DELETE: (id) => `/qr-codes/${id}`,
        GENERATE: '/qr-codes/generate',
        VALIDATE: '/qr-codes/validate',
        BULK_GENERATE: '/qr-codes/bulk-generate',
      },

      // Generator
      GENERATOR: {
        GENERATE: '/generator/generate',
        BATCH: '/generator/batch',
        STATUS: (id) => `/generator/batch/${id}/status`,
        DOWNLOAD: (id) => `/generator/batch/${id}/download`,
        TEMPLATES: '/generator/templates',
      },

      // Search
      SEARCH: {
        DOCUMENTS: '/search/documents',
        ADVANCED: '/search/advanced',
        EXPORT: '/search/export',
        SUGGESTIONS: '/search/suggestions',
      },

      // Users
      USERS: {
        LIST: '/users',
        CREATE: '/users',
        GET: (id) => `/users/${id}`,
        UPDATE: (id) => `/users/${id}`,
        DELETE: (id) => `/users/${id}`,
        PREFERENCES: '/users/preferences',
      },

      // System
      SYSTEM: {
        HEALTH: '/health',
        STATS: '/stats',
        ACTIVITY: '/activity',
        LOGS: '/logs',
      },

      // Microsoft 365
      MICROSOFT: {
        PROFILE: '/microsoft/profile',
        ONEDRIVE_UPLOAD: '/microsoft/onedrive/upload',
        ONEDRIVE_LIST: '/microsoft/onedrive/list',
        ONEDRIVE_DOWNLOAD: (id) => `/microsoft/onedrive/${id}/download`,
        SYNC_STATUS: '/microsoft/sync/status',
      },
    };
  }

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay execution
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Retry failed requests
   */
  async retryRequest(config) {
    const retryCount = config.__retryCount || 0;
    
    if (retryCount >= this.maxRetries) {
      return Promise.reject(new Error('Maximum retry attempts exceeded'));
    }

    config.__retryCount = retryCount + 1;
    
    // Exponential backoff
    const delay = this.retryDelay * Math.pow(2, retryCount);
    await this.delay(delay);
    
    return this.client(config);
  }

  /**
   * Normalize error responses
   */
  normalizeError(error) {
    const normalizedError = {
      name: 'ApiError',
      message: 'An error occurred',
      status: null,
      code: null,
      details: null,
      timestamp: new Date().toISOString(),
    };

    if (error.response) {
      // Server responded with error status
      normalizedError.status = error.response.status;
      normalizedError.message = error.response.data?.message || error.response.statusText;
      normalizedError.code = error.response.data?.code;
      normalizedError.details = error.response.data?.details;
    } else if (error.request) {
      // Network error
      normalizedError.message = 'Network error - please check your connection';
      normalizedError.code = 'NETWORK_ERROR';
    } else {
      // Other error
      normalizedError.message = error.message;
    }

    return normalizedError;
  }

  /**
   * GET request
   */
  async get(url, params = {}, config = {}) {
    try {
      const response = await this.client.get(url, { 
        params, 
        ...config 
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * POST request
   */
  async post(url, data = {}, config = {}) {
    try {
      const response = await this.client.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * PUT request
   */
  async put(url, data = {}, config = {}) {
    try {
      const response = await this.client.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * PATCH request
   */
  async patch(url, data = {}, config = {}) {
    try {
      const response = await this.client.patch(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * DELETE request
   */
  async delete(url, config = {}) {
    try {
      const response = await this.client.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Upload file with progress tracking
   */
  async upload(url, file, metadata = {}, onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add metadata
    Object.keys(metadata).forEach(key => {
      formData.append(key, metadata[key]);
    });

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    };

    try {
      const response = await this.client.post(url, formData, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Download file with progress tracking
   */
  async download(url, onProgress = null) {
    const config = {
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    };

    try {
      const response = await this.client.get(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Cancel request
   */
  createCancelToken() {
    return axios.CancelToken.source();
  }

  /**
   * Check if error is cancellation
   */
  isCancelError(error) {
    return axios.isCancel(error);
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get API status
   */
  async getStatus() {
    try {
      const response = await this.client.get('/status');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;