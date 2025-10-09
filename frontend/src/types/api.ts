// =================================
// API Client Types
// =================================

export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  headers?: Record<string, string>;
  withCredentials?: boolean;
  maxRetries?: number;
  retryDelay?: number;
}

export interface ApiRequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
  signal?: AbortSignal;
  onUploadProgress?: (progress: number) => void;
  onDownloadProgress?: (progress: number) => void;
}

export interface ApiEndpoints {
  // Auth endpoints
  LOGIN: string;
  LOGOUT: string;
  REFRESH: string;
  PROFILE: string;
  MICROSOFT_AUTH: string;
  
  // Document endpoints
  DOCUMENTS: string;
  DOCUMENT_DETAIL: (id: string) => string;
  DOCUMENT_UPLOAD: string;
  DOCUMENT_DOWNLOAD: (id: string) => string;
  DOCUMENT_PREVIEW: (id: string) => string;
  
  // Document Types endpoints
  DOCUMENT_TYPES: string;
  DOCUMENT_TYPE_DETAIL: (id: string) => string;
  
  // QR Code endpoints
  QR_CODES: string;
  QR_CODE_DETAIL: (id: string) => string;
  QR_GENERATE: string;
  QR_VALIDATE: string;
  QR_SCAN: string;
  
  // Generator endpoints
  GENERATOR_TEMPLATES: string;
  GENERATOR_GENERATE: string;
  GENERATOR_BATCH: string;
  
  // Search endpoints
  SEARCH_DOCUMENTS: string;
  SEARCH_ADVANCED: string;
  SEARCH_EXPORT: string;
  
  // User endpoints
  USERS: string;
  USER_DETAIL: (id: string) => string;
  USER_PREFERENCES: string;
  
  // System endpoints
  HEALTH: string;
  STATS: string;
  ACTIVITY: string;
  
  // File endpoints
  FILE_UPLOAD: string;
  FILE_DOWNLOAD: (id: string) => string;
  FILE_PREVIEW: (id: string) => string;
  
  // Microsoft 365 endpoints
  MICROSOFT_PROFILE: string;
  ONEDRIVE_UPLOAD: string;
  ONEDRIVE_LIST: string;
  ONEDRIVE_DOWNLOAD: (id: string) => string;
}

// =================================
// Request/Response Types
// =================================

export interface LoginRequest {
  email: string;
  password: string;
  remember?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    is_admin: boolean;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

export interface MicrosoftAuthRequest {
  code: string;
  state?: string;
  session_state?: string;
}

export interface MicrosoftAuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    given_name: string;
    family_name: string;
    picture?: string;
    tenant_id: string;
  };
}

export interface DocumentUploadRequest {
  file: File;
  document_type_id: string;
  title?: string;
  description?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  auto_extract_qr?: boolean;
}

export interface DocumentUploadResponse {
  id: string;
  title: string;
  file_name: string;
  file_size: number;
  file_type: string;
  file_url: string;
  onedrive_url?: string;
  qr_code?: {
    id: string;
    code: string;
    status: string;
  };
  created_at: string;
}

