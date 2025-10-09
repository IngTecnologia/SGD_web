import React, { Suspense, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { AppShell } from '@mantine/core';

// Context Providers
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';

// Components
import Layout from './components/common/Layout';
import LoadingScreen from './components/common/LoadingScreen';
import ProtectedRoute from './components/common/ProtectedRoute';

// Pages (Lazy loaded para mejor performance)
const Login = React.lazy(() => import('./pages/Login'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Register = React.lazy(() => import('./pages/Register'));
const Search = React.lazy(() => import('./pages/Search'));
const Generator = React.lazy(() => import('./pages/Generator'));
const Admin = React.lazy(() => import('./pages/Admin'));
const NotFound = React.lazy(() => import('./pages/NotFound'));

// Hooks
import { useAuth } from './hooks/useAuth';

// Configuración de la aplicación
const AppContent = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    // Configurar título dinámico de la página
    document.title = 'SGD Web - Sistema de Gestión Documental';
    
    // Configurar meta viewport para dispositivos móviles
    const viewport = document.querySelector("meta[name=viewport]");
    if (viewport) {
      viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
    }

    // Prevenir zoom en iOS
    document.addEventListener('gesturestart', function (e) {
      e.preventDefault();
    });

    // Configurar tema inicial
    const savedTheme = localStorage.getItem('sgd-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    return () => {
      document.removeEventListener('gesturestart', function (e) {
        e.preventDefault();
      });
    };
  }, []);

  // Mostrar loading mientras se verifica autenticación
  if (isLoading) {
    return <LoadingScreen message="Verificando autenticación..." />;
  }

  // Si no está autenticado, mostrar solo rutas públicas
  if (!isAuthenticated) {
    return (
      <>
        <Helmet>
          <title>SGD Web - Iniciar Sesión</title>
          <meta name="description" content="Sistema de Gestión Documental Web - Iniciar Sesión con Microsoft 365" />
        </Helmet>
        
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </>
    );
  }

  // Si está autenticado, mostrar aplicación completa
  return (
    <>
      <Helmet>
        <title>SGD Web - Dashboard</title>
        <meta name="description" content="Sistema de Gestión Documental Web - Panel de Control" />
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>

      <Layout>
        <Suspense fallback={<LoadingScreen message="Cargando módulo..." />}>
          <Routes>
            {/* Redirección raíz */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* Dashboard principal */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* Registro de documentos */}
            <Route 
              path="/register" 
              element={
                <ProtectedRoute requiredRole="operator">
                  <Register />
                </ProtectedRoute>
              } 
            />
            
            {/* Búsqueda de documentos */}
            <Route 
              path="/search" 
              element={
                <ProtectedRoute>
                  <Search />
                </ProtectedRoute>
              } 
            />
            
            {/* Generador de documentos */}
            <Route 
              path="/generator" 
              element={
                <ProtectedRoute requiredRole="operator">
                  <Generator />
                </ProtectedRoute>
              } 
            />
            
            {/* Panel de administración */}
            <Route 
              path="/admin/*" 
              element={
                <ProtectedRoute requiredRole="admin">
                  <Admin />
                </ProtectedRoute>
              } 
            />
            
            {/* Página no encontrada */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </Layout>
    </>
  );
};

// Componente principal de la aplicación
const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <div id="sgd-app" className="sgd-app">
          <AppContent />
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;