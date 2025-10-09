import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  NavLink,
  Stack,
  Group,
  Text,
  Badge,
  Divider,
  Box,
  Tooltip,
  ThemeIcon,
  ScrollArea,
  Progress,
} from '@mantine/core';
import {
  IconDashboard,
  IconFileUpload,
  IconSearch,
  IconFileText,
  IconSettings,
  IconUsers,
  IconFileDatabase,
  IconQrcode,
  IconChartLine,
  IconShield,
  IconCloudUpload,
  IconHistory,
  IconBell,
  IconHelp,
  IconExternalLink,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

import { useAuth } from '../../hooks/useAuth';

const Sidebar = ({ onClose }) => {
  const location = useLocation();
  const { user, hasRole, hasPermission } = useAuth();

  // Configuración de elementos del menú
  const menuItems = [
    {
      group: 'Principal',
      items: [
        {
          icon: IconDashboard,
          label: 'Dashboard',
          link: '/dashboard',
          color: 'blue',
          description: 'Panel principal del sistema',
          badge: null,
        },
      ],
    },
    {
      group: 'Documentos',
      items: [
        {
          icon: IconFileUpload,
          label: 'Registrar',
          link: '/register',
          color: 'green',
          description: 'Subir y registrar documentos',
          badge: null,
          requiresRole: 'operator',
        },
        {
          icon: IconSearch,
          label: 'Buscar',
          link: '/search',
          color: 'orange',
          description: 'Buscar documentos existentes',
          badge: null,
        },
        {
          icon: IconFileText,
          label: 'Generar',
          link: '/generator',
          color: 'violet',
          description: 'Generar documentos con QR',
          badge: 'Nuevo',
          requiresRole: 'operator',
        },
      ],
    },
    {
      group: 'Administración',
      items: [
        {
          icon: IconFileDatabase,
          label: 'Tipos de Documento',
          link: '/admin/document-types',
          color: 'indigo',
          description: 'Gestionar tipos de documento',
          badge: null,
          requiresRole: 'admin',
        },
        {
          icon: IconUsers,
          label: 'Usuarios',
          link: '/admin/users',
          color: 'red',
          description: 'Administrar usuarios del sistema',
          badge: null,
          requiresRole: 'admin',
        },
        {
          icon: IconQrcode,
          label: 'Códigos QR',
          link: '/admin/qr-codes',
          color: 'teal',
          description: 'Gestionar códigos QR',
          badge: null,
          requiresRole: 'admin',
        },
        {
          icon: IconChartLine,
          label: 'Estadísticas',
          link: '/admin/stats',
          color: 'pink',
          description: 'Ver estadísticas del sistema',
          badge: null,
          requiresRole: 'admin',
        },
      ],
    },
    {
      group: 'Sistema',
      items: [
        {
          icon: IconHistory,
          label: 'Actividad',
          link: '/activity',
          color: 'gray',
          description: 'Historial de actividades',
          badge: null,
        },
        {
          icon: IconBell,
          label: 'Notificaciones',
          link: '/notifications',
          color: 'yellow',
          description: 'Centro de notificaciones',
          badge: '3',
        },
        {
          icon: IconSettings,
          label: 'Configuración',
          link: '/settings',
          color: 'gray',
          description: 'Configuración personal',
          badge: null,
        },
      ],
    },
    {
      group: 'Ayuda',
      items: [
        {
          icon: IconHelp,
          label: 'Documentación',
          link: '/help',
          color: 'blue',
          description: 'Guías y documentación',
          badge: null,
        },
        {
          icon: IconExternalLink,
          label: 'Soporte',
          link: 'mailto:soporte@tuempresa.com',
          color: 'red',
          description: 'Contactar soporte técnico',
          badge: null,
          external: true,
        },
      ],
    },
  ];

  // Filtrar elementos según permisos del usuario
  const getFilteredItems = (items) => {
    return items.filter(item => {
      if (item.requiresRole && !hasRole(item.requiresRole)) {
        return false;
      }
      if (item.requiresPermission && !hasPermission(item.requiresPermission)) {
        return false;
      }
      return true;
    });
  };

  const isActive = (link) => {
    if (link === '/dashboard') {
      return location.pathname === '/' || location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(link);
  };

  return (
    <ScrollArea style={{ height: '100%' }}>
      <Stack spacing="md">
        {/* Header con información del usuario */}
        <Box p="md" style={{ borderBottom: '1px solid #e9ecef' }}>
          <Group spacing="sm">
            <ThemeIcon
              size="lg"
              radius="xl"
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan' }}
            >
              <IconShield size={20} />
            </ThemeIcon>
            <Box style={{ flex: 1 }}>
              <Text size="sm" weight={600} lineClamp={1}>
                {user?.name || 'Usuario'}
              </Text>
              <Badge
                size="xs"
                variant="light"
                color={
                  user?.role === 'admin' ? 'red' :
                  user?.role === 'operator' ? 'blue' : 'green'
                }
              >
                {user?.role === 'admin' ? 'Administrador' :
                 user?.role === 'operator' ? 'Operador' : 'Visualizador'}
              </Badge>
            </Box>
          </Group>

          {/* Indicador de almacenamiento */}
          <Box mt="md">
            <Group position="apart" mb={5}>
              <Text size="xs" color="gray.6">
                Almacenamiento
              </Text>
              <Text size="xs" color="gray.6">
                2.4 GB / 5 GB
              </Text>
            </Group>
            <Progress
              value={48}
              size="xs"
              color="blue"
              style={{ backgroundColor: '#e9ecef' }}
            />
          </Box>
        </Box>

        {/* Elementos del menú */}
        <Box px="md">
          {menuItems.map((group, groupIndex) => {
            const filteredItems = getFilteredItems(group.items);
            
            if (filteredItems.length === 0) {
              return null;
            }

            return (
              <motion.div
                key={group.group}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: groupIndex * 0.1 }}
              >
                <Box mb="md">
                  {/* Título del grupo */}
                  <Text
                    size="xs"
                    weight={600}
                    color="gray.6"
                    transform="uppercase"
                    mb="xs"
                    px="xs"
                  >
                    {group.group}
                  </Text>

                  {/* Items del grupo */}
                  <Stack spacing={2}>
                    {filteredItems.map((item, itemIndex) => {
                      const active = isActive(item.link);
                      
                      const linkProps = item.external
                        ? { 
                            component: 'a',
                            href: item.link,
                            target: '_blank',
                            rel: 'noopener noreferrer'
                          }
                        : { 
                            component: Link,
                            to: item.link,
                            onClick: onClose
                          };

                      return (
                        <motion.div
                          key={item.link}
                          whileHover={{ x: 4 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Tooltip
                            label={item.description}
                            position="right"
                            openDelay={500}
                          >
                            <NavLink
                              {...linkProps}
                              icon={
                                <ThemeIcon
                                  size="md"
                                  variant={active ? 'filled' : 'light'}
                                  color={item.color}
                                  style={{
                                    transition: 'all 0.2s ease',
                                  }}
                                >
                                  <item.icon size={16} />
                                </ThemeIcon>
                              }
                              label={
                                <Group position="apart" style={{ flex: 1 }}>
                                  <Text size="sm" weight={active ? 600 : 400}>
                                    {item.label}
                                  </Text>
                                  {item.badge && (
                                    <Badge
                                      size="xs"
                                      variant="filled"
                                      color={item.color}
                                      style={{ transform: 'scale(0.8)' }}
                                    >
                                      {item.badge}
                                    </Badge>
                                  )}
                                </Group>
                              }
                              active={active}
                              variant="light"
                              style={{
                                borderRadius: '8px',
                                marginBottom: '2px',
                                transition: 'all 0.2s ease',
                                backgroundColor: active
                                  ? `var(--mantine-color-${item.color}-1)`
                                  : 'transparent',
                              }}
                            />
                          </Tooltip>
                        </motion.div>
                      );
                    })}
                  </Stack>
                </Box>

                {groupIndex < menuItems.length - 1 && (
                  <Divider my="md" />
                )}
              </motion.div>
            );
          })}
        </Box>

        {/* Información adicional al final */}
        <Box px="md" pb="md">
          <Divider mb="md" />
          
          {/* Estado de sincronización */}
          <Group spacing="xs" mb="sm">
            <ThemeIcon size="sm" color="green" variant="light">
              <IconCloudUpload size={12} />
            </ThemeIcon>
            <Text size="xs" color="gray.6">
              OneDrive sincronizado
            </Text>
          </Group>

          {/* Última actividad */}
          <Text size="xs" color="gray.5">
            Última actividad: hace 2 minutos
          </Text>
        </Box>
      </Stack>
    </ScrollArea>
  );
};

export default Sidebar;