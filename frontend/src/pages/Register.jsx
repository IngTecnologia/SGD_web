import React, { useState } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Button,
  FileInput,
  TextInput,
  Select,
  Textarea,
  Grid,
  Card,
  Badge,
  Progress,
  ActionIcon,
  Alert,
  Timeline,
  ThemeIcon,
  Divider,
  Stepper,
  Center,
  Box,
} from '@mantine/core';
import {
  IconFileUpload,
  IconFile,
  IconFileText,
  IconFileCertificate,
  IconFileDescription,
  IconCheck,
  IconX,
  IconClock,
  IconAlertTriangle,
  IconCloudUpload,
  IconQrcode,
  IconScan,
  IconDownload,
  IconEye,
  IconTrash,
  IconInfoCircle,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';

const Register = () => {
  const { user } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [files, setFiles] = useState([]);
  const [formData, setFormData] = useState({
    documentType: '',
    title: '',
    description: '',
    category: '',
    tags: '',
    priority: 'medium',
  });
  const [uploadProgress, setUploadProgress] = useState({});
  const [processingStatus, setProcessingStatus] = useState('idle');

  const documentTypes = [
    { value: 'contract', label: 'Contrato' },
    { value: 'invoice', label: 'Factura' },
    { value: 'report', label: 'Informe' },
    { value: 'certificate', label: 'Certificado' },
    { value: 'policy', label: 'Política' },
    { value: 'manual', label: 'Manual' },
    { value: 'other', label: 'Otro' },
  ];

  const categories = [
    { value: 'hr', label: 'Recursos Humanos' },
    { value: 'finance', label: 'Finanzas' },
    { value: 'legal', label: 'Legal' },
    { value: 'operations', label: 'Operaciones' },
    { value: 'compliance', label: 'Cumplimiento' },
    { value: 'general', label: 'General' },
  ];

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    switch (extension) {
      case 'pdf':
        return <IconFileCertificate size={20} color="red" />;
      case 'doc':
      case 'docx':
        return <IconFileText size={20} color="blue" />;
      case 'xls':
      case 'xlsx':
        return <IconFileDescription size={20} color="green" />;
      default:
        return <IconFile size={20} color="gray" />;
    }
  };

  const handleFileUpload = (uploadedFiles) => {
    const newFiles = Array.from(uploadedFiles).map((file, index) => ({
      id: `file-${Date.now()}-${index}`,
      file,
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
      qrCode: null,
      documentId: null,
    }));
    setFiles(prev => [...prev, ...newFiles]);
    
    // Simular progreso de carga
    newFiles.forEach(fileData => {
      simulateUpload(fileData.id);
    });
  };

  const simulateUpload = (fileId) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, status: 'completed', progress: 100, qrCode: `QR-${Math.random().toString(36).substr(2, 9)}` }
            : f
        ));
      }
      setUploadProgress(prev => ({ ...prev, [fileId]: progress }));
    }, 200);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileId];
      return newProgress;
    });
  };

  const nextStep = () => {
    if (activeStep < 2) {
      setActiveStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (activeStep > 0) {
      setActiveStep(prev => prev - 1);
    }
  };

  const handleSubmit = () => {
    setProcessingStatus('processing');
    // Simular procesamiento
    setTimeout(() => {
      setProcessingStatus('completed');
      setActiveStep(3);
    }, 3000);
  };

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
                  Registrar Documentos
                </Title>
                <Text color="gray.6" size="lg">
                  Sube y procesa documentos para el sistema de gestión documental
                </Text>
              </div>
              <Badge size="lg" variant="light" color="blue">
                {user?.role === 'admin' ? 'Administrador' : 'Operador'}
              </Badge>
            </Group>
          </Paper>

          {/* Stepper */}
          <Paper p="lg" radius="md" withBorder>
            <Stepper active={activeStep} onStepClick={setActiveStep} breakpoint="sm">
              <Stepper.Step
                label="Seleccionar Archivos"
                description="Sube los documentos a procesar"
                icon={<IconFileUpload size={18} />}
              />
              <Stepper.Step
                label="Configurar Metadatos"
                description="Define información del documento"
                icon={<IconFileDescription size={18} />}
              />
              <Stepper.Step
                label="Revisar y Confirmar"
                description="Verifica la información antes de procesar"
                icon={<IconEye size={18} />}
              />
              <Stepper.Step
                label="Procesamiento"
                description="Procesando documentos"
                icon={<IconCloudUpload size={18} />}
              />
            </Stepper>
          </Paper>

          {/* Step Content */}
          <AnimatePresence mode="wait">
            {activeStep === 0 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Grid>
                  <Grid.Col xs={12} md={8}>
                    <Paper p="lg" radius="md" withBorder>
                      <Stack spacing="lg">
                        <div>
                          <Title order={3} mb="sm">
                            Subir Documentos
                          </Title>
                          <Text color="gray.6" mb="md">
                            Selecciona los archivos que deseas procesar. Se aceptan PDF, DOC, DOCX, XLS, XLSX.
                          </Text>
                        </div>

                        <FileInput
                          label="Seleccionar archivos"
                          placeholder="Haz clic para seleccionar archivos"
                          icon={<IconFileUpload size={14} />}
                          multiple
                          accept=".pdf,.doc,.docx,.xls,.xlsx"
                          onChange={handleFileUpload}
                          styles={{
                            input: {
                              minHeight: '80px',
                              border: '2px dashed #e9ecef',
                              borderRadius: '8px',
                            },
                          }}
                        />

                        {files.length > 0 && (
                          <div>
                            <Text size="sm" weight={500} mb="sm">
                              Archivos seleccionados ({files.length})
                            </Text>
                            <Stack spacing="xs">
                              {files.map((fileData) => (
                                <Card key={fileData.id} p="sm" radius="md" withBorder>
                                  <Group position="apart">
                                    <Group spacing="sm">
                                      {getFileIcon(fileData.name)}
                                      <div style={{ flex: 1 }}>
                                        <Text size="sm" weight={500}>
                                          {fileData.name}
                                        </Text>
                                        <Text size="xs" color="gray.6">
                                          {(fileData.size / 1024 / 1024).toFixed(2)} MB
                                        </Text>
                                      </div>
                                    </Group>
                                    <Group spacing="xs">
                                      <ThemeIcon
                                        size="sm"
                                        variant="light"
                                        color={
                                          fileData.status === 'completed' ? 'green' :
                                          fileData.status === 'error' ? 'red' : 'blue'
                                        }
                                      >
                                        {fileData.status === 'completed' ? <IconCheck size={12} /> :
                                         fileData.status === 'error' ? <IconX size={12} /> :
                                         <IconClock size={12} />}
                                      </ThemeIcon>
                                      <ActionIcon
                                        size="sm"
                                        variant="subtle"
                                        color="red"
                                        onClick={() => removeFile(fileData.id)}
                                      >
                                        <IconTrash size={12} />
                                      </ActionIcon>
                                    </Group>
                                  </Group>
                                  {fileData.status === 'pending' && (
                                    <Progress
                                      value={uploadProgress[fileData.id] || 0}
                                      size="xs"
                                      mt="xs"
                                      color="blue"
                                    />
                                  )}
                                  {fileData.status === 'completed' && fileData.qrCode && (
                                    <Group spacing="xs" mt="xs">
                                      <IconQrcode size={14} />
                                      <Text size="xs" color="green">
                                        QR generado: {fileData.qrCode}
                                      </Text>
                                    </Group>
                                  )}
                                </Card>
                              ))}
                            </Stack>
                          </div>
                        )}
                      </Stack>
                    </Paper>
                  </Grid.Col>

                  <Grid.Col xs={12} md={4}>
                    <Stack spacing="md">
                      <Paper p="lg" radius="md" withBorder>
                        <Title order={4} mb="md">
                          Información
                        </Title>
                        <Stack spacing="sm">
                          <Group spacing="xs">
                            <IconInfoCircle size={16} color="blue" />
                            <Text size="sm">
                              Los documentos se procesan automáticamente
                            </Text>
                          </Group>
                          <Group spacing="xs">
                            <IconQrcode size={16} color="green" />
                            <Text size="sm">
                              Se genera un código QR único para cada documento
                            </Text>
                          </Group>
                          <Group spacing="xs">
                            <IconCloudUpload size={16} color="orange" />
                            <Text size="sm">
                              Los archivos se almacenan en OneDrive Business
                            </Text>
                          </Group>
                        </Stack>
                      </Paper>

                      <Paper p="lg" radius="md" withBorder>
                        <Title order={4} mb="md">
                          Formatos Soportados
                        </Title>
                        <Stack spacing="xs">
                          <Group spacing="xs">
                            <IconFileCertificate size={16} color="red" />
                            <Text size="sm">PDF</Text>
                          </Group>
                          <Group spacing="xs">
                            <IconFileText size={16} color="blue" />
                            <Text size="sm">DOC, DOCX</Text>
                          </Group>
                          <Group spacing="xs">
                            <IconFileDescription size={16} color="green" />
                            <Text size="sm">XLS, XLSX</Text>
                          </Group>
                        </Stack>
                      </Paper>
                    </Stack>
                  </Grid.Col>
                </Grid>
              </motion.div>
            )}

            {activeStep === 1 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Paper p="lg" radius="md" withBorder>
                  <Title order={3} mb="lg">
                    Configurar Metadatos
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Stack spacing="md">
                        <Select
                          label="Tipo de Documento"
                          placeholder="Selecciona el tipo"
                          data={documentTypes}
                          value={formData.documentType}
                          onChange={(value) => setFormData(prev => ({ ...prev, documentType: value }))}
                          required
                        />
                        <TextInput
                          label="Título del Documento"
                          placeholder="Ingresa el título"
                          value={formData.title}
                          onChange={(event) => setFormData(prev => ({ ...prev, title: event.target.value }))}
                          required
                        />
                        <Select
                          label="Categoría"
                          placeholder="Selecciona una categoría"
                          data={categories}
                          value={formData.category}
                          onChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                          required
                        />
                      </Stack>
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <Stack spacing="md">
                        <Textarea
                          label="Descripción"
                          placeholder="Describe el contenido del documento"
                          value={formData.description}
                          onChange={(event) => setFormData(prev => ({ ...prev, description: event.target.value }))}
                          minRows={3}
                        />
                        <TextInput
                          label="Etiquetas"
                          placeholder="Ej: contrato, empleado, 2024"
                          value={formData.tags}
                          onChange={(event) => setFormData(prev => ({ ...prev, tags: event.target.value }))}
                          description="Separa las etiquetas con comas"
                        />
                        <Select
                          label="Prioridad"
                          data={[
                            { value: 'low', label: 'Baja' },
                            { value: 'medium', label: 'Media' },
                            { value: 'high', label: 'Alta' },
                          ]}
                          value={formData.priority}
                          onChange={(value) => setFormData(prev => ({ ...prev, priority: value }))}
                        />
                      </Stack>
                    </Grid.Col>
                  </Grid>
                </Paper>
              </motion.div>
            )}

            {activeStep === 2 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Paper p="lg" radius="md" withBorder>
                  <Title order={3} mb="lg">
                    Revisar y Confirmar
                  </Title>
                  <Grid>
                    <Grid.Col xs={12} md={8}>
                      <Stack spacing="md">
                        <Card p="md" radius="md" withBorder>
                          <Title order={4} mb="sm">
                            Información del Documento
                          </Title>
                          <Group spacing="xl">
                            <div>
                              <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                                Tipo
                              </Text>
                              <Text size="sm">{documentTypes.find(t => t.value === formData.documentType)?.label || 'No seleccionado'}</Text>
                            </div>
                            <div>
                              <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                                Categoría
                              </Text>
                              <Text size="sm">{categories.find(c => c.value === formData.category)?.label || 'No seleccionado'}</Text>
                            </div>
                            <div>
                              <Text size="xs" color="gray.6" transform="uppercase" weight={700}>
                                Prioridad
                              </Text>
                              <Badge size="sm" color={
                                formData.priority === 'high' ? 'red' :
                                formData.priority === 'medium' ? 'orange' : 'green'
                              }>
                                {formData.priority === 'high' ? 'Alta' :
                                 formData.priority === 'medium' ? 'Media' : 'Baja'}
                              </Badge>
                            </div>
                          </Group>
                          <Divider my="sm" />
                          <div>
                            <Text size="xs" color="gray.6" transform="uppercase" weight={700} mb="xs">
                              Título
                            </Text>
                            <Text size="sm">{formData.title || 'Sin título'}</Text>
                          </div>
                          <div>
                            <Text size="xs" color="gray.6" transform="uppercase" weight={700} mb="xs" mt="sm">
                              Descripción
                            </Text>
                            <Text size="sm">{formData.description || 'Sin descripción'}</Text>
                          </div>
                          <div>
                            <Text size="xs" color="gray.6" transform="uppercase" weight={700} mb="xs" mt="sm">
                              Etiquetas
                            </Text>
                            <Text size="sm">{formData.tags || 'Sin etiquetas'}</Text>
                          </div>
                        </Card>

                        <Card p="md" radius="md" withBorder>
                          <Title order={4} mb="sm">
                            Archivos a Procesar ({files.length})
                          </Title>
                          <Stack spacing="xs">
                            {files.map((fileData) => (
                              <Group key={fileData.id} spacing="sm">
                                {getFileIcon(fileData.name)}
                                <div style={{ flex: 1 }}>
                                  <Text size="sm">{fileData.name}</Text>
                                  <Text size="xs" color="gray.6">
                                    {(fileData.size / 1024 / 1024).toFixed(2)} MB
                                  </Text>
                                </div>
                                <Badge size="sm" color="green">
                                  Listo
                                </Badge>
                              </Group>
                            ))}
                          </Stack>
                        </Card>
                      </Stack>
                    </Grid.Col>
                    <Grid.Col xs={12} md={4}>
                      <Alert icon={<IconInfoCircle size={16} />} title="Información" color="blue">
                        <Text size="sm">
                          Una vez confirmado, los documentos se procesarán automáticamente y se generarán los códigos QR correspondientes.
                        </Text>
                      </Alert>
                    </Grid.Col>
                  </Grid>
                </Paper>
              </motion.div>
            )}

            {activeStep === 3 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Paper p="lg" radius="md" withBorder>
                  <Center>
                    <Stack spacing="lg" style={{ textAlign: 'center' }}>
                      <ThemeIcon size="xl" variant="light" color="green">
                        <IconCheck size={32} />
                      </ThemeIcon>
                      <div>
                        <Title order={2} mb="sm">
                          ¡Procesamiento Completado!
                        </Title>
                        <Text color="gray.6" size="lg">
                          Todos los documentos han sido procesados exitosamente
                        </Text>
                      </div>
                      <Group spacing="md">
                        <Button variant="light" leftIcon={<IconDownload size={16} />}>
                          Descargar Códigos QR
                        </Button>
                        <Button variant="light" leftIcon={<IconEye size={16} />}>
                          Ver Documentos
                        </Button>
                      </Group>
                    </Stack>
                  </Center>
                </Paper>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation */}
          {activeStep < 3 && (
            <Paper p="lg" radius="md" withBorder>
              <Group position="apart">
                <Button
                  variant="subtle"
                  onClick={prevStep}
                  disabled={activeStep === 0}
                >
                  Anterior
                </Button>
                <Group spacing="sm">
                  <Text size="sm" color="gray.6">
                    Paso {activeStep + 1} de 4
                  </Text>
                  {activeStep === 2 ? (
                    <Button
                      onClick={handleSubmit}
                      loading={processingStatus === 'processing'}
                      disabled={files.length === 0}
                    >
                      Procesar Documentos
                    </Button>
                  ) : (
                    <Button
                      onClick={nextStep}
                      disabled={
                        (activeStep === 0 && files.length === 0) ||
                        (activeStep === 1 && (!formData.documentType || !formData.title || !formData.category))
                      }
                    >
                      Siguiente
                    </Button>
                  )}
                </Group>
              </Group>
            </Paper>
          )}
        </Stack>
      </motion.div>
    </Container>
  );
};

export default Register;