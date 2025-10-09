import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  Button,
  Stack,
  Group,
  Divider,
  Alert,
  Box,
  ThemeIcon,
  List,
  Grid,
  Badge,
} from '@mantine/core';
import {
  IconBrandMicrosoft,
  IconShield,
  IconCloud,
  IconDevices,
  IconLock,
  IconFileDatabase,
  IconAlertCircle,
  IconCheck,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';
import { showNotification } from '@mantine/notifications';

import { useAuth } from '../hooks/useAuth';
import LoadingScreen from '../components/common/LoadingScreen';

const Login = () => {
  const { login, isAuthenticated, isLoading, error } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const location = useLocation();

  // Redirigir si ya está autenticado
  if (isAuthenticated) {
    const from = location.state?.from || '/dashboard';
    return <Navigate to={from} replace />;
  }

  // Mensaje desde la redirección
  const redirectMessage = location.state?.message;

  const handleLogin = async () => {
    try {
      setIsLoggingIn(true);
      await login();
    } catch (error) {
      console.error('Error during login:', error);
      showNotification({
        title: 'Error de inicio de sesión',
        message: error.message || 'No se pudo completar el inicio de sesión',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setIsLoggingIn(false);
    }
  };

  if (isLoading || isLoggingIn) {
    return <LoadingScreen message="Iniciando sesión..." variant="auth" showDetails />;
  }

  return (
    <Box
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Elementos decorativos de fondo */}
      <motion.div
        style={{
          position: 'absolute',
          top: '10%',
          left: '10%',
          width: '200px',
          height: '200px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <motion.div
        style={{
          position: 'absolute',
          bottom: '15%',
          right: '15%',
          width: '150px',
          height: '150px',
          borderRadius: '30%',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        }}
        animate={{
          rotate: [0, 360],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <Container size="lg" style={{ position: 'relative', zIndex: 1, paddingTop: '5vh' }}>
        <Grid gutter="xl" align="center" style={{ minHeight: '90vh' }}>
          {/* Columna izquierda - Información del producto */}
          <Grid.Col xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Stack spacing="xl">
                {/* Logo y título principal */}
                <Group spacing="lg">
                  <ThemeIcon
                    size={60}
                    radius="xl"
                    variant="white"
                    style={{
                      background: 'rgba(255, 255, 255, 0.2)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                    }}
                  >
                    <IconFileDatabase size={30} color="white" />
                  </ThemeIcon>
                  <Box>
                    <Title order={1} color="white" size="3rem" weight={700}>
                      SGD Web
                    </Title>
                    <Text color="white" size="lg" opacity={0.9}>
                      Sistema de Gestión Documental
                    </Text>
                  </Box>
                </Group>

                {/* Características principales */}
                <Box>
                  <Title order={2} color="white" size="1.5rem" mb="md">
                    Gestión documental empresarial de última generación
                  </Title>
                  
                  <List
                    spacing="sm"
                    icon={
                      <ThemeIcon size={20} radius="xl" variant="white" color="white">
                        <IconCheck size={12} />
                      </ThemeIcon>
                    }
                  >
                    <List.Item>
                      <Text color="white" opacity={0.9}>
                        <strong>Integración Microsoft 365</strong> - Autenticación segura y sincronización automática
                      </Text>
                    </List.Item>
                    <List.Item>
                      <Text color="white" opacity={0.9}>
                        <strong>Códigos QR inteligentes</strong> - Generación y extracción automática
                      </Text>
                    </List.Item>
                    <List.Item>
                      <Text color="white" opacity={0.9}>
                        <strong>OneDrive Business</strong> - Almacenamiento seguro en la nube
                      </Text>
                    </List.Item>
                    <List.Item>
                      <Text color="white" opacity={0.9}>
                        <strong>Búsqueda avanzada</strong> - Encuentra documentos instantáneamente
                      </Text>
                    </List.Item>
                  </List>
                </Box>

                {/* Estadísticas */}
                <Group spacing="xl">
                  <Box style={{ textAlign: 'center' }}>
                    <Text color="white" size="2rem" weight={700}>
                      99.9%
                    </Text>
                    <Text color="white" size="sm" opacity={0.8}>
                      Disponibilidad
                    </Text>
                  </Box>
                  <Box style={{ textAlign: 'center' }}>
                    <Text color="white" size="2rem" weight={700}>
                      24/7
                    </Text>
                    <Text color="white" size="sm" opacity={0.8}>
                      Soporte
                    </Text>
                  </Box>
                  <Box style={{ textAlign: 'center' }}>
                    <Text color="white" size="2rem" weight={700}>
                      100%
                    </Text>
                    <Text color="white" size="sm" opacity={0.8}>
                      Seguro
                    </Text>
                  </Box>
                </Group>
              </Stack>
            </motion.div>
          </Grid.Col>

          {/* Columna derecha - Formulario de login */}
          <Grid.Col xs={12} md={6}>
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Paper
                p="xl"
                radius="lg"
                shadow="xl"
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                }}
              >
                <Stack spacing="xl">
                  {/* Header */}
                  <Box style={{ textAlign: 'center' }}>
                    <Title order={2} color="gray.8" mb="xs">
                      Iniciar Sesión
                    </Title>
                    <Text color="gray.6" size="sm">
                      Accede con tu cuenta corporativa de Microsoft 365
                    </Text>
                  </Box>

                  {/* Mensaje de redirección */}
                  <AnimatePresence>
                    {redirectMessage && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                      >
                        <Alert
                          icon={<IconAlertCircle size={16} />}
                          title="Acceso requerido"
                          color="blue"
                          variant="light"
                        >
                          {redirectMessage}
                        </Alert>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Error de autenticación */}
                  <AnimatePresence>
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                      >
                        <Alert
                          icon={<IconAlertCircle size={16} />}
                          title="Error de autenticación"
                          color="red"
                          variant="light"
                        >
                          {error}
                        </Alert>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Botón de login */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Button
                      leftIcon={<IconBrandMicrosoft size={20} />}
                      size="lg"
                      fullWidth
                      loading={isLoggingIn}
                      onClick={handleLogin}
                      style={{
                        background: 'linear-gradient(135deg, #0078d4 0%, #106ebe 100%)',
                        border: 'none',
                        height: '50px',
                        fontSize: '16px',
                        fontWeight: 600,
                      }}
                    >
                      {isLoggingIn ? 'Iniciando sesión...' : 'Continuar con Microsoft 365'}
                    </Button>
                  </motion.div>

                  <Divider label="Características de seguridad" labelPosition="center" />

                  {/* Características de seguridad */}
                  <Grid gutter="md">
                    <Grid.Col span={6}>
                      <Group spacing="xs">
                        <ThemeIcon size="sm" color="blue" variant="light">
                          <IconShield size={14} />
                        </ThemeIcon>
                        <Text size="xs" color="gray.6">
                          Autenticación única
                        </Text>
                      </Group>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Group spacing="xs">
                        <ThemeIcon size="sm" color="green" variant="light">
                          <IconLock size={14} />
                        </ThemeIcon>
                        <Text size="xs" color="gray.6">
                          Cifrado extremo a extremo
                        </Text>
                      </Group>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Group spacing="xs">
                        <ThemeIcon size="sm" color="orange" variant="light">
                          <IconCloud size={14} />
                        </ThemeIcon>
                        <Text size="xs" color="gray.6">
                          Respaldo automático
                        </Text>
                      </Group>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Group spacing="xs">
                        <ThemeIcon size="sm" color="violet" variant="light">
                          <IconDevices size={14} />
                        </ThemeIcon>
                        <Text size="xs" color="gray.6">
                          Acceso multiplataforma
                        </Text>
                      </Group>
                    </Grid.Col>
                  </Grid>

                  {/* Información adicional */}
                  <Box style={{ textAlign: 'center' }}>
                    <Text size="xs" color="gray.5">
                      Al iniciar sesión, aceptas nuestros términos de servicio y política de privacidad.
                      <br />
                      ¿Necesitas ayuda? Contacta a{' '}
                      <Text component="span" color="blue.6" weight={500}>
                        soporte@tuempresa.com
                      </Text>
                    </Text>
                  </Box>
                </Stack>
              </Paper>
            </motion.div>
          </Grid.Col>
        </Grid>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          style={{ textAlign: 'center', paddingBottom: '2rem' }}
        >
          <Group position="center" spacing="xl">
            <Badge variant="light" color="white" size="lg">
              SGD Web v1.0.0
            </Badge>
            <Badge variant="light" color="white" size="lg">
              INEMEC SAS © 2024
            </Badge>
            <Badge variant="light" color="white" size="lg">
              Powered by Microsoft 365
            </Badge>
          </Group>
        </motion.div>
      </Container>
    </Box>
  );
};

export default Login;