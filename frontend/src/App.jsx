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

// Hooks
import { useAuth } from './hooks/useAuth';

// Pages (Lazy loaded para mejor performance)
const Login = React.lazy(() => import('./pages/Login'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Register = React.lazy(() => import('./pages/Register'));
const Search = React.lazy(() => import('./pages/Search'));
const Generator = React.lazy(() => import('./pages/Generator'));
const Admin = React.lazy(() => import('./pages/Admin'));
const NotFound = React.lazy(() => import('./pages/NotFound'));

// Configuraci�n de la aplicaci�n
const AppContent = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    // Configurar t�tulo din�mico de la p�gina
    document.title = 'SGD Web - Sistema de Gesti�n Documental';
    
    // Configurar meta viewport para dispositivos m�viles
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

  // Mostrar loading mientras se verifica autenticaci�n
  if (isLoading) {
    return <LoadingScreen message="Verificando autenticaci�n..." />;
  }

  // Si no est� autenticado, mostrar solo rutas p�blicas
  if (!isAuthenticated) {
    return (
      <>
        <Helmet>
          <title>SGD Web - Iniciar Sesi�n</title>
          <meta name="description" content="Sistema de Gesti�n Documental Web - Iniciar Sesi�n con Microsoft 365" />
        </Helmet>
        
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </>
    );
  }

  // Si est� autenticado, mostrar aplicaci�n completa
  return (
    <>
      <Helmet>
        <title>SGD Web - Dashboard</title>
        <meta name="description" content="Sistema de Gesti�n Documental Web - Panel de Control" />
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>

      <Layout>
        <Suspense fallback={<LoadingScreen message="Cargando m�dulo..." />}>
          <Routes>
            {/* Redirecci�n ra�z */}
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
            
            {/* B�squeda de documentos */}
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
            
            {/* Panel de administraci�n */}
            <Route 
              path="/admin/*" 
              element={
                <ProtectedRoute requiredRole="admin">
                  <Admin />
                </ProtectedRoute>
              } 
            />
            
            {/* P�gina no encontrada */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </Layout>
    </>
  );
};

// Componente principal de la aplicaci�n
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