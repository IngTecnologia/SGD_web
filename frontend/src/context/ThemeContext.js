import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { ColorSchemeProvider, MantineProvider } from '@mantine/core';

// Estados del tema
const themeInitialState = {
  colorScheme: 'light', // 'light', 'dark', 'auto'
  primaryColor: 'blue',
  fontSize: 'md', // 'xs', 'sm', 'md', 'lg', 'xl'
  radius: 'md', // 'xs', 'sm', 'md', 'lg', 'xl'
  compact: false,
  reducedMotion: false,
  highContrast: false,
  customizations: {
    sidebarWidth: 280,
    headerHeight: 60,
    showSidebarLabels: true,
    showBreadcrumbs: true,
    showPageAnimations: true,
  },
};

// Reducer para gestionar estado del tema
const themeReducer = (state, action) => {
  switch (action.type) {
    case 'SET_COLOR_SCHEME':
      return {
        ...state,
        colorScheme: action.payload,
      };

    case 'SET_PRIMARY_COLOR':
      return {
        ...state,
        primaryColor: action.payload,
      };

    case 'SET_FONT_SIZE':
      return {
        ...state,
        fontSize: action.payload,
      };

    case 'SET_RADIUS':
      return {
        ...state,
        radius: action.payload,
      };

    case 'TOGGLE_COMPACT':
      return {
        ...state,
        compact: !state.compact,
      };

    case 'TOGGLE_REDUCED_MOTION':
      return {
        ...state,
        reducedMotion: !state.reducedMotion,
      };

    case 'TOGGLE_HIGH_CONTRAST':
      return {
        ...state,
        highContrast: !state.highContrast,
      };

    case 'UPDATE_CUSTOMIZATIONS':
      return {
        ...state,
        customizations: {
          ...state.customizations,
          ...action.payload,
        },
      };

    case 'RESET_THEME':
      return themeInitialState;

    case 'LOAD_THEME':
      return {
        ...state,
        ...action.payload,
      };

    default:
      return state;
  }
};

// Crear contexto
const ThemeContext = createContext();

// Provider del contexto
export const ThemeProvider = ({ children }) => {
  const [state, dispatch] = useReducer(themeReducer, themeInitialState);

  // Cargar tema desde localStorage al inicializar
  useEffect(() => {
    const savedTheme = localStorage.getItem('sgd-theme');
    if (savedTheme) {
      try {
        const parsedTheme = JSON.parse(savedTheme);
        dispatch({ type: 'LOAD_THEME', payload: parsedTheme });
      } catch (error) {
        console.error('Error al cargar tema guardado:', error);
      }
    } else {
      // Detectar preferencia del sistema
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const systemPrefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      
      if (systemPrefersDark) {
        dispatch({ type: 'SET_COLOR_SCHEME', payload: 'dark' });
      }
      
      if (systemPrefersReducedMotion) {
        dispatch({ type: 'TOGGLE_REDUCED_MOTION' });
      }
    }
  }, []);

  // Guardar tema en localStorage cuando cambie
  useEffect(() => {
    localStorage.setItem('sgd-theme', JSON.stringify(state));
    
    // Aplicar clase CSS al body para temas
    document.body.className = `theme-${state.colorScheme}${state.compact ? ' compact' : ''}${state.highContrast ? ' high-contrast' : ''}`;
    
    // Aplicar variables CSS customizadas
    const root = document.documentElement;
    root.style.setProperty('--sidebar-width', `${state.customizations.sidebarWidth}px`);
    root.style.setProperty('--header-height', `${state.customizations.headerHeight}px`);
    root.style.setProperty('--animation-duration', state.reducedMotion ? '0ms' : '200ms');
    
  }, [state]);

  // Escuchar cambios en preferencias del sistema
  useEffect(() => {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleColorSchemeChange = (e) => {
      if (state.colorScheme === 'auto') {
        dispatch({ 
          type: 'SET_COLOR_SCHEME', 
          payload: e.matches ? 'dark' : 'light' 
        });
      }
    };

    const handleReducedMotionChange = (e) => {
      if (e.matches !== state.reducedMotion) {
        dispatch({ type: 'TOGGLE_REDUCED_MOTION' });
      }
    };

    darkModeQuery.addEventListener('change', handleColorSchemeChange);
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange);

    return () => {
      darkModeQuery.removeEventListener('change', handleColorSchemeChange);
      reducedMotionQuery.removeEventListener('change', handleReducedMotionChange);
    };
  }, [state.colorScheme, state.reducedMotion]);

  // Funciones para cambiar tema
  const toggleColorScheme = () => {
    const schemes = ['light', 'dark', 'auto'];
    const currentIndex = schemes.indexOf(state.colorScheme);
    const nextIndex = (currentIndex + 1) % schemes.length;
    dispatch({ type: 'SET_COLOR_SCHEME', payload: schemes[nextIndex] });
  };

  const setColorScheme = (scheme) => {
    dispatch({ type: 'SET_COLOR_SCHEME', payload: scheme });
  };

  const setPrimaryColor = (color) => {
    dispatch({ type: 'SET_PRIMARY_COLOR', payload: color });
  };

  const setFontSize = (size) => {
    dispatch({ type: 'SET_FONT_SIZE', payload: size });
  };

  const setRadius = (radius) => {
    dispatch({ type: 'SET_RADIUS', payload: radius });
  };

  const toggleCompact = () => {
    dispatch({ type: 'TOGGLE_COMPACT' });
  };

  const toggleReducedMotion = () => {
    dispatch({ type: 'TOGGLE_REDUCED_MOTION' });
  };

  const toggleHighContrast = () => {
    dispatch({ type: 'TOGGLE_HIGH_CONTRAST' });
  };

  const updateCustomizations = (customizations) => {
    dispatch({ type: 'UPDATE_CUSTOMIZATIONS', payload: customizations });
  };

  const resetTheme = () => {
    dispatch({ type: 'RESET_THEME' });
    localStorage.removeItem('sgd-theme');
  };

  // Obtener tema efectivo (resolver 'auto')
  const getEffectiveColorScheme = () => {
    if (state.colorScheme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return state.colorScheme;
  };

  const value = {
    ...state,
    effectiveColorScheme: getEffectiveColorScheme(),
    toggleColorScheme,
    setColorScheme,
    setPrimaryColor,
    setFontSize,
    setRadius,
    toggleCompact,
    toggleReducedMotion,
    toggleHighContrast,
    updateCustomizations,
    resetTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook para usar el contexto
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme debe ser usado dentro de ThemeProvider');
  }
  return context;
};

export default ThemeContext;