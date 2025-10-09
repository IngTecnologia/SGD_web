import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  Button,
  Group,
  Stack,
  ThemeIcon,
  Alert,
} from '@mantine/core';
import {
  IconShieldX,
  IconArrowLeft,
  IconHome,
  IconLogin,
  IconUserX,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

import { useAuth } from '../../hooks/useAuth';
import LoadingScreen from './LoadingScreen';

const ProtectedRoute = ({ 
  children, 
  requiredRole = null,
  requiredPermission = null,
  fallbackPath = '/login',
  showAccessDenied = true 
}) => {
  const { 
    isAuthenticated, 
    isLoading, 
    user, 
    hasRole, 
    hasPermission 
  } = useAuth();
  
  const location = useLocation();

  // Mostrar loading mientras se verifica autenticación
  if (isLoading) {
    return <LoadingScreen message="Verificando permisos..." variant="auth" />;
  }

  // Si no está autenticado, redirigir al login
  if (!isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ 
          from: location.pathname,
          message: 'Debes iniciar sesión para acceder a esta página'
        }} 
        replace 
      />
    );
  }

  // Verificar rol requerido
  if (requiredRole && !hasRole(requiredRole)) {
    if (!showAccessDenied) {
      return <Navigate to="/dashboard" replace />;
    }

    return (
      <AccessDeniedPage 
        type="role"
        requiredRole={requiredRole}
        userRole={user?.role}
        userName={user?.name}
      />
    );
  }

  // Verificar permiso requerido
  if (requiredPermission && !hasPermission(requiredPermission)) {
    if (!showAccessDenied) {
      return <Navigate to="/dashboard" replace />;
    }

    return (
      <AccessDeniedPage 
        type="permission"
        requiredPermission={requiredPermission}
        userName={user?.name}
      />
    );
  }

  // Si todo está bien, renderizar el componente
  return children;
};

