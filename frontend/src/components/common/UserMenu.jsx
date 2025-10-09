import React from 'react';
import {
  Menu,
  Avatar,
  UnstyledButton,
  Group,
  Text,
  Badge,
  Divider,
  ActionIcon,
} from '@mantine/core';
import {
  IconUser,
  IconSettings,
  IconLogout,
  IconShield,
  IconCrown,
  IconEye,
  IconChevronDown,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

const UserMenu = ({ user, logout }) => {
  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <IconCrown size={14} />;
      case 'operator':
        return <IconShield size={14} />;
      case 'viewer':
        return <IconEye size={14} />;
      default:
        return <IconUser size={14} />;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'red';
      case 'operator':
        return 'blue';
      case 'viewer':
        return 'green';
      default:
        return 'gray';
    }
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name[0].toUpperCase();
  };

  return (
    <Menu shadow="md" width={250} position="bottom-end" withArrow>
      <Menu.Target>
        <UnstyledButton
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            transition: 'background-color 0.2s ease',
          }}
          sx={(theme) => ({
            '&:hover': {
              backgroundColor: theme.colors.gray[1],
            },
          })}
        >
          <Group spacing="sm">
            <Avatar
              src={user?.avatar}
              alt={user?.name}
              radius="xl"
              size="sm"
              color="blue"
            >
              {getInitials(user?.name)}
            </Avatar>
            
            <div style={{ flex: 1, minWidth: 0 }}>
              <Text size="sm" weight={500} lineClamp={1}>
                {user?.name || 'Usuario'}
              </Text>
              <Group spacing={4}>
                {getRoleIcon(user?.role)}
                <Text size="xs" color="gray.6">
                  {user?.role === 'admin' ? 'Administrador' :
                   user?.role === 'operator' ? 'Operador' : 'Visualizador'}
                </Text>
              </Group>
            </div>

            <ActionIcon size="sm" variant="subtle" color="gray">
              <IconChevronDown size={14} />
            </ActionIcon>
          </Group>
        </UnstyledButton>
      </Menu.Target>

      <Menu.Dropdown>
        {/* Header del usuario */}
        <Menu.Label>
          <Group spacing="sm" mb="xs">
            <Avatar
              src={user?.avatar}
              alt={user?.name}
              radius="xl"
              size="md"
              color="blue"
            >
              {getInitials(user?.name)}
            </Avatar>
            <div style={{ flex: 1 }}>
              <Text size="sm" weight={600}>
                {user?.name || 'Usuario'}
              </Text>
              <Text size="xs" color="gray.6">
                {user?.email}
              </Text>
              <Badge
                size="xs"
                variant="light"
                color={getRoleColor(user?.role)}
                leftIcon={getRoleIcon(user?.role)}
                mt={4}
              >
                {user?.role === 'admin' ? 'Administrador' :
                 user?.role === 'operator' ? 'Operador' : 'Visualizador'}
              </Badge>
            </div>
          </Group>
        </Menu.Label>

        <Divider />

        {/* Información de la cuenta */}
        <Menu.Label>Mi Cuenta</Menu.Label>
        
        <Menu.Item
          icon={<IconUser size={14} />}
          onClick={() => {/* navegar a perfil */}}
        >
          <div>
            <Text size="sm">Mi Perfil</Text>
            <Text size="xs" color="gray.6">
              Ver y editar información personal
            </Text>
          </div>
        </Menu.Item>

        <Menu.Item
          icon={<IconSettings size={14} />}
          onClick={() => {/* navegar a configuración */}}
        >
          <div>
            <Text size="sm">Configuración</Text>
            <Text size="xs" color="gray.6">
              Preferencias y ajustes de la cuenta
            </Text>
          </div>
        </Menu.Item>

        <Divider />

        {/* Información del sistema */}
        <Menu.Label>Sistema</Menu.Label>
        
        <Menu.Item
          disabled
          style={{ padding: '8px 12px' }}
        >
          <Group position="apart" style={{ width: '100%' }}>
            <Text size="xs" color="gray.6">
              Última conexión:
            </Text>
            <Text size="xs" color="gray.7">
              {user?.lastLogin ? new Date(user.lastLogin).toLocaleString() : 'Nunca'}
            </Text>
          </Group>
        </Menu.Item>

        <Menu.Item
          disabled
          style={{ padding: '8px 12px' }}
        >
          <Group position="apart" style={{ width: '100%' }}>
            <Text size="xs" color="gray.6">
              Documentos subidos:
            </Text>
            <Text size="xs" color="gray.7">
              {user?.documentsUploaded || 0}
            </Text>
          </Group>
        </Menu.Item>

        <Divider />

        {/* Cerrar sesión */}
        <Menu.Item
          color="red"
          icon={<IconLogout size={14} />}
          onClick={logout}
          style={{
            borderRadius: '6px',
            margin: '4px',
          }}
        >
          <motion.div
            whileHover={{ x: 2 }}
            transition={{ duration: 0.1 }}
          >
            <div>
              <Text size="sm" weight={500}>
                Cerrar Sesión
              </Text>
              <Text size="xs" color="red.6">
                Salir de SGD Web
              </Text>
            </div>
          </motion.div>
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
};

export default UserMenu;