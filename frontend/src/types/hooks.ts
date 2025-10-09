// =================================
// Hook Types
// =================================

import { 
  User, 
  Document, 
  DocumentType, 
  QRCode, 
  SearchFilters, 
  NotificationItem,
  DashboardStats,
  ActivityItem
} from './index';

// =================================
// Auth Hook Types
// =================================

export interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: any) => Promise<void>;
  loginWithMicrosoft: () => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export interface UseAuthConfig {
  autoRefresh?: boolean;
  refreshInterval?: number;
  onAuthStateChange?: (user: User | null) => void;
}

// =================================
// API Hook Types
// =================================

export interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  mutate: (data: T) => void;
}

export interface UseApiConfig<T> {
  enabled?: boolean;
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  retry?: boolean;
  retryDelay?: number;
  cacheTime?: number;
  staleTime?: number;
}

export interface UseMutationReturn<T, V> {
  mutate: (variables: V) => Promise<T>;
  data: T | null;
  loading: boolean;
  error: Error | null;
  reset: () => void;
}

export interface UseMutationConfig<T, V> {
  onSuccess?: (data: T, variables: V) => void;
  onError?: (error: Error, variables: V) => void;
  onSettled?: (data: T | null, error: Error | null, variables: V) => void;
}

// =================================
// Document Hook Types
// =================================

export interface UseDocumentsReturn {
  documents: Document[];
  total: number;
  loading: boolean;
  error: Error | null;
  filters: SearchFilters;
  setFilters: (filters: SearchFilters) => void;
  refetch: () => Promise<void>;
  loadMore: () => Promise<void>;
  hasMore: boolean;
}

export interface UseDocumentsConfig {
  initialFilters?: SearchFilters;
  autoLoad?: boolean;
  pageSize?: number;
  cache?: boolean;
}

export interface UseDocumentReturn {
  document: Document | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  update: (data: Partial<Document>) => Promise<void>;
  delete: () => Promise<void>;
  download: () => Promise<void>;
}

export interface UseDocumentUploadReturn {
  upload: (files: File[], metadata?: Record<string, any>) => Promise<void>;
  progress: number;
  loading: boolean;
  error: Error | null;
  reset: () => void;
  cancel: () => void;
}

export interface UseDocumentUploadConfig {
  chunkSize?: number;
  maxRetries?: number;
  onProgress?: (progress: number) => void;
  onSuccess?: (documents: Document[]) => void;
  onError?: (error: Error) => void;
}

// =================================
// Document Type Hook Types
// =================================

