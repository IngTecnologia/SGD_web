/**
 * Microsoft 365 Integration Service
 * Handles Microsoft Graph API integration, OneDrive operations, and user profile
 */

import { apiService } from './api';
import { AuthService } from './auth';

class MicrosoftService {
  constructor() {
    this.endpoints = apiService.endpoints.MICROSOFT;
    this.graphBaseUrl = 'https://graph.microsoft.com/v1.0';
  }

  /**
   * Get user's Microsoft profile
   */
  async getUserProfile() {
    try {
      const response = await apiService.get(this.endpoints.PROFILE);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch Microsoft profile');
    }
  }

  /**
   * Get user's Microsoft profile directly from Graph API
   */
  async getGraphUserProfile() {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(`${this.graphBaseUrl}/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Graph API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch Graph profile');
    }
  }

  /**
   * Upload file to OneDrive
   */
  async uploadToOneDrive(file, folder = '', onProgress = null) {
    try {
      const formData = {
        folder: folder,
        overwrite: false,
      };

      const response = await apiService.upload(
        this.endpoints.ONEDRIVE_UPLOAD,
        file,
        formData,
        onProgress
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to upload to OneDrive');
    }
  }

  /**
   * Upload file directly to OneDrive using Graph API
   */
  async uploadToOneDriveDirect(file, folder = '', onProgress = null) {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const fileName = encodeURIComponent(file.name);
      const folderPath = folder ? `/${folder}` : '';
      const uploadUrl = `${this.graphBaseUrl}/me/drive/root:${folderPath}/${fileName}:/content`;

      const response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': file.type,
        },
        body: file,
      });

      if (!response.ok) {
        throw new Error(`OneDrive upload error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Failed to upload to OneDrive directly');
    }
  }

  /**
   * List OneDrive files
   */
  async listOneDriveFiles(folder = '', params = {}) {
    try {
      const response = await apiService.get(this.endpoints.ONEDRIVE_LIST, {
        folder,
        ...params,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to list OneDrive files');
    }
  }

  /**
   * List OneDrive files directly from Graph API
   */
  async listOneDriveFilesDirect(folder = '') {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const folderPath = folder ? `/${folder}` : '';
      const listUrl = `${this.graphBaseUrl}/me/drive/root${folderPath}:/children`;

      const response = await fetch(listUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`OneDrive list error: ${response.status}`);
      }

      const data = await response.json();
      return data.value;
    } catch (error) {
      throw this.handleError(error, 'Failed to list OneDrive files directly');
    }
  }

  /**
   * Download file from OneDrive
   */
  async downloadFromOneDrive(fileId, onProgress = null) {
    try {
      const blob = await apiService.download(
        this.endpoints.ONEDRIVE_DOWNLOAD(fileId),
        onProgress
      );
      return blob;
    } catch (error) {
      throw this.handleError(error, 'Failed to download from OneDrive');
    }
  }

  /**
   * Get OneDrive file download URL
   */
  async getOneDriveDownloadUrl(fileId) {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(`${this.graphBaseUrl}/me/drive/items/${fileId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`OneDrive file info error: ${response.status}`);
      }

      const fileInfo = await response.json();
      return fileInfo['@microsoft.graph.downloadUrl'];
    } catch (error) {
      throw this.handleError(error, 'Failed to get OneDrive download URL');
    }
  }

  /**
   * Create OneDrive folder
   */
  async createOneDriveFolder(folderName, parentFolder = '') {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const parentPath = parentFolder ? `/${parentFolder}` : '';
      const createUrl = `${this.graphBaseUrl}/me/drive/root${parentPath}:/children`;

      const response = await fetch(createUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: folderName,
          folder: {},
          '@microsoft.graph.conflictBehavior': 'rename',
        }),
      });

      if (!response.ok) {
        throw new Error(`OneDrive folder creation error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Failed to create OneDrive folder');
    }
  }

