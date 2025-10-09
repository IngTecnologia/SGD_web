import React, { useState, useEffect } from 'react';
import {
  AppShell,
  Navbar,
  Header,
  Footer,
  Text,
  MediaQuery,
  Burger,
  Group,
  ActionIcon,
  Avatar,
  Badge,
  Box,
  Tooltip,
  Divider,
  Indicator,
} from '@mantine/core';
import {
  IconBell,
  IconMoon,
  IconSun,
  IconCrown,
  IconShield,
  IconEye,
  IconUser,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../context/ThemeContext';
import Sidebar from './Sidebar';
import Breadcrumbs from './Breadcrumbs';
import UserMenu from './UserMenu';
import NotificationCenter from './NotificationCenter';

const Layout = ({ children }) => {
  const [opened, setOpened] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const { user, logout } = useAuth();
  const { 
    colorScheme, 
    toggleColorScheme,
    customizations 
  } = useTheme();

  // Cerrar sidebar en mobile cuando cambie la ruta
  useEffect(() => {
    setOpened(false);
  }, [window.location.pathname]);

  const headerHeight = customizations.headerHeight || 60;

  return (
    <AppShell
      navbarOffsetBreakpoint="sm"
      asideOffsetBreakpoint="sm"
      navbar={
        <Navbar
          p="md"
          hiddenBreakpoint="sm"
          hidden={!opened}
          width={{ sm: 250, lg: customizations.sidebarWidth || 280 }}
          style={{
            transition: 'width 0.2s ease',
          }}
        >
          <Sidebar onClose={() => setOpened(false)} />
        </Navbar>
      }
      header={
        <HeaderComponent 
          opened={opened}
          setOpened={setOpened}
          height={headerHeight}
          user={user}
          logout={logout}
          colorScheme={colorScheme}
          toggleColorScheme={toggleColorScheme}
          showNotifications={showNotifications}
          setShowNotifications={setShowNotifications}
        />
      }
      footer={
        <Footer height={40} p="xs">
          <Group position="apart" style={{ height: '100%' }}>
            <Text size="xs" color="gray.6">
              SGD Web v1.0.0 © 2024 INEMEC SAS
            </Text>
            <Group spacing="xs">
              <Text size="xs" color="gray.6">
                Microsoft 365 Integrado
              </Text>
              <Badge size="xs" color="green" variant="dot">
                Online
              </Badge>
            </Group>
          </Group>
        </Footer>
      }
      styles={(theme) => ({
        main: {
          backgroundColor: colorScheme === 'dark' 
            ? theme.colors.dark[8] 
            : theme.colors.gray[0],
          minHeight: `calc(100vh - ${headerHeight}px - 40px)`,
          padding: theme.spacing.md,
        },
      })}
    >
      {/* Breadcrumbs */}
      <Breadcrumbs mb="md" />

      {/* Contenido principal con animaciones */}
      <motion.div
        key={window.location.pathname}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
      >
        {children}
      </motion.div>

      {/* Centro de notificaciones */}
      <NotificationCenter 
        opened={showNotifications}
        onClose={() => setShowNotifications(false)}
      />
    </AppShell>
  );
};

// Componente del Header
const HeaderComponent = ({
  opened,
  setOpened,
  height,
  user,
  logout,
  colorScheme,
  toggleColorScheme,
  showNotifications,
  setShowNotifications,
}) => {
  const [unreadNotifications, setUnreadNotifications] = useState(3);

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

  return (
    <Header height={height} p="md">
      <Group position="apart" style={{ height: '100%' }}>
        {/* Lado izquierdo - Logo y burger menu */}
        <Group>
          <MediaQuery largerThan="sm" styles={{ display: 'none' }}>
            <Burger
              opened={opened}
              onClick={() => setOpened((o) => !o)}
              size="sm"
              color="gray.6"
            />
          </MediaQuery>

          {/* Logo */}
          <Group spacing="xs">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Box
                style={{
                  width: 32,
                  height: 32,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '14px',
                }}
              >
                SGD
              </Box>
            </motion.div>
            
            <MediaQuery smallerThan="sm" styles={{ display: 'none' }}>
              <Box>
                <Text size="lg" weight={600} color="gray.8">
                  SGD Web
                </Text>
                <Text size="xs" color="gray.6" style={{ lineHeight: 1 }}>
                  Sistema de Gestión Documental
                </Text>
              </Box>
            </MediaQuery>
          </Group>
        </Group>

        {/* Lado derecho - Acciones y usuario */}
        <Group spacing="xs">
          {/* Toggle tema */}
          <Tooltip 
            label={colorScheme === 'dark' ? 'Tema claro' : 'Tema oscuro'}
            position="bottom"
          >
            <ActionIcon
              variant="light"
              color="gray"
              size="lg"
              onClick={toggleColorScheme}
              style={{
                transition: 'all 0.2s ease',
              }}
            >
              <motion.div
                initial={false}
                animate={{ rotate: colorScheme === 'dark' ? 180 : 0 }}
                transition={{ duration: 0.3 }}
              >
                {colorScheme === 'dark' ? (
                  <IconSun size={18} />
                ) : (
                  <IconMoon size={18} />
                )}
              </motion.div>
            </ActionIcon>
          </Tooltip>

          {/* Notificaciones */}
          <Tooltip label="Notificaciones" position="bottom">
            <Indicator
              inline
              label={unreadNotifications}
              size={16}
              disabled={unreadNotifications === 0}
              color="red"
            >
              <ActionIcon
                variant={showNotifications ? 'filled' : 'light'}
                color="blue"
                size="lg"
                onClick={() => setShowNotifications(!showNotifications)}
              >
                <IconBell size={18} />
              </ActionIcon>
            </Indicator>
          </Tooltip>

          <Divider orientation="vertical" />

          {/* Menu de usuario */}
          <UserMenu user={user} logout={logout} />
        </Group>
      </Group>
    </Header>
  );
};

export default Layout;