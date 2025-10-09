import React from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Button,
  Group,
  Stack,
  Alert,
  Anchor,
  Code,
  Divider,
} from '@mantine/core';
import {
  IconAlertTriangle,
  IconRefresh,
  IconHome,
  IconBug,
  IconMail,
} from '@tabler/icons-react';

const ErrorFallback = ({ error, resetErrorBoundary }) => {
  const isDevelopment = process.env.NODE_ENV === 'development';

  const handleReload = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  const handleReportError = () => {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      url: window.location.href,
    };

    // Crear enlace mailto con información del error
    const subject = encodeURIComponent('Error en SGD Web');
    const body = encodeURIComponent(`
Se ha producido un error en SGD Web:

Error: ${error.message}
Fecha: ${errorInfo.timestamp}
URL: ${errorInfo.url}
Navegador: ${errorInfo.userAgent}

${isDevelopment ? `\nStack trace:\n${error.stack}` : ''}

Por favor, describe qué estabas haciendo cuando ocurrió el error:
[Describe aquí las acciones que realizaste]
    `);

    window.open(`mailto:soporte@tuempresa.com?subject=${subject}&body=${body}`);
  };

  return (
    <Container size="md" style={{ marginTop: '10vh' }}>
      <Paper p="xl" radius="lg" shadow="md" withBorder>
        <Stack spacing="lg" align="center">
          {/* Icono de error */}
          <div
            style={{
              padding: '20px',
              borderRadius: '50%',
              backgroundColor: '#fef2f2',
              border: '2px solid #fecaca',
            }}
          >
            <IconAlertTriangle size={48} color="#dc2626" />
          </div>

          {/* Título principal */}
          <Title order={1} align="center" color="red.6">
            ¡Oops! Algo salió mal
          </Title>

          {/* Mensaje de error amigable */}
          <Text align="center" size="lg" color="gray.7">
            Se ha producido un error inesperado en la aplicación.
            No te preocupes, nuestro equipo ha sido notificado automáticamente.
          </Text>

          {/* Alert con información técnica */}
          <Alert
            icon={<IconBug size={16} />}
            title="Información técnica"
            color="orange"
            style={{ width: '100%' }}
          >
            <Text size="sm" mb="xs">
              <strong>Error:</strong> {error.message}
            </Text>
            {isDevelopment && (
              <>
                <Text size="sm" mb="xs">
                  <strong>Archivo:</strong> {error.fileName || 'Desconocido'}
                </Text>
                <Text size="sm" mb="xs">
                  <strong>Línea:</strong> {error.lineNumber || 'Desconocida'}
                </Text>
              </>
            )}
            <Text size="sm">
              <strong>Timestamp:</strong> {new Date().toLocaleString()}
            </Text>
          </Alert>

          {/* Stack trace en desarrollo */}
          {isDevelopment && error.stack && (
            <Paper p="md" style={{ width: '100%', backgroundColor: '#f8f9fa' }}>
              <Text size="sm" weight={500} mb="xs">
                Stack Trace:
              </Text>
              <Code
                block
                style={{
                  maxHeight: '200px',
                  overflow: 'auto',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {error.stack}
              </Code>
            </Paper>
          )}

          <Divider style={{ width: '100%' }} />

          {/* Acciones disponibles */}
          <Stack spacing="md" style={{ width: '100%' }}>
            <Text align="center" weight={500} size="lg">
              ¿Qué puedes hacer ahora?
            </Text>

            <Group position="center" spacing="md">
              <Button
                leftIcon={<IconRefresh size={16} />}
                onClick={resetErrorBoundary}
                variant="filled"
                color="blue"
                size="md"
              >
                Intentar de nuevo
              </Button>

              <Button
                leftIcon={<IconHome size={16} />}
                onClick={handleGoHome}
                variant="outline"
                color="blue"
                size="md"
              >
                Ir al inicio
              </Button>

              <Button
                leftIcon={<IconRefresh size={16} />}
                onClick={handleReload}
                variant="light"
                color="gray"
                size="md"
              >
                Recargar página
              </Button>
            </Group>

            <Group position="center" spacing="xs">
              <Text size="sm" color="gray.6">
                ¿El problema persiste?
              </Text>
              <Anchor
                size="sm"
                onClick={handleReportError}
                style={{ cursor: 'pointer' }}
              >
                <Group spacing={4}>
                  <IconMail size={14} />
                  Reportar error
                </Group>
              </Anchor>
            </Group>
          </Stack>

          {/* Información adicional */}
          <Paper p="md" style={{ width: '100%', backgroundColor: '#f8f9fa' }}>
            <Text size="sm" color="gray.6" align="center">
              <strong>SGD Web v1.0.0</strong> • Sistema de Gestión Documental
              <br />
              Si necesitas ayuda inmediata, contacta al administrador del sistema.
            </Text>
          </Paper>
        </Stack>
      </Paper>
    </Container>
  );
};

export default ErrorFallback;