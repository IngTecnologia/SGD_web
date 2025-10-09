import React from 'react';
import {
  Container,
  Title,
  Text,
  Button,
  Group,
  Stack,
  ThemeIcon,
  Paper,
  Grid,
  Card,
  Anchor,
  Center,
  Box,
} from '@mantine/core';
import {
  IconError404,
  IconHome,
  IconArrowLeft,
  IconSearch,
  IconFileText,
  IconQrcode,
  IconUsers,
  IconSettings,
  IconHeadphones,
} from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';

const NotFound = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const goBack = () => {
    navigate(-1);
  };

  const goHome = () => {
    navigate('/dashboard');
  };

  const quickLinks = [
    {
      title: 'Dashboard',
      description: 'Panel principal del sistema',
      icon: IconHome,
      link: '/dashboard',
      color: 'blue',
    },
    {
      title: 'Buscar Documentos',
      description: 'Encuentra documentos en el sistema',
      icon: IconSearch,
      link: '/search',
      color: 'green',
    },
    {
      title: 'Registrar Documentos',
      description: 'Sube nuevos documentos',
      icon: IconFileText,
      link: '/register',
      color: 'orange',
      requiresRole: 'operator',
    },
    {
      title: 'Generar Documentos',
      description: 'Crear plantillas y códigos QR',
      icon: IconQrcode,
      link: '/generator',
      color: 'violet',
      requiresRole: 'operator',
    },
    {
      title: 'Administración',
      description: 'Panel de administración',
      icon: IconUsers,
      link: '/admin',
      color: 'red',
      requiresRole: 'admin',
    },
  ];

  const filteredLinks = quickLinks.filter(link => {
    if (!link.requiresRole) return true;
    if (link.requiresRole === 'admin') return user?.role === 'admin';
    if (link.requiresRole === 'operator') return user?.role === 'admin' || user?.role === 'operator';
    return true;
  });

  return (
    <Container size="lg">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Center style={{ minHeight: '60vh' }}>
          <Stack spacing="xl" style={{ textAlign: 'center', maxWidth: 600 }}>
            {/* 404 Illustration */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <ThemeIcon
                size={120}
                radius="xl"
                variant="light"
                color="blue"
                style={{ margin: '0 auto' }}
              >
                <IconError404 size={60} />
              </ThemeIcon>
            </motion.div>

            {/* Error Message */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              <Title order={1} size="h1" mb="sm">
                Página no encontrada
              </Title>
              <Text size="lg" color="gray.6" mb="xl">
                Lo sentimos, la página que estás buscando no existe o ha sido movida.
                Verifica la URL o navega a una de las secciones disponibles.
              </Text>
            </motion.div>

            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              <Group position="center" spacing="md">
                <Button
                  leftIcon={<IconArrowLeft size={16} />}
                  variant="light"
                  onClick={goBack}
                  size="md"
                >
                  Volver atrás
                </Button>
                <Button
                  leftIcon={<IconHome size={16} />}
                  onClick={goHome}
                  size="md"
                >
                  Ir al Dashboard
                </Button>
              </Group>
            </motion.div>
          </Stack>
        </Center>

        {/* Quick Links Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
        >
          <Paper p="xl" radius="lg" withBorder mt="xl">
            <Stack spacing="lg">
              <div style={{ textAlign: 'center' }}>
                <Title order={2} size="h3" mb="sm">
                  ¿A dónde quieres ir?
                </Title>
                <Text color="gray.6">
                  Explora las diferentes secciones del Sistema de Gestión Documental
                </Text>
              </div>

              <Grid>
                {filteredLinks.map((link, index) => (
                  <Grid.Col key={link.title} xs={12} sm={6} md={4}>
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1 + index * 0.1, duration: 0.4 }}
                    >
                      <Card
                        component={Link}
                        to={link.link}
                        p="lg"
                        radius="md"
                        withBorder
                        style={{
                          height: '100%',
                          textDecoration: 'none',
                          color: 'inherit',
                          transition: 'all 0.2s ease',
                          cursor: 'pointer',
                        }}
                        sx={(theme) => ({
                          '&:hover': {
                            backgroundColor: theme.colors.gray[0],
                            transform: 'translateY(-2px)',
                            boxShadow: theme.shadows.lg,
                          },
                        })}
                      >
                        <Group spacing="md" mb="sm">
                          <ThemeIcon
                            size="lg"
                            radius="md"
                            variant="light"
                            color={link.color}
                          >
                            <link.icon size={20} />
                          </ThemeIcon>
                          <div style={{ flex: 1 }}>
                            <Text size="sm" weight={600} mb={4}>
                              {link.title}
                            </Text>
                            <Text size="xs" color="gray.6">
                              {link.description}
                            </Text>
                          </div>
                        </Group>
                      </Card>
                    </motion.div>
                  </Grid.Col>
                ))}
              </Grid>
            </Stack>
          </Paper>
        </motion.div>

        {/* Help Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.5 }}
        >
          <Paper p="lg" radius="md" withBorder mt="xl">
            <Grid>
              <Grid.Col xs={12} md={6}>
                <Group spacing="md">
                  <ThemeIcon size="lg" variant="light" color="blue">
                    <IconHeadphones size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="sm" weight={500} mb="xs">
                      ¿Necesitas ayuda?
                    </Text>
                    <Text size="xs" color="gray.6">
                      Si el problema persiste, contacta con el administrador del sistema
                      o consulta la documentación de ayuda.
                    </Text>
                  </div>
                </Group>
              </Grid.Col>
              <Grid.Col xs={12} md={6}>
                <Group spacing="md">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconSettings size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="sm" weight={500} mb="xs">
                      Información del sistema
                    </Text>
                    <Text size="xs" color="gray.6">
                      SGD Web v1.0 - Sistema de Gestión Documental.
                      Todos los servicios funcionando correctamente.
                    </Text>
                  </div>
                </Group>
              </Grid.Col>
            </Grid>
          </Paper>
        </motion.div>

        {/* Error Details (Development) */}
        {process.env.NODE_ENV === 'development' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.4, duration: 0.5 }}
          >
            <Paper p="lg" radius="md" withBorder mt="xl" style={{ backgroundColor: '#f8f9fa' }}>
              <Stack spacing="sm">
                <Text size="sm" weight={500} color="gray.7">
                  Información de desarrollo
                </Text>
                <Text size="xs" color="gray.6">
                  URL solicitada: {window.location.pathname}
                </Text>
                <Text size="xs" color="gray.6">
                  Usuario: {user?.name || 'No autenticado'}
                </Text>
                <Text size="xs" color="gray.6">
                  Rol: {user?.role || 'N/A'}
                </Text>
                <Text size="xs" color="gray.6">
                  Timestamp: {new Date().toISOString()}
                </Text>
              </Stack>
            </Paper>
          </motion.div>
        )}
      </motion.div>
    </Container>
  );
};

export default NotFound;