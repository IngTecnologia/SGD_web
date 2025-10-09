// =================================
// Component Props Types
// =================================

import { ReactNode, ComponentType } from 'react';
import { Document, DocumentType, QRCode, User, NotificationItem } from './index';

// =================================
// Common Component Props
// =================================

export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  id?: string;
  'data-testid'?: string;
}

export interface LoadingProps extends BaseComponentProps {
  loading?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  variant?: 'oval' | 'dots' | 'bars';
  overlay?: boolean;
  text?: string;
}

export interface ErrorProps extends BaseComponentProps {
  error?: Error | string | null;
  title?: string;
  description?: string;
  retry?: () => void;
  variant?: 'inline' | 'page' | 'modal';
}

export interface EmptyStateProps extends BaseComponentProps {
  title: string;
  description?: string;
  icon?: ComponentType<any>;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  };
  image?: string;
}

// =================================
// Layout Component Props
// =================================

export interface LayoutProps extends BaseComponentProps {
  user: User;
  onLogout: () => void;
  sidebar?: boolean;
  header?: boolean;
  footer?: boolean;
  breadcrumbs?: BreadcrumbItem[];
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
  icon?: ComponentType<any>;
  active?: boolean;
}

export interface HeaderProps extends BaseComponentProps {
  user: User;
  onLogout: () => void;
  notifications?: NotificationItem[];
  onNotificationRead?: (id: string) => void;
  onNotificationClear?: () => void;
}

export interface SidebarProps extends BaseComponentProps {
  user: User;
  currentPath: string;
  collapsed?: boolean;
  onToggle?: (collapsed: boolean) => void;
  items?: NavigationItem[];
}

export interface NavigationItem {
  key: string;
  label: string;
  href?: string;
  icon?: ComponentType<any>;
  badge?: string | number;
  children?: NavigationItem[];
  disabled?: boolean;
  external?: boolean;
  onClick?: () => void;
}

// =================================
// Form Component Props
// =================================

export interface FormProps extends BaseComponentProps {
  onSubmit: (data: any) => void | Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  initialValues?: Record<string, any>;
  validationSchema?: any;
}

export interface FormFieldProps extends BaseComponentProps {
  name: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  help?: string;
  placeholder?: string;
}

export interface FileUploadProps extends BaseComponentProps {
  onUpload: (files: File[]) => void | Promise<void>;
  multiple?: boolean;
  accept?: string;
  maxSize?: number;
  maxFiles?: number;
  loading?: boolean;
  disabled?: boolean;
  preview?: boolean;
  dragDrop?: boolean;
  description?: string;
  error?: string;
}

export interface QRScannerProps extends BaseComponentProps {
  onScan: (code: string) => void;
  onError?: (error: Error) => void;
  active?: boolean;
  width?: number;
  height?: number;
  facingMode?: 'user' | 'environment';
  torch?: boolean;
  zoom?: number;
}

// =================================
// Table Component Props
// =================================

export interface DataTableProps<T = any> extends BaseComponentProps {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  pagination?: PaginationProps;
  selection?: SelectionProps<T>;
  sorting?: SortingProps;
  filtering?: FilteringProps;
  actions?: ActionProps<T>[];
  emptyState?: EmptyStateProps;
  rowKey?: string | ((record: T) => string);
  onRowClick?: (record: T) => void;
  rowClassName?: (record: T) => string;
  expandable?: ExpandableProps<T>;
}

export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex?: string;
  render?: (value: any, record: T, index: number) => ReactNode;
  width?: number;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  fixed?: 'left' | 'right';
  ellipsis?: boolean;
  className?: string;
}

export interface PaginationProps {
  current: number;
  total: number;
  pageSize: number;
  onChange: (page: number, pageSize: number) => void;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: (total: number, range: [number, number]) => string;
  pageSizeOptions?: string[];
}

