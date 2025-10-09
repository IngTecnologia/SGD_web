import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { PublicClientApplication } from '@azure/msal-browser';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX, IconInfoCircle } from '@tabler/icons-react';

// Configuración MSAL
const msalConfig = {
  auth: {
    clientId: process.env.REACT_APP_MICROSOFT_CLIENT_ID || '',
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_MICROSOFT_TENANT_ID || 'common'}`,
    redirectUri: window.location.origin + '/login',
    postLogoutRedirectUri: window.location.origin + '/login',
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        
        switch (level) {
          case 0: // Error
            console.error('MSAL Error:', message);
            break;
          case 1: // Warning
            console.warn('MSAL Warning:', message);
            break;
          case 2: // Info
            console.info('MSAL Info:', message);
            break;
          case 3: // Verbose
            if (process.env.NODE_ENV === 'development') {
              console.log('MSAL Verbose:', message);
            }
            break;
          default:
            console.log('MSAL:', message);
        }
      },
      piiLoggingEnabled: false,
    },
    allowNativeBroker: false,
  },
};

// Scopes requeridos
const loginRequest = {
  scopes: [
    'User.Read',
    'User.ReadBasic.All',
    'Files.ReadWrite',
    'Sites.ReadWrite.All',
  ],
  prompt: 'select_account',
};

// Crear instancia MSAL
const msalInstance = new PublicClientApplication(msalConfig);

// Estados de autenticación
const authInitialState = {
  isAuthenticated: false,
  isLoading: true,
  user: null,
  accessToken: null,
  refreshToken: null,
  tokenExpiry: null,
  permissions: {
    canUpload: false,
    canGenerate: false,
    canManageTypes: false,
    canManageUsers: false,
  },
  lastActivity: null,
  sessionTimeout: 24 * 60 * 60 * 1000, // 24 horas
  error: null,
};

// Reducer para gestionar estado de autenticación
const authReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
        error: null,
      };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        tokenExpiry: action.payload.tokenExpiry,
        permissions: action.payload.permissions,
        lastActivity: new Date().toISOString(),
        error: null,
      };

    case 'LOGIN_FAILURE':
      return {
        ...authInitialState,
        isLoading: false,
        error: action.payload,
      };

    case 'LOGOUT':
      return {
        ...authInitialState,
        isLoading: false,
      };

    case 'UPDATE_TOKEN':
      return {
        ...state,
        accessToken: action.payload.accessToken,
        tokenExpiry: action.payload.tokenExpiry,
        lastActivity: new Date().toISOString(),
      };

    case 'UPDATE_USER':
      return {
        ...state,
        user: { ...state.user, ...action.payload },
        lastActivity: new Date().toISOString(),
      };

    case 'UPDATE_ACTIVITY':
      return {
        ...state,
        lastActivity: new Date().toISOString(),
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    default:
      return state;
  }
};

// Crear contexto
const AuthContext = createContext();

// Provider del contexto
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, authInitialState);

  // Inicializar MSAL
  useEffect(() => {
    const initializeMsal = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        
        await msalInstance.initialize();
        
        // Verificar si hay una sesión activa
        const accounts = msalInstance.getAllAccounts();
        
        if (accounts.length > 0) {
          // Intentar obtener token silenciosamente
          try {
            const silentRequest = {
              ...loginRequest,
              account: accounts[0],
            };
            
            const response = await msalInstance.acquireTokenSilent(silentRequest);
            await processAuthResponse(response);
          } catch (silentError) {
            console.log('Silent token acquisition failed:', silentError);
            // Si falla, el usuario necesitará autenticarse de nuevo
            dispatch({ type: 'SET_LOADING', payload: false });
          }
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        console.error('Error initializing MSAL:', error);
        dispatch({ 
          type: 'SET_ERROR', 
          payload: 'Error al inicializar sistema de autenticación'
        });
      }
    };

    initializeMsal();
  }, []);

  // Procesar respuesta de autenticación
  const processAuthResponse = async (response) => {
    try {
      const microsoftUser = await getMicrosoftUserInfo(response.accessToken);
      
      // Obtener información del usuario desde nuestro backend
      const backendResponse = await fetch(`${process.env.REACT_APP_API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${response.accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!backendResponse.ok) {
        throw new Error('Error al obtener información del usuario');
      }

      const userData = await backendResponse.json();

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: {
            ...userData,
            microsoftProfile: microsoftUser,
          },
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
          tokenExpiry: response.expiresOn,
          permissions: userData.permissions || authInitialState.permissions,
        },
      });

      showNotification({
        title: '¡Bienvenido!',
        message: `Hola ${userData.name}, has iniciado sesión correctamente`,
        color: 'green',
        icon: <IconCheck size={16} />,
      });

    } catch (error) {
      console.error('Error processing auth response:', error);
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: error.message || 'Error al procesar autenticación',
      });
      
      showNotification({
        title: 'Error de autenticación',
        message: error.message || 'No se pudo completar el inicio de sesión',
        color: 'red',
        icon: <IconX size={16} />,
      });
    }
  };

  // Obtener información del usuario de Microsoft
  const getMicrosoftUserInfo = async (accessToken) => {
    const response = await fetch('https://graph.microsoft.com/v1.0/me', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Error al obtener información del usuario de Microsoft');
    }

    return await response.json();
  };

  // Función de login
  const login = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await msalInstance.loginPopup(loginRequest);
      await processAuthResponse(response);

    } catch (error) {
      console.error('Login error:', error);
      
      let errorMessage = 'Error al iniciar sesión';
      
      if (error.errorCode === 'user_cancelled') {
        errorMessage = 'Inicio de sesión cancelado por el usuario';
      } else if (error.errorCode === 'popup_window_error') {
        errorMessage = 'Error con la ventana emergente. Por favor, permite las ventanas emergentes.';
      }

      dispatch({
        type: 'LOGIN_FAILURE',
        payload: errorMessage,
      });

      showNotification({
        title: 'Error de inicio de sesión',
        message: errorMessage,
        color: 'red',
        icon: <IconX size={16} />,
      });
    }
  };

  // Función de logout
  const logout = async () => {
    try {
      const accounts = msalInstance.getAllAccounts();
      
      if (accounts.length > 0) {
        await msalInstance.logoutPopup({
          account: accounts[0],
          postLogoutRedirectUri: window.location.origin + '/login',
        });
      }

      // Limpiar localStorage
      localStorage.removeItem('sgd-theme');
      localStorage.removeItem('sgd-user-preferences');

      dispatch({ type: 'LOGOUT' });

      showNotification({
        title: 'Sesión cerrada',
        message: 'Has cerrado sesión correctamente',
        color: 'blue',
        icon: <IconInfoCircle size={16} />,
      });

    } catch (error) {
      console.error('Logout error:', error);
      
      // Forzar logout local incluso si hay error
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Renovar token automáticamente
  const refreshToken = async () => {
    try {
      const accounts = msalInstance.getAllAccounts();
      
      if (accounts.length === 0) {
        throw new Error('No hay cuentas disponibles');
      }

      const silentRequest = {
        ...loginRequest,
        account: accounts[0],
      };

      const response = await msalInstance.acquireTokenSilent(silentRequest);
      
      dispatch({
        type: 'UPDATE_TOKEN',
        payload: {
          accessToken: response.accessToken,
          tokenExpiry: response.expiresOn,
        },
      });

      return response.accessToken;

    } catch (error) {
      console.error('Token refresh error:', error);
      
      // Si no se puede renovar, hacer logout
      await logout();
      throw error;
    }
  };

  // Verificar si el token está próximo a expirar
  const checkTokenExpiry = () => {
    if (!state.tokenExpiry || !state.accessToken) return;

    const now = new Date();
    const expiry = new Date(state.tokenExpiry);
    const timeUntilExpiry = expiry.getTime() - now.getTime();

    // Si expira en menos de 5 minutos, renovar
    if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) {
      refreshToken().catch(console.error);
    }
  };

  // Verificar expiración cada minuto
  useEffect(() => {
    if (!state.isAuthenticated) return;

    const interval = setInterval(checkTokenExpiry, 60 * 1000);
    return () => clearInterval(interval);
  }, [state.isAuthenticated, state.tokenExpiry]);

  // Verificar timeout de sesión
  useEffect(() => {
    if (!state.isAuthenticated || !state.lastActivity) return;

    const checkSessionTimeout = () => {
      const lastActivity = new Date(state.lastActivity);
      const now = new Date();
      const inactiveTime = now.getTime() - lastActivity.getTime();

      if (inactiveTime > state.sessionTimeout) {
        showNotification({
          title: 'Sesión expirada',
          message: 'Tu sesión ha expirado por inactividad',
          color: 'orange',
          icon: <IconInfoCircle size={16} />,
        });
        logout();
      }
    };

    const interval = setInterval(checkSessionTimeout, 5 * 60 * 1000); // Verificar cada 5 minutos
    return () => clearInterval(interval);
  }, [state.isAuthenticated, state.lastActivity, state.sessionTimeout]);

  // Actualizar actividad en interacciones del usuario
  const updateActivity = () => {
    if (state.isAuthenticated) {
      dispatch({ type: 'UPDATE_ACTIVITY' });
    }
  };

  // Verificar permisos
  const hasPermission = (permission) => {
    return state.permissions[permission] || false;
  };

  // Verificar rol
  const hasRole = (role) => {
    if (!state.user) return false;
    
    const userRole = state.user.role;
    
    switch (role) {
      case 'admin':
        return userRole === 'admin';
      case 'operator':
        return ['admin', 'operator'].includes(userRole);
      case 'viewer':
        return ['admin', 'operator', 'viewer'].includes(userRole);
      default:
        return false;
    }
  };

  const value = {
    ...state,
    login,
    logout,
    refreshToken,
    updateActivity,
    hasPermission,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook para usar el contexto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de AuthProvider');
  }
  return context;
};

export default AuthContext;