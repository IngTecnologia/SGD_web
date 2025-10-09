import React from 'react';
import {
  Drawer,
  Title,
  Text,
  Stack,
  Group,
  ActionIcon,
  Badge,
  Paper,
  ScrollArea,
  Button,
  Divider,
  ThemeIcon,
  UnstyledButton,
} from '@mantine/core';
import {
  IconX,
  IconBell,
  IconCheck,
  IconAlertTriangle,
  IconInfo,
  IconTrash,
  IconSettings,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationCenter = ({ opened, onClose }) => {
  // Datos de ejemplo para notificaciones
  const notifications = [
    {
      id: 1,
      type: 'success',
      title: 'Documento procesado exitosamente',
      message: 'El documento "Contrato-EMP-001.pdf" ha sido procesado y almacenado en OneDrive.',
      time: 'hace 5 minutos',
      read: false,
    },
    {
      id: 2,
      type: 'info',
      title: 'Nuevo usuario registrado',
      message: 'María García se ha registrado en el sistema y requiere asignación de rol.',
      time: 'hace 15 minutos',
      read: false,
    },
    {
      id: 3,
      type: 'warning',
      title: 'Espacio de almacenamiento',
      message: 'El almacenamiento está al 85% de su capacidad. Considera limpiar archivos temporales.',
      time: 'hace 1 hora',
      read: true,
    },
    {
      id: 4,
      type: 'info',
      title: 'Sincronización completada',
      message: 'Se han sincronizado 23 documentos con OneDrive Business.',
      time: 'hace 2 horas',
      read: true,
    },
    {
      id: 5,
      type: 'success',
      title: 'Backup realizado',
      message: 'El backup automático de la base de datos se completó correctamente.',
      time: 'hace 1 día',
      read: true,
    },
  ];

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <IconCheck size={16} />;
      case 'warning':
        return <IconAlertTriangle size={16} />;
      case 'error':
        return <IconX size={16} />;
      default:
        return <IconInfo size={16} />;
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success':
        return 'green';
      case 'warning':
        return 'orange';
      case 'error':
        return 'red';
      default:
        return 'blue';
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      size="md"
      title={
        <Group position="apart" style={{ width: '100%' }}>
          <Group spacing="sm">
            <ThemeIcon size="lg" variant="light" color="blue">
              <IconBell size={20} />
            </ThemeIcon>
            <div>
              <Title order={4}>Notificaciones</Title>
              {unreadCount > 0 && (
                <Text size="sm" color="gray.6">
                  {unreadCount} sin leer
                </Text>
              )}
            </div>
          </Group>
          <Group spacing="xs">
            <ActionIcon variant="light" color="gray">
              <IconSettings size={16} />
            </ActionIcon>
            <ActionIcon variant="light" color="gray" onClick={onClose}>
              <IconX size={16} />
            </ActionIcon>
          </Group>
        </Group>
      }
      styles={{
        title: { width: '100%' },
        header: { paddingBottom: '16px', borderBottom: '1px solid #e9ecef' },
        body: { padding: 0 },
      }}
    >
      <ScrollArea style={{ height: 'calc(100vh - 120px)' }}>
        <Stack spacing={0}>
          {/* Acciones rápidas */}
          <div style={{ padding: '16px' }}>
            <Group spacing="sm">
              <Button
                variant="light"
                size="xs"
                leftIcon={<IconCheck size={14} />}
                disabled={unreadCount === 0}
              >
                Marcar todas como leídas
              </Button>
              <Button
                variant="light"
                size="xs"
                color="red"
                leftIcon={<IconTrash size={14} />}
              >
                Limpiar notificaciones
              </Button>
            </Group>
          </div>

          <Divider />

          {/* Lista de notificaciones */}
          <AnimatePresence>
            {notifications.map((notification, index) => (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ delay: index * 0.05 }}
              >
                <UnstyledButton
                  style={{
                    width: '100%',
                    padding: '16px',
                    borderBottom: '1px solid #f1f3f4',
                    backgroundColor: notification.read ? 'transparent' : '#f8f9fa',
                    transition: 'background-color 0.2s ease',
                  }}
                  sx={(theme) => ({
                    '&:hover': {
                      backgroundColor: theme.colors.blue[0],
                    },
                  })}
                >
                  <Group spacing="md" align="flex-start">
                    <ThemeIcon
                      size="md"
                      variant="light"
                      color={getNotificationColor(notification.type)}
                      style={{ marginTop: '4px' }}
                    >
                      {getNotificationIcon(notification.type)}
                    </ThemeIcon>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Group position="apart" align="flex-start" mb="xs">
                        <Text
                          size="sm"
                          weight={notification.read ? 400 : 600}
                          lineClamp={1}
                          style={{ flex: 1 }}
                        >
                          {notification.title}
                        </Text>
                        {!notification.read && (
                          <Badge size="xs" color="blue" variant="filled">
                            Nuevo
                          </Badge>
                        )}
                      </Group>

                      <Text
                        size="xs"
                        color="gray.6"
                        lineClamp={2}
                        mb="xs"
                      >
                        {notification.message}
                      </Text>

                      <Text size="xs" color="gray.5">
                        {notification.time}
                      </Text>
                    </div>

                    <ActionIcon
                      size="sm"
                      variant="subtle"
                      color="gray"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Aquí eliminar notificación
                      }}
                    >
                      <IconX size={12} />
                    </ActionIcon>
                  </Group>
                </UnstyledButton>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Estado vacío */}
          {notifications.length === 0 && (
            <div style={{ padding: '40px 16px', textAlign: 'center' }}>
              <ThemeIcon
                size="xl"
                variant="light"
                color="gray"
                style={{ margin: '0 auto 16px' }}
              >
                <IconBell size={24} />
              </ThemeIcon>
              <Text size="lg" weight={500} color="gray.7" mb="xs">
                No hay notificaciones
              </Text>
              <Text size="sm" color="gray.5">
                Te notificaremos cuando haya algo nuevo
              </Text>
            </div>
          )}

          {/* Configuración de notificaciones */}
          <Divider />
          <div style={{ padding: '16px' }}>
            <Paper p="md" radius="md" withBorder>
              <Group spacing="sm" mb="sm">
                <ThemeIcon size="sm" variant="light" color="blue">
                  <IconSettings size={14} />
                </ThemeIcon>
                <Text size="sm" weight={500}>
                  Configurar Notificaciones
                </Text>
              </Group>
              <Text size="xs" color="gray.6" mb="md">
                Personaliza qué notificaciones quieres recibir y cómo recibirlas.
              </Text>
              <Button variant="light" size="xs" fullWidth>
                Abrir configuración
              </Button>
            </Paper>
          </div>
        </Stack>
      </ScrollArea>
    </Drawer>
  );
};

export default NotificationCenter;