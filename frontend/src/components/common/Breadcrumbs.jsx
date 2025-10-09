import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Breadcrumbs, Anchor, Text } from '@mantine/core';
import { IconHome, IconChevronRight } from '@tabler/icons-react';

const AppBreadcrumbs = ({ ...props }) => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Mapeo de rutas a nombres amigables
  const routeNames = {
    dashboard: 'Dashboard',
    register: 'Registrar Documentos',
    search: 'Buscar Documentos',
    generator: 'Generar Documentos',
    admin: 'Administración',
    'document-types': 'Tipos de Documento',
    users: 'Usuarios',
    'qr-codes': 'Códigos QR',
    stats: 'Estadísticas',
    activity: 'Actividad',
    notifications: 'Notificaciones',
    settings: 'Configuración',
    help: 'Ayuda',
  };

  if (pathnames.length === 0 || (pathnames.length === 1 && pathnames[0] === 'dashboard')) {
    return null;
  }

  const breadcrumbItems = [
    <Anchor component={Link} to="/dashboard" key="home">
      <IconHome size={16} />
    </Anchor>
  ];

  pathnames.forEach((name, index) => {
    const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
    const isLast = index === pathnames.length - 1;
    const displayName = routeNames[name] || name.charAt(0).toUpperCase() + name.slice(1);

    if (isLast) {
      breadcrumbItems.push(
        <Text key={name} size="sm" color="gray.7">
          {displayName}
        </Text>
      );
    } else {
      breadcrumbItems.push(
        <Anchor component={Link} to={routeTo} key={name} size="sm">
          {displayName}
        </Anchor>
      );
    }
  });

  return (
    <Breadcrumbs separator={<IconChevronRight size={14} />} {...props}>
      {breadcrumbItems}
    </Breadcrumbs>
  );
};

export default AppBreadcrumbs;