// Componente para mostrar error de acceso denegado
const AccessDeniedPage = ({ 
  type = 'role', 
  requiredRole = null,
  requiredPermission = null,
  userRole = null,
  userName = 'Usuario'
}) => {
  const getTitle = () => {
    switch (type) {
      case 'role':
        return 'Acceso Denegado - Rol Insuficiente';
      case 'permission':
        return 'Acceso Denegado - Permisos Insuficientes';
      default:
        return 'Acceso Denegado';
    }
  };

  const getMessage = () => {
    switch (type) {
      case 'role':
        return `Tu rol actual (${userRole}) no tiene permisos para acceder a esta sección. Se requiere el rol: ${requiredRole}.`;
      case 'permission':
        return `No tienes los permisos necesarios para acceder a esta funcionalidad. Permiso requerido: ${requiredPermission}.`;
      default:
        return 'No tienes autorización para acceder a esta página.';
    }
  };

  const getSuggestion = () => {
    switch (type) {
      case 'role':
        return 'Contacta al administrador del sistema para solicitar una elevación de permisos.';
      case 'permission':
        return 'Si crees que deberías tener acceso, contacta al administrador del sistema.';
      default:
        return 'Verifica tus credenciales o contacta al soporte técnico.';
    }
  };

  const getRoleInfo = () => {
    const roles = {
      admin: {
        name: 'Administrador',
        description: 'Acceso completo al sistema',
        color: 'red',
      },
      operator: {
        name: 'Operador',
        description: 'Puede generar, registrar y buscar documentos',
        color: 'blue',
      },
      viewer: {
        name: 'Visualizador',
        description: 'Solo puede consultar documentos',
        color: 'green',
      },
    };

    return roles[requiredRole] || { name: requiredRole, description: '', color: 'gray' };
  };

  return (
    <Container size="md" style={{ marginTop: '10vh' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper p="xl" radius="lg" shadow="md" withBorder>
          <Stack spacing="lg" align="center">
            {/* Icono de error */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ 
                delay: 0.2, 
                type: "spring", 
                stiffness: 200 
              }}
            >
              <ThemeIcon
                size={80}
                radius="xl"
                variant="light"
                color="red"
                style={{
                  backgroundColor: '#fef2f2',
                  border: '2px solid #fecaca',
                }}
              >
                <IconShieldX size={40} />
              </ThemeIcon>
            </motion.div>

            {/* Título y mensaje */}
            <Stack spacing="md" align="center" style={{ textAlign: 'center' }}>
              <Title order={1} color="red.6">
                {getTitle()}
              </Title>

              <Text size="lg" color="gray.7">
                Hola {userName}, lamentablemente no puedes acceder a esta sección.
              </Text>

              <Alert
                icon={<IconUserX size={16} />}
                title="Información de acceso"
                color="orange"
                style={{ width: '100%' }}
              >
                <Text size="sm" mb="xs">
                  <strong>Problema:</strong> {getMessage()}
                </Text>
                <Text size="sm">
                  <strong>Solución:</strong> {getSuggestion()}
                </Text>
              </Alert>

              {/* Información de rol requerido */}
              {type === 'role' && requiredRole && (
                <Paper p="md" style={{ width: '100%', backgroundColor: '#f8f9fa' }}>
                  <Text size="sm" weight={500} mb="xs">
                    Rol requerido:
                  </Text>
                  <Group spacing="xs">
                    <ThemeIcon
                      size="sm"
                      color={getRoleInfo().color}
                      variant="light"
                    >
                      <IconShieldX size={12} />
                    </ThemeIcon>
                    <Text size="sm" weight={500}>
                      {getRoleInfo().name}
                    </Text>
                    <Text size="sm" color="gray.6">
                      - {getRoleInfo().description}
                    </Text>
                  </Group>
                </Paper>
              )}
            </Stack>

            {/* Acciones disponibles */}
            <Group spacing="md">
              <Button
                leftIcon={<IconArrowLeft size={16} />}
                variant="light"
                color="gray"
                onClick={() => window.history.back()}
              >
                Volver atrás
              </Button>

              <Button
                leftIcon={<IconHome size={16} />}
                variant="filled"
                color="blue"
                onClick={() => window.location.href = '/dashboard'}
              >
                Ir al Dashboard
              </Button>

              <Button
                leftIcon={<IconLogin size={16} />}
                variant="outline"
                color="red"
                onClick={() => window.location.href = '/login'}
              >
                Cambiar cuenta
              </Button>
            </Group>

            {/* Información de contacto */}
            <Paper p="md" style={{ width: '100%', backgroundColor: '#f8f9fa' }}>
              <Text size="sm" color="gray.6" align="center">
                <strong>¿Necesitas ayuda?</strong>
                <br />
                Contacta al administrador del sistema o envía un correo a{' '}
                <Text component="span" color="blue.6" weight={500}>
                  soporte@tuempresa.com
                </Text>
              </Text>
            </Paper>
          </Stack>
        </Paper>
      </motion.div>
    </Container>
  );
};

// HOC para proteger componentes (alternativa al componente ProtectedRoute)
export const withAuth = (Component, options = {}) => {
  const { 
    requiredRole = null,
    requiredPermission = null,
    fallbackPath = '/login',
    showAccessDenied = true
  } = options;

  return function AuthenticatedComponent(props) {
    return (
      <ProtectedRoute
        requiredRole={requiredRole}
        requiredPermission={requiredPermission}
        fallbackPath={fallbackPath}
        showAccessDenied={showAccessDenied}
      >
        <Component {...props} />
      </ProtectedRoute>
    );
  };
};

// Hook para verificar permisos en componentes
export const usePermissions = () => {
  const { hasRole, hasPermission, user } = useAuth();

  const checkAccess = (requirements = {}) => {
    const { role = null, permission = null } = requirements;

    if (role && !hasRole(role)) {
      return {
        hasAccess: false,
        reason: 'role',
        required: role,
        current: user?.role,
      };
    }

    if (permission && !hasPermission(permission)) {
      return {
        hasAccess: false,
        reason: 'permission',
        required: permission,
      };
    }

    return {
      hasAccess: true,
      reason: null,
    };
  };

  return {
    checkAccess,
    hasRole,
    hasPermission,
    user,
  };
};

export default ProtectedRoute;