export interface SelectionProps<T = any> {
  selectedRowKeys: string[];
  onChange: (selectedRowKeys: string[], selectedRows: T[]) => void;
  onSelectAll?: (selected: boolean, selectedRows: T[], changeRows: T[]) => void;
  onSelect?: (record: T, selected: boolean, selectedRows: T[]) => void;
  getCheckboxProps?: (record: T) => { disabled?: boolean };
  columnTitle?: string;
  columnWidth?: number;
  fixed?: boolean;
}

export interface SortingProps {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
}

export interface FilteringProps {
  filters?: Record<string, any>;
  onChange: (filters: Record<string, any>) => void;
}

export interface ActionProps<T = any> {
  key: string;
  label: string;
  icon?: ComponentType<any>;
  onClick: (record: T) => void;
  disabled?: (record: T) => boolean;
  loading?: (record: T) => boolean;
  confirm?: {
    title: string;
    content?: string;
    okText?: string;
    cancelText?: string;
  };
  type?: 'primary' | 'secondary' | 'danger';
}

export interface ExpandableProps<T = any> {
  expandedRowRender: (record: T) => ReactNode;
  expandedRowKeys?: string[];
  onExpandedRowsChange?: (expandedRowKeys: string[]) => void;
  expandRowByClick?: boolean;
  expandIcon?: (props: any) => ReactNode;
}

// =================================
// Modal Component Props
// =================================

export interface ModalProps extends BaseComponentProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  width?: number;
  height?: number;
  centered?: boolean;
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
  footer?: ReactNode;
  loading?: boolean;
  zIndex?: number;
}

export interface ConfirmModalProps extends Omit<ModalProps, 'footer'> {
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  confirmLoading?: boolean;
  danger?: boolean;
  content?: ReactNode;
}

export interface DrawerProps extends BaseComponentProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  width?: number;
  placement?: 'left' | 'right' | 'top' | 'bottom';
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
  footer?: ReactNode;
  loading?: boolean;
}

// =================================
// Card Component Props
// =================================

export interface CardProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  extra?: ReactNode;
  cover?: string;
  actions?: ReactNode[];
  loading?: boolean;
  bordered?: boolean;
  hoverable?: boolean;
  size?: 'small' | 'default' | 'large';
  type?: 'inner' | 'default';
}

export interface StatsCardProps extends BaseComponentProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
    timeframe?: string;
  };
  icon?: ComponentType<any>;
  color?: string;
  loading?: boolean;
}

// =================================
// Document Component Props
// =================================

export interface DocumentCardProps extends BaseComponentProps {
  document: Document;
  onView?: (document: Document) => void;
  onDownload?: (document: Document) => void;
  onEdit?: (document: Document) => void;
  onDelete?: (document: Document) => void;
  actions?: ActionProps<Document>[];
  selectable?: boolean;
  selected?: boolean;
  onSelect?: (document: Document, selected: boolean) => void;
}

export interface DocumentViewerProps extends BaseComponentProps {
  document: Document;
  onClose: () => void;
  onDownload?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  toolbar?: boolean;
  fullscreen?: boolean;
}

export interface DocumentPreviewProps extends BaseComponentProps {
  document: Document;
  width?: number;
  height?: number;
  showControls?: boolean;
  onError?: (error: Error) => void;
}

export interface DocumentUploadProps extends BaseComponentProps {
  documentType?: DocumentType;
  onUpload: (files: File[], metadata?: Record<string, any>) => void | Promise<void>;
  multiple?: boolean;
  loading?: boolean;
  disabled?: boolean;
  progress?: number;
  error?: string;
}

export interface DocumentFormProps extends BaseComponentProps {
  documentType: DocumentType;
  onSubmit: (data: any) => void | Promise<void>;
  initialValues?: Record<string, any>;
  loading?: boolean;
  disabled?: boolean;
}

// =================================
// QR Code Component Props
// =================================

export interface QRCodeDisplayProps extends BaseComponentProps {
  qrCode: QRCode;
  size?: number;
  showDetails?: boolean;
  showActions?: boolean;
  onDownload?: (qrCode: QRCode) => void;
  onPrint?: (qrCode: QRCode) => void;
  onValidate?: (qrCode: QRCode) => void;
}

