import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { MantineProvider } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { NavigationProgress } from '@mantine/nprogress';
import { HelmetProvider } from 'react-helmet-async';
import { ErrorBoundary } from 'react-error-boundary';

// En Mantine v6, los estilos se manejan automáticamente con withGlobalStyles
// No se requieren imports de CSS explícitos

// Importar estilos personalizados
import './styles/globals.css';
import './styles/variables.css';
import './styles/components.css';

// Importar componentes
import App from './App';
import ErrorFallback from './components/common/ErrorFallback';

// Configurar React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 10 * 60 * 1000, // 10 minutos
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
});

// Tema personalizado para Mantine
const theme = {
  colorScheme: 'light',
  primaryColor: 'blue',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  headings: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: 600,
  },
  colors: {
    // Colores corporativos profesionales
    brand: [
      '#f0f9ff',
      '#e0f2fe',
      '#bae6fd',
      '#7dd3fc',
      '#38bdf8',
      '#0ea5e9',
      '#0284c7',
      '#0369a1',
      '#075985',
      '#0c4a6e',
    ],
    success: [
      '#f0fdf4',
      '#dcfce7',
      '#bbf7d0',
      '#86efac',
      '#4ade80',
      '#22c55e',
      '#16a34a',
      '#15803d',
      '#166534',
      '#14532d',
    ],
    warning: [
      '#fffbeb',
      '#fef3c7',
      '#fde68a',
      '#fcd34d',
      '#fbbf24',
      '#f59e0b',
      '#d97706',
      '#b45309',
      '#92400e',
      '#78350f',
    ],
    error: [
      '#fef2f2',
      '#fee2e2',
      '#fecaca',
      '#fca5a5',
      '#f87171',
      '#ef4444',
      '#dc2626',
      '#b91c1c',
      '#991b1b',
      '#7f1d1d',
    ],
  },
  shadows: {
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
  components: {
    Button: {
      styles: (theme) => ({
        root: {
          fontWeight: 500,
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: theme.shadows.md,
          },
        },
      }),
    },
    Card: {
      styles: (theme) => ({
        root: {
          boxShadow: theme.shadows.sm,
          border: `1px solid ${theme.colors.gray[2]}`,
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: theme.shadows.md,
          },
        },
      }),
    },
    Paper: {
      styles: (theme) => ({
        root: {
          boxShadow: theme.shadows.xs,
          border: `1px solid ${theme.colors.gray[1]}`,
        },
      }),
    },
    Input: {
      styles: (theme) => ({
        input: {
          borderColor: theme.colors.gray[3],
          '&:focus': {
            borderColor: theme.colors.blue[5],
            boxShadow: `0 0 0 3px ${theme.colors.blue[1]}`,
          },
        },
      }),
    },
    Notification: {
      styles: (theme) => ({
        root: {
          borderLeft: `4px solid ${theme.colors.blue[5]}`,
          boxShadow: theme.shadows.lg,
        },
      }),
    },
  },
};

// Componente ra�z
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <HelmetProvider>
      <ErrorBoundary
        FallbackComponent={ErrorFallback}
        onError={(error, errorInfo) => {
          console.error('Error capturado por ErrorBoundary:', error, errorInfo);
          // Aqu� puedes enviar el error a un servicio de monitoreo
        }}
      >
        <BrowserRouter>
          <QueryClientProvider client={queryClient}>
            <MantineProvider theme={theme} withGlobalStyles withNormalizeCSS>
              <ModalsProvider>
                <Notifications 
                  position="top-right"
                  limit={5}
                  zIndex={9999}
                />
                <NavigationProgress />
                <App />
                {process.env.NODE_ENV === 'development' && (
                  <ReactQueryDevtools initialIsOpen={false} />
                )}
              </ModalsProvider>
            </MantineProvider>
          </QueryClientProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </HelmetProvider>
  </React.StrictMode>
);

// Registrar Service Worker en producci�n
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// Configurar manejo de errores no capturados
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // Aqu� puedes enviar el error a un servicio de monitoreo
});

window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  // Aqu� puedes enviar el error a un servicio de monitoreo
});

// Reportar Web Vitals
if (process.env.NODE_ENV === 'production') {
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    getCLS(console.log);
    getFID(console.log);
    getFCP(console.log);
    getLCP(console.log);
    getTTFB(console.log);
  });
}