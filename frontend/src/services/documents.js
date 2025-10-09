/**
 * Documents Service
 * Handles document-related operations including CRUD, upload, download, and search
 */

import { apiService } from './api';

class DocumentsService {
  constructor() {
    this.endpoints = apiService.endpoints.DOCUMENTS;
  }

  /**
   * Get documents list with pagination and filters
   */
  async getDocuments(params = {}) {
    try {
      const response = await apiService.get(this.endpoints.LIST, params);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch documents');
    }
  }

  /**
   * Get single document by ID
   */
  async getDocument(id) {
    try {
      const response = await apiService.get(this.endpoints.GET(id));
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document');
    }
  }

  /**
   * Create new document
   */
  async createDocument(documentData) {
    try {
      const response = await apiService.post(this.endpoints.CREATE, documentData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to create document');
    }
  }

  /**
   * Update document
   */
  async updateDocument(id, documentData) {
    try {
      const response = await apiService.put(this.endpoints.UPDATE(id), documentData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to update document');
    }
  }

  /**
   * Delete document
   */
  async deleteDocument(id) {
    try {
      const response = await apiService.delete(this.endpoints.DELETE(id));
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to delete document');
    }
  }

  /**
   * Upload document file
   */
  async uploadDocument(file, metadata = {}, onProgress = null) {
    try {
      const formData = {
        ...metadata,
      };

      const response = await apiService.upload(
        this.endpoints.UPLOAD,
        file,
        formData,
        onProgress
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to upload document');
    }
  }

  /**
   * Upload multiple documents
   */
  async uploadMultipleDocuments(files, metadata = {}, onProgress = null) {
    try {
      const uploads = files.map((file, index) => {
        const fileMetadata = {
          ...metadata,
          file_index: index,
        };

        return this.uploadDocument(file, fileMetadata, (progress) => {
          if (onProgress) {
            onProgress(index, progress);
          }
        });
      });

      const results = await Promise.allSettled(uploads);
      
      const successful = [];
      const failed = [];

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          successful.push({
            file: files[index],
            document: result.value,
          });
        } else {
          failed.push({
            file: files[index],
            error: result.reason,
          });
        }
      });

      return {
        successful,
        failed,
        total: files.length,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to upload multiple documents');
    }
  }

  /**
   * Download document
   */
  async downloadDocument(id, onProgress = null) {
    try {
      const blob = await apiService.download(this.endpoints.DOWNLOAD(id), onProgress);
      return blob;
    } catch (error) {
      throw this.handleError(error, 'Failed to download document');
    }
  }

  /**
   * Download document as URL
   */
  async getDownloadUrl(id) {
    try {
      const response = await apiService.get(this.endpoints.DOWNLOAD(id), {
        mode: 'url',
      });
      return response.data.download_url;
    } catch (error) {
      throw this.handleError(error, 'Failed to get download URL');
    }
  }

  /**
   * Get document preview
   */
  async getDocumentPreview(id, options = {}) {
    try {
      const params = {
        width: options.width || 800,
        height: options.height || 600,
        page: options.page || 1,
        quality: options.quality || 'medium',
      };

      const response = await apiService.get(this.endpoints.PREVIEW(id), params);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get document preview');
    }
  }

  /**
   * Update document metadata
   */
  async updateDocumentMetadata(id, metadata) {
    try {
      const response = await apiService.patch(this.endpoints.METADATA(id), {
        metadata,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to update document metadata');
    }
  }

  /**
   * Get document versions
   */
  async getDocumentVersions(id) {
    try {
      const response = await apiService.get(`${this.endpoints.GET(id)}/versions`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document versions');
    }
  }

  /**
   * Restore document version
   */
  async restoreDocumentVersion(id, versionId) {
    try {
      const response = await apiService.post(
        `${this.endpoints.GET(id)}/versions/${versionId}/restore`
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to restore document version');
    }
  }

  /**
   * Archive document
   */
  async archiveDocument(id) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/archive`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to archive document');
    }
  }

  /**
   * Restore archived document
   */
  async restoreDocument(id) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/restore`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to restore document');
    }
  }

  /**
   * Get document statistics
   */
  async getDocumentStats() {
    try {
      const response = await apiService.get(`${this.endpoints.LIST}/stats`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document statistics');
    }
  }

  /**
   * Bulk operations on documents
   */
  async bulkOperation(operation, documentIds, params = {}) {
    try {
      const response = await apiService.post(`${this.endpoints.LIST}/bulk`, {
        operation,
        document_ids: documentIds,
        parameters: params,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, `Failed to perform bulk ${operation}`);
    }
  }

  /**
   * Search documents
   */
  async searchDocuments(searchParams) {
    try {
      const response = await apiService.post('/search/documents', searchParams);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to search documents');
    }
  }

  /**
   * Get recent documents
   */
  async getRecentDocuments(limit = 10) {
    try {
      const response = await apiService.get(this.endpoints.LIST, {
        sort_by: 'updated_at',
        sort_order: 'desc',
        per_page: limit,
      });
      return response.data.items;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch recent documents');
    }
  }

  /**
   * Get my documents
   */
  async getMyDocuments(params = {}) {
    try {
      const response = await apiService.get(this.endpoints.LIST, {
        ...params,
        created_by: 'me',
      });
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch my documents');
    }
  }

  /**
   * Get shared documents
   */
  async getSharedDocuments(params = {}) {
    try {
      const response = await apiService.get(`${this.endpoints.LIST}/shared`, params);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch shared documents');
    }
  }

  /**
   * Share document
   */
  async shareDocument(id, shareData) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/share`, shareData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to share document');
    }
  }

  /**
   * Get document sharing info
   */
  async getDocumentSharing(id) {
    try {
      const response = await apiService.get(`${this.endpoints.GET(id)}/sharing`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document sharing info');
    }
  }

  /**
   * Update document sharing
   */
  async updateDocumentSharing(id, shareData) {
    try {
      const response = await apiService.put(`${this.endpoints.GET(id)}/sharing`, shareData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to update document sharing');
    }
  }

  /**
   * Stop sharing document
   */
  async stopSharingDocument(id) {
    try {
      const response = await apiService.delete(`${this.endpoints.GET(id)}/sharing`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to stop sharing document');
    }
  }

  /**
   * Get document activity log
   */
  async getDocumentActivity(id, params = {}) {
    try {
      const response = await apiService.get(`${this.endpoints.GET(id)}/activity`, params);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document activity');
    }
  }

  /**
   * Get document tags
   */
  async getDocumentTags() {
    try {
      const response = await apiService.get(`${this.endpoints.LIST}/tags`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document tags');
    }
  }

  /**
   * Add tags to document
   */
  async addDocumentTags(id, tags) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/tags`, {
        tags,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to add document tags');
    }
  }

  /**
   * Remove tags from document
   */
  async removeDocumentTags(id, tags) {
    try {
      const response = await apiService.delete(`${this.endpoints.GET(id)}/tags`, {
        data: { tags },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to remove document tags');
    }
  }

  /**
   * Export documents
   */
  async exportDocuments(params) {
    try {
      const response = await apiService.post('/search/export', params);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to export documents');
    }
  }

  /**
   * Get export status
   */
  async getExportStatus(exportId) {
    try {
      const response = await apiService.get(`/search/export/${exportId}/status`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get export status');
    }
  }

  /**
   * Download export
   */
  async downloadExport(exportId) {
    try {
      const blob = await apiService.download(`/search/export/${exportId}/download`);
      return blob;
    } catch (error) {
      throw this.handleError(error, 'Failed to download export');
    }
  }

  /**
   * Validate file before upload
   */
  validateFile(file, documentType = null) {
    const errors = [];
    
    // Check file size
    const maxSize = documentType?.file_config?.max_file_size_mb || 50;
    if (file.size > maxSize * 1024 * 1024) {
      errors.push(`File size exceeds ${maxSize}MB limit`);
    }

    // Check file type
    const allowedTypes = documentType?.file_config?.allowed_file_types || [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    
    if (!allowedTypes.includes(file.type)) {
      errors.push(`File type ${file.type} is not allowed`);
    }

    // Check file name
    if (file.name.length > 255) {
      errors.push('File name is too long (max 255 characters)');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  /**
   * Generate download filename
   */
  generateDownloadFilename(document) {
    const timestamp = new Date().toISOString().slice(0, 10);
    const sanitizedTitle = document.title.replace(/[^\w\s-]/g, '').trim();
    const extension = document.file_name.split('.').pop();
    
    return `${sanitizedTitle}_${timestamp}.${extension}`;
  }

  /**
   * Handle service errors
   */
  handleError(error, message) {
    console.error(`DocumentsService Error: ${message}`, error);
    
    const enhancedError = new Error(message);
    enhancedError.originalError = error;
    enhancedError.status = error.status;
    enhancedError.code = error.code;
    
    return enhancedError;
  }
}

// Export singleton instance
export const documentsService = new DocumentsService();
export default documentsService;