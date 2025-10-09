import React from 'react';
import {
  Container,
  Grid,
  Card,
  Text,
  Title,
  Group,
  ThemeIcon,
  Badge,
  Progress,
  Stack,
  ActionIcon,
  SimpleGrid,
  Paper,
  RingProgress,
  Center,
} from '@mantine/core';
import {
  IconFileText,
  IconUsers,
  IconQrcode,
  IconCloudUpload,
  IconTrendingUp,
  IconCheck,
  IconClock,
  IconAlertTriangle,
  IconExternalLink,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';

import { useAuth } from '../hooks/useAuth';

const Dashboard = () => {
  const { user } = useAuth();

  // Datos de ejemplo para el dashboard
  const stats = [
    {
      title: 'Documentos Totales',
      value: '1,234',
      diff: 34,
      description: 'En los últimos 30 días',
      icon: IconFileText,
      color: 'blue',
    },
    {
      title: 'Usuarios Activos',
      value: '23',
      diff: 8,
      description: 'Usuarios del sistema',
      icon: IconUsers,
      color: 'green',
    },
    {
      title: 'Códigos QR',
      value: '892',
      diff: 12,
      description: 'Generados este mes',
      icon: IconQrcode,
      color: 'violet',
    },
    {
      title: 'Almacenamiento',
      value: '2.4 GB',
      diff: 5,
      description: 'De 5 GB disponibles',
      icon: IconCloudUpload,
      color: 'orange',
    },
  ];

  const activities = [
    {
      action: 'Documento subido',
      user: 'María García',
      document: 'Contrato-EMP-001.pdf',
      time: 'hace 5 minutos',
      status: 'success',
    },
    {
      action: 'QR generado',
      user: 'Juan Pérez',
      document: 'GCO-REG-099',
      time: 'hace 15 minutos',
      status: 'info',
    },
    {
      action: 'Búsqueda realizada',
      user: 'Ana López',
      document: 'Documentos de empleados',
      time: 'hace 30 minutos',
      status: 'default',
    },
    {
      action: 'Error en sincronización',
      user: 'Sistema',
      document: 'OneDrive Backup',
      time: 'hace 1 hora',
      status: 'warning',
    },
  ];

  return (
    <Container size="xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Stack spacing="xl">
          {/* Header */}
          <Group position="apart">
            <div>
              <Title order={1} size="h2" mb="xs">
                ¡Bienvenido, {user?.name?.split(' ')[0] || 'Usuario'}!
              </Title>
              <Text color="gray.6" size="lg">
                Panel de control del Sistema de Gestión Documental
              </Text>
            </div>
            <Badge size="lg" variant="light" color="green">
              Sistema Operativo
            </Badge>
          </Group>

          {/* Estadísticas principales */}
          <SimpleGrid cols={4} breakpoints={[
            { maxWidth: 'lg', cols: 2 },
            { maxWidth: 'sm', cols: 1 },
          ]}>
            {stats.map((stat, index) => (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card p="md" radius="md" withBorder>
                  <Group position="apart">
                    <div>
                      <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                        {stat.title}
                      </Text>
                      <Text size="xl" weight={700} mt={4}>
                        {stat.value}
                      </Text>
                      <Text size="xs" color="gray.6" mt={4}>
                        {stat.description}
                      </Text>
                    </div>
                    <ThemeIcon
                      size="lg"
                      radius="md"
                      variant="light"
                      color={stat.color}
                    >
                      <stat.icon size={20} />
                    </ThemeIcon>
                  </Group>
                  <Group spacing="xs" mt="md">
                    <IconTrendingUp size={14} color="green" />
                    <Text size="xs" color="green">
                      +{stat.diff}%
                    </Text>
                    <Text size="xs" color="gray.6">
                      vs mes anterior
                    </Text>
                  </Group>
                </Card>
              </motion.div>
            ))}
          </SimpleGrid>

          <Grid>
            {/* Actividad reciente */}
            <Grid.Col xs={12} lg={8}>
              <Card p="lg" radius="md" withBorder>
                <Group position="apart" mb="md">
                  <Title order={3} size="h4">
                    Actividad Reciente
                  </Title>
                  <ActionIcon variant="light" color="blue">
                    <IconExternalLink size={16} />
                  </ActionIcon>
                </Group>

                <Stack spacing="md">
                  {activities.map((activity, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Group position="apart" p="md" style={{
                        borderRadius: '8px',
                        backgroundColor: 'var(--mantine-color-gray-0)',
                        border: '1px solid var(--mantine-color-gray-2)',
                      }}>
                        <Group spacing="md">
                          <ThemeIcon
                            size="md"
                            radius="xl"
                            variant="light"
                            color={
                              activity.status === 'success' ? 'green' :
                              activity.status === 'warning' ? 'orange' :
                              activity.status === 'info' ? 'blue' : 'gray'
                            }
                          >
                            {activity.status === 'success' ? <IconCheck size={14} /> :
                             activity.status === 'warning' ? <IconAlertTriangle size={14} /> :
                             activity.status === 'info' ? <IconQrcode size={14} /> :
                             <IconClock size={14} />}
                          </ThemeIcon>
                          <div>
                            <Text size="sm" weight={500}>
                              {activity.action}
                            </Text>
                            <Text size="xs" color="gray.6">
                              {activity.user} " {activity.document}
                            </Text>
                          </div>
                        </Group>
                        <Text size="xs" color="gray.5">
                          {activity.time}
                        </Text>
                      </Group>
                    </motion.div>
                  ))}
                </Stack>
              </Card>
            </Grid.Col>

            {/* Panel lateral */}
            <Grid.Col xs={12} lg={4}>
              <Stack spacing="md">
                {/* Estado del sistema */}
                <Card p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Estado del Sistema
                  </Title>
                  
                  <Stack spacing="lg">
                    <div>
                      <Group position="apart" mb="xs">
                        <Text size="sm">OneDrive</Text>
                        <Badge size="xs" color="green">Conectado</Badge>
                      </Group>
                      <Progress value={100} color="green" size="xs" />
                    </div>

                    <div>
                      <Group position="apart" mb="xs">
                        <Text size="sm">Base de Datos</Text>
                        <Badge size="xs" color="green">Activa</Badge>
                      </Group>
                      <Progress value={85} color="blue" size="xs" />
                    </div>

                    <div>
                      <Group position="apart" mb="xs">
                        <Text size="sm">Microsoft 365</Text>
                        <Badge size="xs" color="green">Sincronizado</Badge>
                      </Group>
                      <Progress value={100} color="green" size="xs" />
                    </div>
                  </Stack>
                </Card>

                {/* Uso de almacenamiento */}
                <Card p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Almacenamiento
                  </Title>
                  
                  <Center>
                    <RingProgress
                      size={120}
                      thickness={12}
                      label={
                        <Text size="xs" align="center">
                          2.4 GB / 5 GB
                        </Text>
                      }
                      sections={[
                        { value: 48, color: 'blue' },
                      ]}
                    />
                  </Center>

                  <Stack spacing="xs" mt="md">
                    <Group position="apart">
                      <Text size="xs" color="gray.6">Documentos</Text>
                      <Text size="xs">1.8 GB</Text>
                    </Group>
                    <Group position="apart">
                      <Text size="xs" color="gray.6">Plantillas</Text>
                      <Text size="xs">350 MB</Text>
                    </Group>
                    <Group position="apart">
                      <Text size="xs" color="gray.6">Temporales</Text>
                      <Text size="xs">250 MB</Text>
                    </Group>
                  </Stack>
                </Card>

                {/* Accesos rápidos */}
                <Card p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Accesos Rápidos
                  </Title>
                  
                  <Stack spacing="xs">
                    <Paper p="sm" radius="sm" style={{ cursor: 'pointer' }} withBorder>
                      <Group spacing="sm">
                        <ThemeIcon size="sm" variant="light" color="green">
                          <IconFileText size={14} />
                        </ThemeIcon>
                        <Text size="sm">Registrar Documento</Text>
                      </Group>
                    </Paper>
                    
                    <Paper p="sm" radius="sm" style={{ cursor: 'pointer' }} withBorder>
                      <Group spacing="sm">
                        <ThemeIcon size="sm" variant="light" color="orange">
                          <IconQrcode size={14} />
                        </ThemeIcon>
                        <Text size="sm">Generar QR</Text>
                      </Group>
                    </Paper>
                    
                    <Paper p="sm" radius="sm" style={{ cursor: 'pointer' }} withBorder>
                      <Group spacing="sm">
                        <ThemeIcon size="sm" variant="light" color="blue">
                          <IconUsers size={14} />
                        </ThemeIcon>
                        <Text size="sm">Gestionar Usuarios</Text>
                      </Group>
                    </Paper>
                  </Stack>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </Stack>
      </motion.div>
    </Container>
  );
};

export default Dashboard;