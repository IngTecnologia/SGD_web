import React, { useState } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Button,
  Tabs,
  Table,
  Avatar,
  Badge,
  ActionIcon,
  Modal,
  TextInput,
  Select,
  Switch,
  Card,
  Grid,
  Divider,
  Progress,
  RingProgress,
  Center,
  Alert,
  Timeline,
  ThemeIcon,
  Menu,
  ScrollArea,
  NumberInput,
  Textarea,
  FileInput,
  Notification,
  JsonInput,
  Code,
  Tooltip,
} from '@mantine/core';
import {
  IconUsers,
  IconFileText,
  IconSettings,
  IconChartBar,
  IconDatabase,
  IconShield,
  IconPlus,
  IconEdit,
  IconTrash,
  IconEye,
  IconDownload,
  IconUpload,
  IconRefresh,
  IconCheck,
  IconX,
  IconCrown,
  IconUser,
  IconAlertTriangle,
  IconInfoCircle,
  IconCloudUpload,
  IconServer,
  IconCloud,
  IconKey,
  IconLock,
  IconMail,
  IconPhone,
  IconCalendar,
  IconClock,
  IconActivity,
  IconTrendingUp,
  IconTrendingDown,
  IconDots,
  IconSearch,
  IconFilter,
  IconExport,
  IconImport,
  IconBell,
  IconPalette,
  IconLanguage,
  IconGlobe,
  IconSecurity,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';

const Admin = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [userModalOpened, setUserModalOpened] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [settingsModalOpened, setSettingsModalOpened] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data para usuarios
  const users = [
    {
      id: 1,
      name: 'Mar�a Garc�a',
      email: 'maria.garcia@empresa.com',
      role: 'operator',
      status: 'active',
      lastLogin: '2024-01-20T10:30:00',
      documentsUploaded: 45,
      avatar: null,
      department: 'Recursos Humanos',
      phone: '+34 612 345 678',
      joinDate: '2023-06-15',
    },
    {
      id: 2,
      name: 'Carlos Ruiz',
      email: 'carlos.ruiz@empresa.com',
      role: 'admin',
      status: 'active',
      lastLogin: '2024-01-21T14:15:00',
      documentsUploaded: 128,
      avatar: null,
      department: 'Tecnolog�a',
      phone: '+34 634 567 890',
      joinDate: '2023-03-10',
    },
    {
      id: 3,
      name: 'Ana L�pez',
      email: 'ana.lopez@empresa.com',
      role: 'viewer',
      status: 'inactive',
      lastLogin: '2024-01-18T09:45:00',
      documentsUploaded: 12,
      avatar: null,
      department: 'Finanzas',
      phone: '+34 656 789 012',
      joinDate: '2023-08-22',
    },
  ];

  const systemStats = {
    totalUsers: 23,
    activeUsers: 18,
    totalDocuments: 1234,
    storageUsed: 2.4,
    storageTotal: 5.0,
    backupStatus: 'success',
    lastBackup: '2024-01-21T02:00:00',
    systemUptime: '99.9%',
    avgResponseTime: '120ms',
  };

  const recentActivity = [
    {
      id: 1,
      type: 'user_created',
      user: 'Admin',
      description: 'Nuevo usuario creado: Pedro Mart�n',
      timestamp: '2024-01-21T15:30:00',
      severity: 'info',
    },
    {
      id: 2,
      type: 'document_uploaded',
      user: 'Mar�a Garc�a',
      description: 'Documento subido: Contrato-EMP-045.pdf',
      timestamp: '2024-01-21T14:20:00',
      severity: 'success',
    },
    {
      id: 3,
      type: 'system_backup',
      user: 'Sistema',
      description: 'Backup autom�tico completado',
      timestamp: '2024-01-21T02:00:00',
      severity: 'success',
    },
    {
      id: 4,
      type: 'login_failed',
      user: 'Sistema',
      description: 'Intento de login fallido para: user@invalid.com',
      timestamp: '2024-01-21T01:15:00',
      severity: 'warning',
    },
  ];

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <IconCrown size={16} />;
      case 'operator':
        return <IconShield size={16} />;
      case 'viewer':
        return <IconUser size={16} />;
      default:
        return <IconUser size={16} />;
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'inactive':
        return 'gray';
      case 'suspended':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'user_created':
        return <IconUsers size={16} />;
      case 'document_uploaded':
        return <IconFileText size={16} />;
      case 'system_backup':
        return <IconDatabase size={16} />;
      case 'login_failed':
        return <IconAlertTriangle size={16} />;
      default:
        return <IconActivity size={16} />;
    }
  };

  const getActivityColor = (severity) => {
    switch (severity) {
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

  const openUserModal = (user = null) => {
    setSelectedUser(user);
    setUserModalOpened(true);
  };

  const closeUserModal = () => {
    setSelectedUser(null);
    setUserModalOpened(false);
  };

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Container size="xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Stack spacing="xl">
          {/* Header */}
          <Paper p="lg" radius="md" withBorder>
            <Group position="apart">
              <div>
                <Title order={1} size="h2" mb="xs">
                  Panel de Administraci�n
                </Title>
                <Text color="gray.6" size="lg">
                  Gesti�n completa del sistema SGD Web
                </Text>
              </div>
              <Badge size="lg" variant="light" color="red" leftIcon={<IconCrown size={16} />}>
                Administrador
              </Badge>
            </Group>
          </Paper>

          {/* Quick Stats */}
          <Grid>
            <Grid.Col xs={12} sm={6} md={3}>
              <Card p="md" radius="md" withBorder>
                <Group spacing="sm">
                  <ThemeIcon size="lg" variant="light" color="blue">
                    <IconUsers size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                      Usuarios Totales
                    </Text>
                    <Text size="xl" weight={700}>
                      {systemStats.totalUsers}
                    </Text>
                    <Text size="xs" color="green">
                      {systemStats.activeUsers} activos
                    </Text>
                  </div>
                </Group>
              </Card>
            </Grid.Col>
            <Grid.Col xs={12} sm={6} md={3}>
              <Card p="md" radius="md" withBorder>
                <Group spacing="sm">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconFileText size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                      Documentos
                    </Text>
                    <Text size="xl" weight={700}>
                      {systemStats.totalDocuments.toLocaleString()}
                    </Text>
                    <Text size="xs" color="blue">
                      +34 este mes
                    </Text>
                  </div>
                </Group>
              </Card>
            </Grid.Col>
            <Grid.Col xs={12} sm={6} md={3}>
              <Card p="md" radius="md" withBorder>
                <Group spacing="sm">
                  <ThemeIcon size="lg" variant="light" color="orange">
                    <IconDatabase size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                      Almacenamiento
                    </Text>
                    <Text size="xl" weight={700}>
                      {systemStats.storageUsed} GB
                    </Text>
                    <Text size="xs" color="gray.6">
                      de {systemStats.storageTotal} GB
                    </Text>
                  </div>
                </Group>
              </Card>
            </Grid.Col>
            <Grid.Col xs={12} sm={6} md={3}>
              <Card p="md" radius="md" withBorder>
                <Group spacing="sm">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconServer size={20} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                      Uptime
                    </Text>
                    <Text size="xl" weight={700}>
                      {systemStats.systemUptime}
                    </Text>
                    <Text size="xs" color="green">
                      {systemStats.avgResponseTime}
                    </Text>
                  </div>
                </Group>
              </Card>
            </Grid.Col>
          </Grid>

          {/* Main Tabs */}
          <Tabs value={activeTab} onTabChange={setActiveTab}>
            <Tabs.List>
              <Tabs.Tab value="users" icon={<IconUsers size={16} />}>
                Usuarios
              </Tabs.Tab>
              <Tabs.Tab value="documents" icon={<IconFileText size={16} />}>
                Documentos
              </Tabs.Tab>
              <Tabs.Tab value="system" icon={<IconSettings size={16} />}>
                Sistema
              </Tabs.Tab>
              <Tabs.Tab value="analytics" icon={<IconChartBar size={16} />}>
                Anal�ticas
              </Tabs.Tab>
              <Tabs.Tab value="security" icon={<IconShield size={16} />}>
                Seguridad
              </Tabs.Tab>
            </Tabs.List>

            {/* Users Tab */}
            <Tabs.Panel value="users" pt="md">
              <Stack spacing="md">
                <Paper p="lg" radius="md" withBorder>
                  <Group position="apart" mb="md">
                    <Title order={3}>
                      Gesti�n de Usuarios
                    </Title>
                    <Group spacing="sm">
                      <TextInput
                        placeholder="Buscar usuarios..."
                        icon={<IconSearch size={16} />}
                        value={searchQuery}
                        onChange={(event) => setSearchQuery(event.target.value)}
                        style={{ minWidth: 250 }}
                      />
                      <Button
                        leftIcon={<IconPlus size={16} />}
                        onClick={() => openUserModal()}
                      >
                        Nuevo Usuario
                      </Button>
                    </Group>
                  </Group>

                  <ScrollArea>
                    <Table highlightOnHover>
                      <thead>
                        <tr>
                          <th>Usuario</th>
                          <th>Rol</th>
                          <th>Estado</th>
                          <th>Departamento</th>
                          <th>�ltimo acceso</th>
                          <th>Documentos</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredUsers.map((user) => (
                          <tr key={user.id}>
                            <td>
                              <Group spacing="sm">
                                <Avatar src={user.avatar} radius="xl" size="sm">
                                  {user.name.split(' ').map(n => n[0]).join('')}
                                </Avatar>
                                <div>
                                  <Text size="sm" weight={500}>
                                    {user.name}
                                  </Text>
                                  <Text size="xs" color="gray.6">
                                    {user.email}
                                  </Text>
                                </div>
                              </Group>
                            </td>
                            <td>
                              <Badge
                                size="sm"
                                color={getRoleColor(user.role)}
                                leftIcon={getRoleIcon(user.role)}
                              >
                                {user.role === 'admin' ? 'Administrador' :
                                 user.role === 'operator' ? 'Operador' : 'Visualizador'}
                              </Badge>
                            </td>
                            <td>
                              <Badge
                                size="sm"
                                color={getStatusColor(user.status)}
                                variant="light"
                              >
                                {user.status === 'active' ? 'Activo' : 'Inactivo'}
                              </Badge>
                            </td>
                            <td>
                              <Text size="sm">{user.department}</Text>
                            </td>
                            <td>
                              <Text size="sm">
                                {new Date(user.lastLogin).toLocaleDateString()}
                              </Text>
                            </td>
                            <td>
                              <Text size="sm">{user.documentsUploaded}</Text>
                            </td>
                            <td>
                              <Group spacing="xs">
                                <Tooltip label="Ver perfil">
                                  <ActionIcon
                                    variant="subtle"
                                    size="sm"
                                    onClick={() => openUserModal(user)}
                                  >
                                    <IconEye size={16} />
                                  </ActionIcon>
                                </Tooltip>
                                <Menu shadow="md" width={200}>
                                  <Menu.Target>
                                    <ActionIcon variant="subtle" size="sm">
                                      <IconDots size={16} />
                                    </ActionIcon>
                                  </Menu.Target>
                                  <Menu.Dropdown>
                                    <Menu.Item icon={<IconEdit size={14} />}>
                                      Editar usuario
                                    </Menu.Item>
                                    <Menu.Item icon={<IconKey size={14} />}>
                                      Resetear contrase�a
                                    </Menu.Item>
                                    <Menu.Item
                                      icon={<IconLock size={14} />}
                                      color={user.status === 'active' ? 'orange' : 'green'}
                                    >
                                      {user.status === 'active' ? 'Suspender' : 'Activar'}
                                    </Menu.Item>
                                    <Menu.Divider />
                                    <Menu.Item icon={<IconTrash size={14} />} color="red">
                                      Eliminar usuario
                                    </Menu.Item>
                                  </Menu.Dropdown>
                                </Menu>
                              </Group>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </ScrollArea>
                </Paper>

                {/* Recent Activity */}
                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Actividad Reciente
                  </Title>
                  <Timeline active={recentActivity.length} bulletSize={24} lineWidth={2}>
                    {recentActivity.map((activity) => (
                      <Timeline.Item
                        key={activity.id}
                        bullet={
                          <ThemeIcon
                            size="sm"
                            variant="light"
                            color={getActivityColor(activity.severity)}
                          >
                            {getActivityIcon(activity.type)}
                          </ThemeIcon>
                        }
                        title={activity.description}
                      >
                        <Text color="gray.6" size="sm">
                          {activity.user} " {new Date(activity.timestamp).toLocaleString()}
                        </Text>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                </Paper>
              </Stack>
            </Tabs.Panel>

            {/* Documents Tab */}
            <Tabs.Panel value="documents" pt="md">
              <Stack spacing="md">
                <Paper p="lg" radius="md" withBorder>
                  <Title order={3} mb="md">
                    Gesti�n de Documentos
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="blue">
                            <IconFileText size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Estad�sticas de Documentos
                            </Text>
                            <Text size="xs" color="gray.6">
                              Resumen del sistema
                            </Text>
                          </div>
                        </Group>
                        <Stack spacing="xs">
                          <Group position="apart">
                            <Text size="sm">Total de documentos:</Text>
                            <Text size="sm" weight={500}>1,234</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Documentos activos:</Text>
                            <Text size="sm" weight={500}>1,187</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Archivados:</Text>
                            <Text size="sm" weight={500}>47</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">C�digos QR generados:</Text>
                            <Text size="sm" weight={500}>892</Text>
                          </Group>
                        </Stack>
                      </Card>
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="orange">
                            <IconDatabase size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Uso de Almacenamiento
                            </Text>
                            <Text size="xs" color="gray.6">
                              OneDrive Business
                            </Text>
                          </div>
                        </Group>
                        <Center>
                          <RingProgress
                            size={120}
                            thickness={12}
                            label={
                              <Text size="xs" align="center">
                                {((systemStats.storageUsed / systemStats.storageTotal) * 100).toFixed(1)}%
                              </Text>
                            }
                            sections={[
                              { value: (systemStats.storageUsed / systemStats.storageTotal) * 100, color: 'orange' },
                            ]}
                          />
                        </Center>
                        <Text size="sm" align="center" mt="sm">
                          {systemStats.storageUsed} GB de {systemStats.storageTotal} GB utilizados
                        </Text>
                      </Card>
                    </Grid.Col>
                  </Grid>
                </Paper>

                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Herramientas de Gesti�n
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} sm={6} md={3}>
                      <Button
                        variant="light"
                        leftIcon={<IconDownload size={16} />}
                        fullWidth
                      >
                        Exportar Datos
                      </Button>
                    </Grid.Col>
                    <Grid.Col xs={12} sm={6} md={3}>
                      <Button
                        variant="light"
                        leftIcon={<IconUpload size={16} />}
                        fullWidth
                      >
                        Importar Datos
                      </Button>
                    </Grid.Col>
                    <Grid.Col xs={12} sm={6} md={3}>
                      <Button
                        variant="light"
                        leftIcon={<IconDatabase size={16} />}
                        fullWidth
                      >
                        Crear Backup
                      </Button>
                    </Grid.Col>
                    <Grid.Col xs={12} sm={6} md={3}>
                      <Button
                        variant="light"
                        leftIcon={<IconUpload size={16} />}
                        fullWidth
                      >
                        Restaurar Backup
                      </Button>
                    </Grid.Col>
                  </Grid>
                </Paper>
              </Stack>
            </Tabs.Panel>

            {/* System Tab */}
            <Tabs.Panel value="system" pt="md">
              <Stack spacing="md">
                <Paper p="lg" radius="md" withBorder>
                  <Group position="apart" mb="md">
                    <Title order={3}>
                      Configuraci�n del Sistema
                    </Title>
                    <Button
                      leftIcon={<IconSettings size={16} />}
                      onClick={() => setSettingsModalOpened(true)}
                    >
                      Configuraci�n Avanzada
                    </Button>
                  </Group>

                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="blue">
                            <IconCloud size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Microsoft 365 Integration
                            </Text>
                            <Badge size="sm" color="green">Conectado</Badge>
                          </div>
                        </Group>
                        <Stack spacing="xs">
                          <Group position="apart">
                            <Text size="sm">Estado de OneDrive:</Text>
                            <Badge size="xs" color="green">Sincronizado</Badge>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">�ltima sincronizaci�n:</Text>
                            <Text size="xs">hace 5 minutos</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Archivos sincronizados:</Text>
                            <Text size="xs">1,234 documentos</Text>
                          </Group>
                        </Stack>
                      </Card>
                    </Grid.Col>

                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="green">
                            <IconDatabase size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Base de Datos
                            </Text>
                            <Badge size="sm" color="green">Operativa</Badge>
                          </div>
                        </Group>
                        <Stack spacing="xs">
                          <Group position="apart">
                            <Text size="sm">Versi�n PostgreSQL:</Text>
                            <Text size="xs">14.9</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Tama�o de BD:</Text>
                            <Text size="xs">127 MB</Text>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">�ltimo backup:</Text>
                            <Text size="xs">hace 2 horas</Text>
                          </Group>
                        </Stack>
                      </Card>
                    </Grid.Col>
                  </Grid>
                </Paper>

                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Estado del Sistema
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Stack spacing="md">
                        <div>
                          <Group position="apart" mb="xs">
                            <Text size="sm">Uso de CPU</Text>
                            <Text size="sm">12%</Text>
                          </Group>
                          <Progress value={12} color="blue" size="sm" />
                        </div>
                        <div>
                          <Group position="apart" mb="xs">
                            <Text size="sm">Uso de Memoria</Text>
                            <Text size="sm">34%</Text>
                          </Group>
                          <Progress value={34} color="green" size="sm" />
                        </div>
                        <div>
                          <Group position="apart" mb="xs">
                            <Text size="sm">Almacenamiento Usado</Text>
                            <Text size="sm">48%</Text>
                          </Group>
                          <Progress value={48} color="orange" size="sm" />
                        </div>
                      </Stack>
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <Alert icon={<IconInfoCircle size={16} />} title="Estado del Sistema" color="green">
                        <Text size="sm">
                          Todos los servicios est�n funcionando correctamente. 
                          El �ltimo mantenimiento se realiz� hace 3 d�as.
                        </Text>
                      </Alert>
                    </Grid.Col>
                  </Grid>
                </Paper>
              </Stack>
            </Tabs.Panel>

            {/* Analytics Tab */}
            <Tabs.Panel value="analytics" pt="md">
              <Paper p="lg" radius="md" withBorder>
                <Title order={3} mb="md">
                  Anal�ticas del Sistema
                </Title>
                <Alert icon={<IconInfoCircle size={16} />} title="Pr�ximamente" color="blue">
                  <Text size="sm">
                    Esta secci�n incluir� gr�ficos detallados de uso, estad�sticas 
                    de documentos, an�lisis de usuarios y m�tricas de rendimiento.
                  </Text>
                </Alert>
              </Paper>
            </Tabs.Panel>

            {/* Security Tab */}
            <Tabs.Panel value="security" pt="md">
              <Stack spacing="md">
                <Paper p="lg" radius="md" withBorder>
                  <Title order={3} mb="md">
                    Configuraci�n de Seguridad
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="red">
                            <IconShield size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Pol�ticas de Seguridad
                            </Text>
                            <Text size="xs" color="gray.6">
                              Configuraci�n actual
                            </Text>
                          </div>
                        </Group>
                        <Stack spacing="sm">
                          <Group position="apart">
                            <Text size="sm">Autenticaci�n 2FA:</Text>
                            <Switch checked={true} />
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Sesiones autom�ticas:</Text>
                            <Switch checked={false} />
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Registro de auditor�a:</Text>
                            <Switch checked={true} />
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Notificaciones de acceso:</Text>
                            <Switch checked={true} />
                          </Group>
                        </Stack>
                      </Card>
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <Card p="md" radius="md" withBorder>
                        <Group spacing="sm" mb="md">
                          <ThemeIcon size="lg" variant="light" color="orange">
                            <IconAlertTriangle size={20} />
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              Alertas de Seguridad
                            </Text>
                            <Text size="xs" color="gray.6">
                              �ltimas 24 horas
                            </Text>
                          </div>
                        </Group>
                        <Stack spacing="xs">
                          <Group position="apart">
                            <Text size="sm">Intentos de login fallidos:</Text>
                            <Badge size="sm" color="orange">3</Badge>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Accesos desde nuevas IPs:</Text>
                            <Badge size="sm" color="blue">1</Badge>
                          </Group>
                          <Group position="apart">
                            <Text size="sm">Descargas inusuales:</Text>
                            <Badge size="sm" color="green">0</Badge>
                          </Group>
                        </Stack>
                      </Card>
                    </Grid.Col>
                  </Grid>
                </Paper>

                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Registro de Auditor�a
                  </Title>
                  <Alert icon={<IconInfoCircle size={16} />} title="Funcionalidad de auditor�a" color="blue">
                    <Text size="sm">
                      El registro completo de auditor�a permite rastrear todas las acciones 
                      realizadas en el sistema por cada usuario.
                    </Text>
                  </Alert>
                </Paper>
              </Stack>
            </Tabs.Panel>
          </Tabs>
        </Stack>
      </motion.div>

      {/* User Modal */}
      <Modal
        opened={userModalOpened}
        onClose={closeUserModal}
        title={selectedUser ? `Editar Usuario: ${selectedUser.name}` : 'Nuevo Usuario'}
        size="lg"
        centered
      >
        <Stack spacing="md">
          <Grid>
            <Grid.Col xs={12} sm={6}>
              <TextInput
                label="Nombre completo"
                placeholder="Ej: Mar�a Garc�a"
                defaultValue={selectedUser?.name || ''}
                required
              />
            </Grid.Col>
            <Grid.Col xs={12} sm={6}>
              <TextInput
                label="Email"
                placeholder="email@empresa.com"
                defaultValue={selectedUser?.email || ''}
                required
              />
            </Grid.Col>
          </Grid>
          
          <Grid>
            <Grid.Col xs={12} sm={6}>
              <Select
                label="Rol"
                data={[
                  { value: 'viewer', label: 'Visualizador' },
                  { value: 'operator', label: 'Operador' },
                  { value: 'admin', label: 'Administrador' },
                ]}
                defaultValue={selectedUser?.role || 'viewer'}
                required
              />
            </Grid.Col>
            <Grid.Col xs={12} sm={6}>
              <TextInput
                label="Departamento"
                placeholder="Ej: Recursos Humanos"
                defaultValue={selectedUser?.department || ''}
              />
            </Grid.Col>
          </Grid>

          <Grid>
            <Grid.Col xs={12} sm={6}>
              <TextInput
                label="Tel�fono"
                placeholder="+34 612 345 678"
                defaultValue={selectedUser?.phone || ''}
              />
            </Grid.Col>
            <Grid.Col xs={12} sm={6}>
              <Select
                label="Estado"
                data={[
                  { value: 'active', label: 'Activo' },
                  { value: 'inactive', label: 'Inactivo' },
                  { value: 'suspended', label: 'Suspendido' },
                ]}
                defaultValue={selectedUser?.status || 'active'}
              />
            </Grid.Col>
          </Grid>

          <Group position="right" mt="md">
            <Button variant="light" onClick={closeUserModal}>
              Cancelar
            </Button>
            <Button>
              {selectedUser ? 'Actualizar' : 'Crear'} Usuario
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Settings Modal */}
      <Modal
        opened={settingsModalOpened}
        onClose={() => setSettingsModalOpened(false)}
        title="Configuraci�n Avanzada del Sistema"
        size="xl"
        centered
      >
        <Tabs defaultValue="general">
          <Tabs.List>
            <Tabs.Tab value="general" icon={<IconSettings size={16} />}>
              General
            </Tabs.Tab>
            <Tabs.Tab value="notifications" icon={<IconBell size={16} />}>
              Notificaciones
            </Tabs.Tab>
            <Tabs.Tab value="appearance" icon={<IconPalette size={16} />}>
              Apariencia
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="general" pt="md">
            <Stack spacing="md">
              <TextInput
                label="Nombre de la organizaci�n"
                defaultValue="Mi Empresa S.L."
              />
              <Textarea
                label="Descripci�n"
                placeholder="Descripci�n de la organizaci�n"
                minRows={2}
              />
              <NumberInput
                label="Tama�o m�ximo de archivo (MB)"
                defaultValue={50}
                min={1}
                max={500}
              />
              <Select
                label="Idioma predeterminado"
                data={[
                  { value: 'es', label: 'Espa�ol' },
                  { value: 'en', label: 'English' },
                  { value: 'fr', label: 'Fran�ais' },
                ]}
                defaultValue="es"
              />
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="notifications" pt="md">
            <Stack spacing="md">
              <Switch
                label="Notificaciones por email"
                description="Enviar notificaciones importantes por correo electr�nico"
                defaultChecked={true}
              />
              <Switch
                label="Notificaciones de nuevos usuarios"
                description="Notificar cuando se registre un nuevo usuario"
                defaultChecked={true}
              />
              <Switch
                label="Alertas de seguridad"
                description="Notificar sobre eventos de seguridad"
                defaultChecked={true}
              />
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="appearance" pt="md">
            <Stack spacing="md">
              <Select
                label="Tema predeterminado"
                data={[
                  { value: 'light', label: 'Claro' },
                  { value: 'dark', label: 'Oscuro' },
                  { value: 'auto', label: 'Autom�tico' },
                ]}
                defaultValue="light"
              />
              <TextInput
                label="Color primario"
                defaultValue="#339af0"
                placeholder="#339af0"
              />
              <FileInput
                label="Logo de la organizaci�n"
                placeholder="Seleccionar archivo"
                accept="image/*"
              />
            </Stack>
          </Tabs.Panel>
        </Tabs>

        <Group position="right" mt="xl">
          <Button variant="light" onClick={() => setSettingsModalOpened(false)}>
            Cancelar
          </Button>
          <Button>
            Guardar Configuraci�n
          </Button>
        </Group>
      </Modal>
    </Container>
  );
};

export default Admin;