  /**
   * Delete OneDrive file
   */
  async deleteOneDriveFile(fileId) {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(`${this.graphBaseUrl}/me/drive/items/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok && response.status !== 404) {
        throw new Error(`OneDrive delete error: ${response.status}`);
      }

      return true;
    } catch (error) {
      throw this.handleError(error, 'Failed to delete OneDrive file');
    }
  }

  /**
   * Get OneDrive storage quota
   */
  async getStorageQuota() {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(`${this.graphBaseUrl}/me/drive`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`OneDrive quota error: ${response.status}`);
      }

      const driveInfo = await response.json();
      return driveInfo.quota;
    } catch (error) {
      throw this.handleError(error, 'Failed to get storage quota');
    }
  }

  /**
   * Search OneDrive files
   */
  async searchOneDriveFiles(query, params = {}) {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const searchUrl = `${this.graphBaseUrl}/me/drive/root/search(q='${encodeURIComponent(query)}')`;

      const response = await fetch(searchUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`OneDrive search error: ${response.status}`);
      }

      const data = await response.json();
      return data.value;
    } catch (error) {
      throw this.handleError(error, 'Failed to search OneDrive files');
    }
  }

  /**
   * Get file sharing link
   */
  async createSharingLink(fileId, type = 'view', scope = 'organization') {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(
        `${this.graphBaseUrl}/me/drive/items/${fileId}/createLink`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: type, // view, edit, embed
            scope: scope, // anonymous, organization
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Sharing link creation error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Failed to create sharing link');
    }
  }

  /**
   * Get sync status
   */
  async getSyncStatus() {
    try {
      const response = await apiService.get(this.endpoints.SYNC_STATUS);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get sync status');
    }
  }

  /**
   * Trigger manual sync
   */
  async triggerSync() {
    try {
      const response = await apiService.post('/microsoft/sync/trigger');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to trigger sync');
    }
  }

  /**
   * Get user's organization info
   */
  async getOrganizationInfo() {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(`${this.graphBaseUrl}/organization`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Organization info error: ${response.status}`);
      }

      const data = await response.json();
      return data.value[0];
    } catch (error) {
      throw this.handleError(error, 'Failed to get organization info');
    }
  }

  /**
   * Get user's recent files
   */
  async getRecentFiles(limit = 10) {
    try {
      const token = await AuthService.getMicrosoftGraphToken();
      const response = await fetch(
        `${this.graphBaseUrl}/me/drive/recent?$top=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Recent files error: ${response.status}`);
      }

      const data = await response.json();
      return data.value;
    } catch (error) {
      throw this.handleError(error, 'Failed to get recent files');
    }
  }

  /**
   * Validate file for OneDrive upload
   */
  validateFileForUpload(file) {
    const errors = [];
    const warnings = [];

    // Check file size (OneDrive has a 15GB limit for single file)
    const maxSize = 15 * 1024 * 1024 * 1024; // 15GB
    if (file.size > maxSize) {
      errors.push('File size exceeds OneDrive single file limit (15GB)');
    }

    // Warn about large files
    const warningSize = 100 * 1024 * 1024; // 100MB
    if (file.size > warningSize) {
      warnings.push('Large file detected. Upload may take some time.');
    }

    // Check file name for invalid characters
    const invalidChars = /[<>:"|*?]/;
    if (invalidChars.test(file.name)) {
      errors.push('File name contains invalid characters: < > : " | * ?');
    }

    // Check file name length
    if (file.name.length > 255) {
      errors.push('File name is too long (max 255 characters)');
    }

    // Check for certain file types that might be blocked
    const blockedExtensions = ['.exe', '.bat', '.cmd', '.scr', '.pif'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (blockedExtensions.includes(extension)) {
      warnings.push('File type may be blocked by OneDrive security policies');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Generate OneDrive folder structure for document type
   */
  generateFolderStructure(documentType) {
    const baseFolder = 'SGD_Documents';
    const typeFolder = `${documentType.code}_${documentType.name.replace(/[^\w\s-]/g, '').trim()}`;
    const currentYear = new Date().getFullYear();
    
    return {
      base: baseFolder,
      type: `${baseFolder}/${typeFolder}`,
      year: `${baseFolder}/${typeFolder}/${currentYear}`,
      month: `${baseFolder}/${typeFolder}/${currentYear}/${String(new Date().getMonth() + 1).padStart(2, '0')}`,
    };
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file icon based on extension
   */
  getFileIcon(fileName) {
    const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.') + 1);
    
    const iconMap = {
      pdf: '=Ä',
      doc: '=Ý',
      docx: '=Ý',
      xls: '=Ê',
      xlsx: '=Ê',
      ppt: '=ý',
      pptx: '=ý',
      jpg: '=¼',
      jpeg: '=¼',
      png: '=¼',
      gif: '=¼',
      mp4: '<¥',
      avi: '<¥',
      mp3: '<µ',
      wav: '<µ',
      zip: '=æ',
      rar: '=æ',
      txt: '=Ä',
    };

    return iconMap[extension] || '=Ä';
  }

  /**
   * Handle service errors
   */
  handleError(error, message) {
    console.error(`MicrosoftService Error: ${message}`, error);
    
    const enhancedError = new Error(message);
    enhancedError.originalError = error;
    enhancedError.status = error.status;
    enhancedError.code = error.code;
    
    return enhancedError;
  }
}

// Export singleton instance
export const microsoftService = new MicrosoftService();
export default microsoftService;