export interface UseDocumentTypesReturn {
  documentTypes: DocumentType[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  create: (data: Partial<DocumentType>) => Promise<DocumentType>;
  update: (id: string, data: Partial<DocumentType>) => Promise<DocumentType>;
  delete: (id: string) => Promise<void>;
}

export interface UseDocumentTypeReturn {
  documentType: DocumentType | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  update: (data: Partial<DocumentType>) => Promise<void>;
  delete: () => Promise<void>;
}

// =================================
// QR Code Hook Types
// =================================

export interface UseQRCodesReturn {
  qrCodes: QRCode[];
  total: number;
  loading: boolean;
  error: Error | null;
  filters: any;
  setFilters: (filters: any) => void;
  refetch: () => Promise<void>;
  generate: (data: any) => Promise<QRCode[]>;
  validate: (code: string) => Promise<boolean>;
}

export interface UseQRCodeReturn {
  qrCode: QRCode | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  validate: () => Promise<boolean>;
  regenerate: () => Promise<void>;
}

export interface UseQRScannerReturn {
  scanning: boolean;
  result: string | null;
  error: Error | null;
  startScan: () => void;
  stopScan: () => void;
  reset: () => void;
}

export interface UseQRScannerConfig {
  onScan?: (code: string) => void;
  onError?: (error: Error) => void;
  facingMode?: 'user' | 'environment';
  constraints?: MediaTrackConstraints;
}

// =================================
// Search Hook Types
// =================================

export interface UseSearchReturn {
  results: Document[];
  total: number;
  loading: boolean;
  error: Error | null;
  filters: SearchFilters;
  setFilters: (filters: SearchFilters) => void;
  search: (query: string) => Promise<void>;
  advancedSearch: (filters: SearchFilters) => Promise<void>;
  export: (format: 'csv' | 'excel' | 'pdf') => Promise<void>;
  clearResults: () => void;
}

export interface UseSearchConfig {
  debounceDelay?: number;
  minQueryLength?: number;
  maxResults?: number;
  saveHistory?: boolean;
}

export interface UseSearchHistoryReturn {
  history: string[];
  addToHistory: (query: string) => void;
  clearHistory: () => void;
  removeFromHistory: (query: string) => void;
}

// =================================
// Generator Hook Types
// =================================

export interface UseGeneratorReturn {
  generate: (data: any) => Promise<void>;
  progress: number;
  loading: boolean;
  error: Error | null;
  result: any;
  reset: () => void;
  cancel: () => void;
}

export interface UseGeneratorConfig {
  onProgress?: (progress: number) => void;
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
  batchSize?: number;
}

// =================================
// File Hook Types
// =================================

export interface UseFileUploadReturn {
  upload: (files: File[]) => Promise<void>;
  progress: number;
  loading: boolean;
  error: Error | null;
  reset: () => void;
  cancel: () => void;
}

export interface UseFileUploadConfig {
  accept?: string;
  maxSize?: number;
  maxFiles?: number;
  chunkSize?: number;
  onProgress?: (progress: number) => void;
  onSuccess?: (files: any[]) => void;
  onError?: (error: Error) => void;
}

export interface UseFileDownloadReturn {
  download: (url: string, filename?: string) => Promise<void>;
  progress: number;
  loading: boolean;
  error: Error | null;
  cancel: () => void;
}

export interface UseFileDownloadConfig {
  onProgress?: (progress: number) => void;
  onSuccess?: (blob: Blob) => void;
  onError?: (error: Error) => void;
}

// =================================
// Notification Hook Types
// =================================

export interface UseNotificationsReturn {
  notifications: NotificationItem[];
  unreadCount: number;
  loading: boolean;
  error: Error | null;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  delete: (id: string) => void;
  clear: () => void;
  refetch: () => Promise<void>;
}

export interface UseNotificationsConfig {
  autoRefresh?: boolean;
  refreshInterval?: number;
  maxNotifications?: number;
}

export interface UseToastReturn {
  show: (message: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
  hide: (id: string) => void;
  hideAll: () => void;
}

// =================================
// Dashboard Hook Types
// =================================

export interface UseDashboardReturn {
  stats: DashboardStats | null;
  activities: ActivityItem[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  refreshStats: () => Promise<void>;
  refreshActivities: () => Promise<void>;
}

export interface UseDashboardConfig {
  autoRefresh?: boolean;
  refreshInterval?: number;
  includeActivities?: boolean;
  activityLimit?: number;
}

// =================================
// Storage Hook Types
// =================================

export interface UseLocalStorageReturn<T> {
  value: T | null;
  setValue: (value: T | null) => void;
  removeValue: () => void;
}

export interface UseSessionStorageReturn<T> {
  value: T | null;
  setValue: (value: T | null) => void;
  removeValue: () => void;
}

// =================================
// Permission Hook Types
// =================================

export interface UsePermissionsReturn {
  can: (permission: string) => boolean;
  canAny: (permissions: string[]) => boolean;
  canAll: (permissions: string[]) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  isAdmin: boolean;
  permissions: string[];
  roles: string[];
}

export interface UsePermissionsConfig {
  user?: User;
  refreshOnUserChange?: boolean;
}

// =================================
// Form Hook Types
// =================================

export interface UseFormReturn<T> {
  values: T;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isValid: boolean;
  isSubmitting: boolean;
  setValue: (field: keyof T, value: any) => void;
  setValues: (values: Partial<T>) => void;
  setError: (field: keyof T, error: string) => void;
  setErrors: (errors: Record<string, string>) => void;
  clearError: (field: keyof T) => void;
  clearErrors: () => void;
  handleSubmit: (onSubmit: (values: T) => void | Promise<void>) => (event: React.FormEvent) => void;
  reset: (values?: T) => void;
  validate: () => boolean;
  validateField: (field: keyof T) => boolean;
}

export interface UseFormConfig<T> {
  initialValues?: T;
  validationSchema?: any;
  validate?: (values: T) => Record<string, string>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  enableReinitialize?: boolean;
}

// =================================
// Theme Hook Types
// =================================

export interface UseThemeReturn {
  theme: 'light' | 'dark' | 'auto';
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  toggleTheme: () => void;
  isDark: boolean;
  isLight: boolean;
  systemTheme: 'light' | 'dark';
}

export interface UseThemeConfig {
  defaultTheme?: 'light' | 'dark' | 'auto';
  storageKey?: string;
  attribute?: string;
}

// =================================
// Utility Hook Types
// =================================

export interface UseDebounceReturn<T> {
  debouncedValue: T;
  cancel: () => void;
  flush: () => void;
}

export interface UseClipboardReturn {
  copy: (text: string) => Promise<void>;
  copied: boolean;
  error: Error | null;
  isSupported: boolean;
}

export interface UseMediaQueryReturn {
  matches: boolean;
  media: string;
}

export interface UseOnlineReturn {
  isOnline: boolean;
  isOffline: boolean;
}

export interface UseWindowSizeReturn {
  width: number;
  height: number;
}

export interface UseScrollReturn {
  x: number;
  y: number;
  scrollTo: (x: number, y: number) => void;
  scrollToTop: () => void;
  scrollToBottom: () => void;
}

// =================================
// Validation Hook Types
// =================================

export interface UseValidationReturn {
  validate: (value: any, rules: ValidationRule[]) => string[];
  validateField: (field: string, value: any, rules: ValidationRule[]) => string[];
  validateForm: (data: Record<string, any>, schema: ValidationSchema) => Record<string, string[]>;
  isValid: (value: any, rules: ValidationRule[]) => boolean;
  isFormValid: (data: Record<string, any>, schema: ValidationSchema) => boolean;
}

export interface ValidationRule {
  type: 'required' | 'email' | 'min' | 'max' | 'pattern' | 'custom';
  message?: string;
  value?: any;
  validator?: (value: any) => boolean | string;
}

export interface ValidationSchema {
  [field: string]: ValidationRule[];
}