export interface QRCodeGeneratorProps extends BaseComponentProps {
  onGenerate: (data: any) => void | Promise<void>;
  documentType?: DocumentType;
  loading?: boolean;
  disabled?: boolean;
}

// =================================
// Search Component Props
// =================================

export interface SearchFormProps extends BaseComponentProps {
  onSearch: (filters: any) => void;
  documentTypes?: DocumentType[];
  loading?: boolean;
  initialValues?: Record<string, any>;
  advanced?: boolean;
}

export interface SearchResultsProps extends BaseComponentProps {
  results: Document[];
  total: number;
  loading?: boolean;
  onView?: (document: Document) => void;
  onDownload?: (document: Document) => void;
  onSelect?: (documents: Document[]) => void;
  selection?: SelectionProps<Document>;
  pagination?: PaginationProps;
  emptyState?: EmptyStateProps;
}

export interface AdvancedFiltersProps extends BaseComponentProps {
  filters: Record<string, any>;
  onChange: (filters: Record<string, any>) => void;
  documentTypes?: DocumentType[];
  users?: User[];
  onReset?: () => void;
  loading?: boolean;
}

// =================================
// Generator Component Props
// =================================

export interface GeneratorFormProps extends BaseComponentProps {
  documentTypes: DocumentType[];
  onGenerate: (data: any) => void | Promise<void>;
  loading?: boolean;
  disabled?: boolean;
}

export interface TemplateSelectionProps extends BaseComponentProps {
  documentType: DocumentType;
  onSelect: (template: string) => void;
  selected?: string;
  loading?: boolean;
}

export interface ProgressModalProps extends BaseComponentProps {
  visible: boolean;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  title?: string;
  description?: string;
  onCancel?: () => void;
  onClose?: () => void;
  cancelable?: boolean;
}

// =================================
// Admin Component Props
// =================================

export interface UserManagementProps extends BaseComponentProps {
  users: User[];
  onInvite: (userData: any) => void | Promise<void>;
  onUpdate: (userId: string, userData: any) => void | Promise<void>;
  onDelete: (userId: string) => void | Promise<void>;
  onRoleChange: (userId: string, role: string) => void | Promise<void>;
  loading?: boolean;
}

export interface DocumentTypeFormProps extends BaseComponentProps {
  documentType?: DocumentType;
  onSubmit: (data: any) => void | Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export interface SystemStatsProps extends BaseComponentProps {
  stats: {
    documents: number;
    users: number;
    qrCodes: number;
    storage: number;
  };
  charts?: {
    documentsOverTime: Array<{ date: string; count: number }>;
    documentsByType: Array<{ type: string; count: number }>;
    userActivity: Array<{ date: string; count: number }>;
  };
  loading?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
}

// =================================
// Notification Component Props
// =================================

export interface NotificationListProps extends BaseComponentProps {
  notifications: NotificationItem[];
  onRead: (id: string) => void;
  onReadAll: () => void;
  onDelete: (id: string) => void;
  onClear: () => void;
  loading?: boolean;
  maxHeight?: number;
}

export interface NotificationItemProps extends BaseComponentProps {
  notification: NotificationItem;
  onRead: (id: string) => void;
  onDelete: (id: string) => void;
  onClick?: (notification: NotificationItem) => void;
}

// =================================
// Chart Component Props
// =================================

export interface ChartProps extends BaseComponentProps {
  data: any[];
  width?: number;
  height?: number;
  loading?: boolean;
  error?: string;
  title?: string;
  description?: string;
}

export interface LineChartProps extends ChartProps {
  xKey: string;
  yKey: string;
  color?: string;
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
}

export interface BarChartProps extends ChartProps {
  xKey: string;
  yKey: string;
  color?: string;
  horizontal?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
}

export interface PieChartProps extends ChartProps {
  nameKey: string;
  valueKey: string;
  colors?: string[];
  showTooltip?: boolean;
  showLegend?: boolean;
  innerRadius?: number;
  outerRadius?: number;
}