import React from 'react';
import {
  Container,
  Paper,
  Stack,
  Text,
  Progress,
  ThemeIcon,
  Group,
  Loader,
  Box,
} from '@mantine/core';
import { IconFileDatabase, IconCloud, IconShield } from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';

const LoadingScreen = ({ 
  message = 'Cargando...', 
  progress = null,
  showDetails = false,
  variant = 'default' // 'default', 'auth', 'upload', 'processing'
}) => {
  
  const getIcon = () => {
    switch (variant) {
      case 'auth':
        return <IconShield size={32} />;
      case 'upload':
        return <IconCloud size={32} />;
      case 'processing':
        return <IconFileDatabase size={32} />;
      default:
        return <Loader size={32} />;
    }
  };

  const getColor = () => {
    switch (variant) {
      case 'auth':
        return 'blue';
      case 'upload':
        return 'green';
      case 'processing':
        return 'orange';
      default:
        return 'blue';
    }
  };

  const getSubtext = () => {
    switch (variant) {
      case 'auth':
        return 'Verificando credenciales con Microsoft 365...';
      case 'upload':
        return 'Sincronizando archivos con OneDrive...';
      case 'processing':
        return 'Procesando documentos y códigos QR...';
      default:
        return 'Preparando la aplicación...';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Container size="xs">
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          transition={{ 
            duration: 0.5,
            type: "spring",
            stiffness: 300,
            damping: 20
          }}
        >
          <Paper
            p="xl"
            radius="lg"
            shadow="xl"
            withBorder
            style={{
              textAlign: 'center',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
            }}
          >
            <Stack spacing="lg" align="center">
              {/* Logo/Icono principal */}
              <motion.div
                animate={{ rotate: variant === 'default' ? 360 : 0 }}
                transition={{ 
                  duration: 2, 
                  repeat: variant === 'default' ? Infinity : 0,
                  ease: "linear" 
                }}
              >
                <ThemeIcon
                  size={64}
                  radius="xl"
                  variant="light"
                  color={getColor()}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                  }}
                >
                  {getIcon()}
                </ThemeIcon>
              </motion.div>

              {/* Título de la aplicación */}
              <Box>
                <Text
                  size="xl"
                  weight={600}
                  mb={4}
                  style={{
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  SGD Web
                </Text>
                <Text
                  size="sm"
                  opacity={0.9}
                  style={{
                    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  Sistema de Gestión Documental
                </Text>
              </Box>

              {/* Mensaje de carga */}
              <Stack spacing="xs" style={{ width: '100%' }}>
                <Text size="md" weight={500}>
                  {message}
                </Text>
                
                {showDetails && (
                  <Text size="sm" opacity={0.8}>
                    {getSubtext()}
                  </Text>
                )}

                {/* Barra de progreso */}
                {progress !== null ? (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    style={{ width: '100%' }}
                  >
                    <Progress
                      value={progress}
                      size="md"
                      radius="xl"
                      style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      }}
                      styles={{
                        bar: {
                          background: 'linear-gradient(90deg, #4facfe 0%, #00f2fe 100%)',
                        },
                      }}
                    />
                    <Text size="xs" mt={4} opacity={0.8}>
                      {Math.round(progress)}% completado
                    </Text>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Progress
                      size="md"
                      radius="xl"
                      style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      }}
                      styles={{
                        bar: {
                          background: 'linear-gradient(90deg, #4facfe 0%, #00f2fe 100%)',
                        },
                      }}
                    />
                  </motion.div>
                )}
              </Stack>

              {/* Indicadores de funcionalidades */}
              {showDetails && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  style={{ width: '100%' }}
                >
                  <Group position="center" spacing="xl" mt="md">
                    <Stack spacing={4} align="center">
                      <ThemeIcon
                        size={24}
                        radius="xl"
                        variant="light"
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.2)',
                          color: 'white',
                        }}
                      >
                        <IconShield size={14} />
                      </ThemeIcon>
                      <Text size="xs" opacity={0.8}>
                        Seguro
                      </Text>
                    </Stack>

                    <Stack spacing={4} align="center">
                      <ThemeIcon
                        size={24}
                        radius="xl"
                        variant="light"
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.2)',
                          color: 'white',
                        }}
                      >
                        <IconCloud size={14} />
                      </ThemeIcon>
                      <Text size="xs" opacity={0.8}>
                        En la nube
                      </Text>
                    </Stack>

                    <Stack spacing={4} align="center">
                      <ThemeIcon
                        size={24}
                        radius="xl"
                        variant="light"
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.2)',
                          color: 'white',
                        }}
                      >
                        <IconFileDatabase size={14} />
                      </ThemeIcon>
                      <Text size="xs" opacity={0.8}>
                        Inteligente
                      </Text>
                    </Stack>
                  </Group>
                </motion.div>
              )}
            </Stack>
          </Paper>
        </motion.div>

        {/* Mensaje adicional en la parte inferior */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          <Text
            size="xs"
            color="gray.6"
            align="center"
            mt="lg"
            style={{
              textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
            }}
          >
            SGD Web v1.0.0 • Powered by Microsoft 365
          </Text>
        </motion.div>
      </Container>
    </motion.div>
  );
};

// Componente de loading simple para usar en componentes más pequeños
export const SimpleLoader = ({ 
  size = 'md', 
  color = 'blue',
  message = 'Cargando...',
  centered = true
}) => {
  const content = (
    <Stack spacing="xs" align="center">
      <Loader size={size} color={color} />
      {message && (
        <Text size="sm" color="gray.6">
          {message}
        </Text>
      )}
    </Stack>
  );

  if (centered) {
    return (
      <Box
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '200px',
          width: '100%',
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

// Componente de loading para overlay
export const LoadingOverlay = ({ 
  visible = true, 
  message = 'Procesando...',
  variant = 'default'
}) => {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            borderRadius: '8px',
          }}
        >
          <Stack spacing="md" align="center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <Loader size="lg" color="blue" />
            </motion.div>
            <Text size="sm" color="gray.7" weight={500}>
              {message}
            </Text>
          </Stack>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LoadingScreen;