export interface DocumentListRequest {
  page?: number;
  per_page?: number;
  search?: string;
  document_type_id?: string;
  status?: string;
  created_by?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface DocumentListResponse {
  items: Array<{
    id: string;
    title: string;
    file_name: string;
    file_size: number;
    file_type: string;
    document_type: {
      id: string;
      code: string;
      name: string;
    };
    status: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    qr_code?: {
      id: string;
      code: string;
      status: string;
    };
  }>;
  meta: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface DocumentTypeCreateRequest {
  code: string;
  name: string;
  description?: string;
  requirements: {
    requires_qr: boolean;
    requires_cedula: boolean;
    requires_nombre: boolean;
    requires_telefono: boolean;
    requires_email: boolean;
    requires_direccion: boolean;
  };
  file_config: {
    allowed_file_types: string[];
    max_file_size_mb: number;
    allow_multiple_files: boolean;
  };
  workflow: {
    requires_approval: boolean;
    auto_notify_email: boolean;
    notification_emails: string[];
    retention_days: number;
  };
  qr_config?: {
    qr_table_number: number;
    qr_row: number;
    qr_column: number;
    qr_width: number;
    qr_height: number;
  };
}

export interface DocumentTypeResponse {
  id: string;
  code: string;
  name: string;
  description?: string;
  requirements: {
    requires_qr: boolean;
    requires_cedula: boolean;
    requires_nombre: boolean;
    requires_telefono: boolean;
    requires_email: boolean;
    requires_direccion: boolean;
  };
  file_config: {
    allowed_file_types: string[];
    max_file_size_mb: number;
    allow_multiple_files: boolean;
  };
  workflow: {
    requires_approval: boolean;
    auto_notify_email: boolean;
    notification_emails: string[];
    retention_days: number;
  };
  qr_config?: {
    qr_table_number: number;
    qr_row: number;
    qr_column: number;
    qr_width: number;
    qr_height: number;
  };
  template_path?: string;
  is_active: boolean;
  documents_count: number;
  created_at: string;
  updated_at: string;
}

export interface QRGenerateRequest {
  document_code?: string;
  document_type_id?: string;
  quantity?: number;
  metadata?: Record<string, any>;
  expires_in_days?: number;
}

export interface QRGenerateResponse {
  codes: Array<{
    id: string;
    code: string;
    document_code?: string;
    qr_image_url: string;
    created_at: string;
    expires_at?: string;
  }>;
  total_generated: number;
}

export interface QRValidateRequest {
  code: string;
  context?: string;
}

export interface QRValidateResponse {
  valid: boolean;
  qr_code?: {
    id: string;
    code: string;
    status: string;
    document_id?: string;
    document?: {
      id: string;
      title: string;
      file_name: string;
      document_type: {
        id: string;
        code: string;
        name: string;
      };
    };
    metadata?: Record<string, any>;
    created_at: string;
    expires_at?: string;
  };
  error?: string;
}

export interface GeneratorCreateRequest {
  document_type_id: string;
  template_data: Record<string, any>;
  quantity?: number;
  output_format?: 'docx' | 'pdf';
  include_qr?: boolean;
  batch_options?: {
    prefix?: string;
    start_number?: number;
    include_timestamp: boolean;
  };
}

export interface GeneratorCreateResponse {
  batch_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_documents: number;
  completed_documents: number;
  failed_documents: number;
  download_url?: string;
  files: Array<{
    id: string;
    name: string;
    size: number;
    download_url: string;
    qr_code?: {
      id: string;
      code: string;
    };
  }>;
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface SearchRequest {
  query?: string;
  filters?: {
    document_type_id?: string;
    status?: string;
    created_by?: string;
    date_from?: string;
    date_to?: string;
    tags?: string[];
    metadata?: Record<string, any>;
    has_qr?: boolean;
    qr_status?: string;
  };
  sort?: {
    field: string;
    order: 'asc' | 'desc';
  };
  pagination?: {
    page: number;
    per_page: number;
  };
}

export interface SearchResponse {
  results: Array<{
    id: string;
    title: string;
    file_name: string;
    file_size: number;
    file_type: string;
    document_type: {
      id: string;
      code: string;
      name: string;
    };
    status: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    qr_code?: {
      id: string;
      code: string;
      status: string;
    };
    metadata?: Record<string, any>;
    relevance_score?: number;
  }>;
  meta: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
    query_time: number;
  };
  facets?: {
    document_types: Array<{
      id: string;
      name: string;
      count: number;
    }>;
    statuses: Array<{
      status: string;
      count: number;
    }>;
    creators: Array<{
      id: string;
      name: string;
      count: number;
    }>;
  };
}

export interface StatsResponse {
  documents: {
    total: number;
    by_type: Array<{
      type_id: string;
      type_name: string;
      count: number;
    }>;
    by_status: Array<{
      status: string;
      count: number;
    }>;
    by_month: Array<{
      month: string;
      count: number;
    }>;
  };
  qr_codes: {
    total: number;
    active: number;
    used: number;
    expired: number;
    by_status: Array<{
      status: string;
      count: number;
    }>;
  };
  users: {
    total: number;
    active: number;
    by_role: Array<{
      role: string;
      count: number;
    }>;
  };
  storage: {
    used_bytes: number;
    total_bytes: number;
    usage_percentage: number;
    by_type: Array<{
      file_type: string;
      size_bytes: number;
      count: number;
    }>;
  };
}

export interface ActivityResponse {
  activities: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    user_id?: string;
    user_name?: string;
    metadata?: Record<string, any>;
    created_at: string;
  }>;
  meta: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// =================================
// Error Response Types
// =================================

export interface ErrorResponse {
  error: {
    message: string;
    code?: string;
    details?: any;
    fields?: Array<{
      field: string;
      message: string;
      code?: string;
    }>;
  };
  timestamp: string;
  path: string;
  method: string;
  status: number;
}

// =================================
// Upload Progress Types
// =================================

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate?: number;
  estimated_time?: number;
}

export interface DownloadProgress {
  loaded: number;
  total: number;
  percentage: number;
  rate?: number;
  estimated_time?: number;
}

// =================================
// Batch Operation Types
// =================================

export interface BatchOperationRequest {
  operation: 'delete' | 'archive' | 'restore' | 'export';
  item_ids: string[];
  parameters?: Record<string, any>;
}

export interface BatchOperationResponse {
  batch_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_items: number;
  processed_items: number;
  failed_items: number;
  results: Array<{
    item_id: string;
    success: boolean;
    error?: string;
  }>;
  created_at: string;
  completed_at?: string;
}