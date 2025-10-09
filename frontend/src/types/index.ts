// =================================
// Core Types for SGD Web Application
// =================================

export interface User {
  id: string;
  email: string;
  name: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
  tenant_id?: string;
  role: UserRole;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  preferences?: UserPreferences;
}

export enum UserRole {
  ADMIN = 'admin',
  OPERATOR = 'operator',
  VIEWER = 'viewer'
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'es' | 'en';
  notifications: boolean;
  email_notifications: boolean;
  items_per_page: number;
  default_view: 'grid' | 'list';
}

// =================================
// Document Types
// =================================

export interface Document {
  id: string;
  title: string;
  description?: string;
  file_name: string;
  file_size: number;
  file_type: string;
  file_url?: string;
  onedrive_url?: string;
  onedrive_id?: string;
  document_type_id: string;
  document_type: DocumentType;
  qr_code_id?: string;
  qr_code?: QRCode;
  metadata: DocumentMetadata;
  status: DocumentStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
  is_deleted: boolean;
  tags?: string[];
}

export enum DocumentStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted'
}

export interface DocumentMetadata {
  cedula?: string;
  nombre?: string;
  telefono?: string;
  email?: string;
  direccion?: string;
  fecha_documento?: string;
  departamento?: string;
  categoria?: string;
  numero_documento?: string;
  observaciones?: string;
  [key: string]: any;
}

export interface DocumentType {
  id: string;
  code: string;
  name: string;
  description?: string;
  requirements: DocumentRequirements;
  file_config: FileConfig;
  workflow: WorkflowConfig;
  qr_config?: QRConfig;
  template_path?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  documents_count?: number;
}

export interface DocumentRequirements {
  requires_qr: boolean;
  requires_cedula: boolean;
  requires_nombre: boolean;
  requires_telefono: boolean;
  requires_email: boolean;
  requires_direccion: boolean;
  custom_fields?: CustomField[];
}

export interface CustomField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'date' | 'select' | 'textarea';
  required: boolean;
  options?: string[];
  validation?: string;
  placeholder?: string;
  help_text?: string;
}

export interface FileConfig {
  allowed_file_types: string[];
  max_file_size_mb: number;
  allow_multiple_files: boolean;
  auto_generate_name: boolean;
  name_pattern?: string;
}

export interface WorkflowConfig {
  requires_approval: boolean;
  auto_notify_email: boolean;
  notification_emails: string[];
  retention_days: number;
  auto_archive: boolean;
  archive_after_days?: number;
}

export interface QRConfig {
  qr_table_number: number;
  qr_row: number;
  qr_column: number;
  qr_width: number;
  qr_height: number;
  qr_position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
}

// =================================
// QR Code Types
// =================================

export interface QRCode {
  id: string;
  code: string;
  document_code?: string;
  document_id?: string;
  document?: Document;
  status: QRStatus;
  metadata?: QRMetadata;
  created_at: string;
  used_at?: string;
  expires_at?: string;
  is_expired: boolean;
  scan_count: number;
  last_scan_at?: string;
}

export enum QRStatus {
  GENERATED = 'generated',
  ACTIVE = 'active',
  USED = 'used',
  EXPIRED = 'expired',
  INVALID = 'invalid'
}

export interface QRMetadata {
  generation_method: 'manual' | 'automatic';
  template_used?: string;
  generated_by?: string;
  purpose?: string;
  additional_data?: { [key: string]: any };
}

// =================================
// API Response Types
// =================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: ApiError[];
  meta?: ResponseMeta;
}

export interface ApiError {
  field?: string;
  message: string;
  code?: string;
  details?: any;
}

export interface ResponseMeta {
  total?: number;
  page?: number;
  per_page?: number;
  pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: ResponseMeta;
}

// =================================
// Form Types
// =================================

export interface DocumentGenerationForm {
  document_type_id: string;
  quantity: number;
  metadata: DocumentMetadata;
  template_overrides?: Partial<QRConfig>;
  batch_options?: BatchOptions;
}

export interface BatchOptions {
  prefix?: string;
  start_number?: number;
  include_timestamp: boolean;
  folder_structure: 'flat' | 'by_date' | 'by_type';
}

export interface DocumentRegistrationForm {
  file: File;
  document_type_id: string;
  title: string;
  description?: string;
  metadata: DocumentMetadata;
  tags?: string[];
  auto_extract_qr: boolean;
  override_qr_data?: boolean;
}

export interface SearchFilters {
  query?: string;
  document_type_id?: string;
  status?: DocumentStatus;
  created_by?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  metadata_filters?: { [key: string]: any };
  has_qr?: boolean;
  qr_status?: QRStatus;
  sort_by?: 'created_at' | 'updated_at' | 'title' | 'file_size';
  sort_order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}

// =================================
// UI Component Types
// =================================

export interface TableColumn<T = any> {
  key: string;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
  width?: number;
  align?: 'left' | 'center' | 'right';
  hidden?: boolean;
}

export interface NavigationItem {
  key: string;
  label: string;
  icon?: React.ComponentType<any>;
  path?: string;
  children?: NavigationItem[];
  disabled?: boolean;
  badge?: string | number;
  external?: boolean;
}

export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface DashboardStats {
  total_documents: number;
  documents_this_month: number;
  total_qr_codes: number;
  active_qr_codes: number;
  total_users: number;
  storage_used: number;
  storage_limit: number;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'document_created' | 'document_updated' | 'qr_generated' | 'user_login' | 'system_error';
  title: string;
  description: string;
  user_name?: string;
  timestamp: string;
  metadata?: { [key: string]: any };
}

// =================================
// Microsoft 365 Integration Types
// =================================

export interface MSGraphUser {
  id: string;
  displayName: string;
  givenName: string;
  surname: string;
  mail: string;
  userPrincipalName: string;
  jobTitle?: string;
  department?: string;
  companyName?: string;
  officeLocation?: string;
}

export interface OneDriveFile {
  id: string;
  name: string;
  size: number;
  webUrl: string;
  downloadUrl?: string;
  mimeType: string;
  createdDateTime: string;
  lastModifiedDateTime: string;
  parentReference?: {
    id: string;
    path: string;
  };
}

export interface OneDriveUploadResponse {
  id: string;
  name: string;
  size: number;
  webUrl: string;
  downloadUrl: string;
  parentReference: {
    id: string;
    path: string;
  };
}

// =================================
// Error Types
// =================================

export interface AppError {
  name: string;
  message: string;
  code?: string;
  status?: number;
  timestamp: string;
  stack?: string;
  context?: { [key: string]: any };
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
  constraint?: string;
}

// =================================
// Auth Types
// =================================

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember?: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  refresh_token: string;
  expires_in: number;
}

// =================================
// Theme Types
// =================================

export interface Theme {
  colorScheme: 'light' | 'dark';
  primaryColor: string;
  colors: {
    primary: string[];
    secondary: string[];
    success: string[];
    warning: string[];
    error: string[];
    info: string[];
    gray: string[];
  };
  fonts: {
    body: string;
    heading: string;
    monospace: string;
  };
  fontSizes: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  breakpoints: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// =================================
// Utility Types
// =================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type Required<T, K extends keyof T> = T & Pick<Required<T>, K>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// =================================
// Export All
// =================================

export * from './api';
export * from './components';
export * from './hooks';