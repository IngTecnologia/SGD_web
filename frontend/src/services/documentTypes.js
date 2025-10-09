/**
 * Document Types Service
 * Handles document type configuration and management
 */

import { apiService } from './api';

class DocumentTypesService {
  constructor() {
    this.endpoints = apiService.endpoints.DOCUMENT_TYPES;
  }

  /**
   * Get all document types
   */
  async getDocumentTypes(params = {}) {
    try {
      const response = await apiService.get(this.endpoints.LIST, params);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document types');
    }
  }

  /**
   * Get single document type by ID
   */
  async getDocumentType(id) {
    try {
      const response = await apiService.get(this.endpoints.GET(id));
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document type');
    }
  }

  /**
   * Create new document type
   */
  async createDocumentType(documentTypeData) {
    try {
      const response = await apiService.post(this.endpoints.CREATE, documentTypeData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to create document type');
    }
  }

  /**
   * Update document type
   */
  async updateDocumentType(id, documentTypeData) {
    try {
      const response = await apiService.put(this.endpoints.UPDATE(id), documentTypeData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to update document type');
    }
  }

  /**
   * Delete document type
   */
  async deleteDocumentType(id) {
    try {
      const response = await apiService.delete(this.endpoints.DELETE(id));
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to delete document type');
    }
  }

  /**
   * Get active document types only
   */
  async getActiveDocumentTypes() {
    try {
      const response = await apiService.get(this.endpoints.LIST, {
        is_active: true,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch active document types');
    }
  }

  /**
   * Upload template for document type
   */
  async uploadTemplate(id, templateFile, onProgress = null) {
    try {
      const response = await apiService.upload(
        `${this.endpoints.GET(id)}/template`,
        templateFile,
        {},
        onProgress
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to upload template');
    }
  }

  /**
   * Download template for document type
   */
  async downloadTemplate(id) {
    try {
      const blob = await apiService.download(`${this.endpoints.GET(id)}/template`);
      return blob;
    } catch (error) {
      throw this.handleError(error, 'Failed to download template');
    }
  }

  /**
   * Delete template for document type
   */
  async deleteTemplate(id) {
    try {
      const response = await apiService.delete(`${this.endpoints.GET(id)}/template`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to delete template');
    }
  }

  /**
   * Test QR configuration for document type
   */
  async testQRConfiguration(id, qrConfig) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/test-qr`, {
        qr_config: qrConfig,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to test QR configuration');
    }
  }

  /**
   * Get document type statistics
   */
  async getDocumentTypeStats(id) {
    try {
      const response = await apiService.get(`${this.endpoints.GET(id)}/stats`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch document type statistics');
    }
  }

  /**
   * Clone document type
   */
  async cloneDocumentType(id, newData = {}) {
    try {
      const response = await apiService.post(`${this.endpoints.GET(id)}/clone`, newData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to clone document type');
    }
  }

  /**
   * Export document type configuration
   */
  async exportDocumentType(id) {
    try {
      const response = await apiService.get(`${this.endpoints.GET(id)}/export`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to export document type');
    }
  }

  /**
   * Import document type configuration
   */
  async importDocumentType(configFile) {
    try {
      const response = await apiService.upload(
        `${this.endpoints.LIST}/import`,
        configFile
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to import document type');
    }
  }

  /**
   * Validate document type configuration
   */
  validateDocumentType(documentTypeData) {
    const errors = [];
    const warnings = [];

    // Validate basic fields
    if (!documentTypeData.code) {
      errors.push('Document type code is required');
    } else if (!/^[A-Z0-9-_]{3,20}$/.test(documentTypeData.code)) {
      errors.push('Document type code must be 3-20 characters, uppercase letters, numbers, hyphens and underscores only');
    }

    if (!documentTypeData.name) {
      errors.push('Document type name is required');
    } else if (documentTypeData.name.length < 3 || documentTypeData.name.length > 100) {
      errors.push('Document type name must be between 3 and 100 characters');
    }

    // Validate requirements
    if (!documentTypeData.requirements) {
      errors.push('Requirements configuration is required');
    }

    // Validate file configuration
    if (!documentTypeData.file_config) {
      errors.push('File configuration is required');
    } else {
      const fileConfig = documentTypeData.file_config;
      
      if (!fileConfig.allowed_file_types || fileConfig.allowed_file_types.length === 0) {
        errors.push('At least one allowed file type must be specified');
      }

      if (!fileConfig.max_file_size_mb || fileConfig.max_file_size_mb <= 0) {
        errors.push('Maximum file size must be specified and greater than 0');
      } else if (fileConfig.max_file_size_mb > 100) {
        warnings.push('Maximum file size is very large (>100MB), consider reducing for better performance');
      }
    }

    // Validate workflow configuration
    if (!documentTypeData.workflow) {
      errors.push('Workflow configuration is required');
    } else {
      const workflow = documentTypeData.workflow;
      
      if (workflow.auto_notify_email && (!workflow.notification_emails || workflow.notification_emails.length === 0)) {
        warnings.push('Email notification is enabled but no notification emails are specified');
      }

      if (!workflow.retention_days || workflow.retention_days <= 0) {
        errors.push('Retention days must be specified and greater than 0');
      } else if (workflow.retention_days < 365) {
        warnings.push('Retention period is less than 1 year, which may be too short for business documents');
      }
    }

    // Validate QR configuration if QR is required
    if (documentTypeData.requirements?.requires_qr && documentTypeData.qr_config) {
      const qrConfig = documentTypeData.qr_config;
      
      if (!Number.isInteger(qrConfig.qr_table_number) || qrConfig.qr_table_number < 1) {
        errors.push('QR table number must be a positive integer');
      }

      if (!Number.isInteger(qrConfig.qr_row) || qrConfig.qr_row < 1) {
        errors.push('QR row must be a positive integer');
      }

      if (!Number.isInteger(qrConfig.qr_column) || qrConfig.qr_column < 0) {
        errors.push('QR column must be a non-negative integer');
      }

      if (!qrConfig.qr_width || qrConfig.qr_width <= 0) {
        errors.push('QR width must be specified and greater than 0');
      }

      if (!qrConfig.qr_height || qrConfig.qr_height <= 0) {
        errors.push('QR height must be specified and greater than 0');
      }
    } else if (documentTypeData.requirements?.requires_qr && !documentTypeData.qr_config) {
      errors.push('QR configuration is required when QR is enabled');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Get default document type configuration
   */
  getDefaultConfig() {
    return {
      code: '',
      name: '',
      description: '',
      requirements: {
        requires_qr: true,
        requires_cedula: true,
        requires_nombre: true,
        requires_telefono: false,
        requires_email: false,
        requires_direccion: false,
      },
      file_config: {
        allowed_file_types: [
          'application/pdf',
          'image/jpeg',
          'image/png',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ],
        max_file_size_mb: 10,
        allow_multiple_files: false,
      },
      workflow: {
        requires_approval: false,
        auto_notify_email: false,
        notification_emails: [],
        retention_days: 2555, // 7 years
      },
      qr_config: {
        qr_table_number: 1,
        qr_row: 1,
        qr_column: 0,
        qr_width: 2,
        qr_height: 2,
      },
      is_active: true,
    };
  }

  /**
   * Get supported file types
   */
  getSupportedFileTypes() {
    return [
      {
        type: 'application/pdf',
        extension: 'pdf',
        name: 'PDF Document',
        description: 'Portable Document Format',
      },
      {
        type: 'image/jpeg',
        extension: 'jpg',
        name: 'JPEG Image',
        description: 'Joint Photographic Experts Group',
      },
      {
        type: 'image/png',
        extension: 'png',
        name: 'PNG Image',
        description: 'Portable Network Graphics',
      },
      {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        extension: 'docx',
        name: 'Word Document',
        description: 'Microsoft Word Document',
      },
      {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        extension: 'xlsx',
        name: 'Excel Spreadsheet',
        description: 'Microsoft Excel Spreadsheet',
      },
      {
        type: 'text/plain',
        extension: 'txt',
        name: 'Text File',
        description: 'Plain Text Document',
      },
    ];
  }

  /**
   * Get QR position options
   */
  getQRPositionOptions() {
    return [
      { value: 'top-left', label: 'Top Left' },
      { value: 'top-right', label: 'Top Right' },
      { value: 'bottom-left', label: 'Bottom Left' },
      { value: 'bottom-right', label: 'Bottom Right' },
      { value: 'center', label: 'Center' },
    ];
  }

  /**
   * Generate document type code from name
   */
  generateCodeFromName(name) {
    return name
      .toUpperCase()
      .replace(/[^A-Z0-9\s]/g, '')
      .replace(/\s+/g, '-')
      .substring(0, 20);
  }

  /**
   * Handle service errors
   */
  handleError(error, message) {
    console.error(`DocumentTypesService Error: ${message}`, error);
    
    const enhancedError = new Error(message);
    enhancedError.originalError = error;
    enhancedError.status = error.status;
    enhancedError.code = error.code;
    
    return enhancedError;
  }
}

// Export singleton instance
export const documentTypesService = new DocumentTypesService();
export default documentTypesService;