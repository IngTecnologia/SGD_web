import React, { useState } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Button,
  TextInput,
  Select,
  Textarea,
  Grid,
  Card,
  Badge,
  ActionIcon,
  Tabs,
  Code,
  Divider,
  Center,
  Box,
  Table,
  ScrollArea,
  Modal,
  Alert,
  FileInput,
  JsonInput,
  Stepper,
  Checkbox,
  NumberInput,
  ColorInput,
  Slider,
  Switch,
  Image,
  ThemeIcon,
  Timeline,
  Progress,
  Notification,
} from '@mantine/core';
import {
  IconFileText,
  IconTemplate,
  IconQrcode,
  IconDownload,
  IconEye,
  IconSettings,
  IconPlus,
  IconTrash,
  IconEdit,
  IconCopy,
  IconShare,
  IconPalette,
  IconBrandHtml5,
  IconBrandCss3,
  IconFileTypePdf,
  IconFileTypeDocx,
  IconPhoto,
  IconUpload,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconInfoCircle,
  IconWand,
  IconScan,
  IconRefresh,
  IconHistory,
  IconStar,
  IconSearch,
  IconFilter,
  IconLayoutGrid,
  IconList,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';

const Generator = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('templates');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [generatorType, setGeneratorType] = useState('qr');
  const [qrConfig, setQrConfig] = useState({
    text: '',
    size: 256,
    errorCorrection: 'M',
    margin: 4,
    colorDark: '#000000',
    colorLight: '#ffffff',
    logo: null,
    format: 'png',
  });
  const [templateConfig, setTemplateConfig] = useState({
    name: '',
    description: '',
    category: '',
    fields: [],
    html: '',
    css: '',
    variables: {},
  });
  const [previewOpened, setPreviewOpened] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedFiles, setGeneratedFiles] = useState([]);

  // Mock data para plantillas
  const templates = [
    {
      id: 'template-1',
      name: 'Contrato de Trabajo',
      description: 'Plantilla estándar para contratos de trabajo',
      category: 'legal',
      fields: ['nombre', 'cargo', 'salario', 'fecha_inicio'],
      preview: '/api/templates/contract-preview.png',
      downloads: 45,
      rating: 4.8,
      lastModified: '2024-01-20',
    },
    {
      id: 'template-2',
      name: 'Certificado de Empleado',
      description: 'Certificado de trabajo para empleados',
      category: 'hr',
      fields: ['nombre_empleado', 'cargo', 'fecha_ingreso', 'salario'],
      preview: '/api/templates/certificate-preview.png',
      downloads: 32,
      rating: 4.6,
      lastModified: '2024-01-15',
    },
    {
      id: 'template-3',
      name: 'Factura Comercial',
      description: 'Plantilla para facturas comerciales',
      category: 'finance',
      fields: ['cliente', 'productos', 'total', 'fecha_vencimiento'],
      preview: '/api/templates/invoice-preview.png',
      downloads: 78,
      rating: 4.9,
      lastModified: '2024-01-25',
    },
  ];

  const categories = [
    { value: 'legal', label: 'Legal' },
    { value: 'hr', label: 'Recursos Humanos' },
    { value: 'finance', label: 'Finanzas' },
    { value: 'operations', label: 'Operaciones' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'general', label: 'General' },
  ];

  const qrErrorLevels = [
    { value: 'L', label: 'Bajo (~7%)' },
    { value: 'M', label: 'Medio (~15%)' },
    { value: 'Q', label: 'Alto (~25%)' },
    { value: 'H', label: 'Muy Alto (~30%)' },
  ];

  const handleQrGeneration = async () => {
    if (!qrConfig.text.trim()) {
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);

    // Simular proceso de generación
    const interval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          setGeneratedFiles(prev => [...prev, {
            id: Date.now(),
            name: `QR-${Date.now()}.${qrConfig.format}`,
            type: 'qr',
            size: '2.1 KB',
            downloadUrl: '#',
            previewUrl: '#',
            createdAt: new Date().toISOString(),
          }]);
          return 100;
        }
        return prev + 10;
      });
    }, 100);
  };

  const handleTemplateGeneration = async () => {
    if (!selectedTemplate) {
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);

    // Simular proceso de generación
    const interval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          setGeneratedFiles(prev => [...prev, {
            id: Date.now(),
            name: `${selectedTemplate.name}-${Date.now()}.pdf`,
            type: 'document',
            size: '156 KB',
            downloadUrl: '#',
            previewUrl: '#',
            createdAt: new Date().toISOString(),
          }]);
          return 100;
        }
        return prev + 8;
      });
    }, 150);
  };

  const addTemplateField = () => {
    setTemplateConfig(prev => ({
      ...prev,
      fields: [...prev.fields, { name: '', type: 'text', required: true, placeholder: '' }]
    }));
  };

  const removeTemplateField = (index) => {
    setTemplateConfig(prev => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index)
    }));
  };

  const updateTemplateField = (index, field, value) => {
    setTemplateConfig(prev => ({
      ...prev,
      fields: prev.fields.map((f, i) => i === index ? { ...f, [field]: value } : f)
    }));
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
                  Generador de Documentos
                </Title>
                <Text color="gray.6" size="lg">
                  Crea documentos y códigos QR personalizados
                </Text>
              </div>
              <Badge size="lg" variant="light" color="blue">
                {user?.role === 'admin' ? 'Administrador' : 'Operador'}
              </Badge>
            </Group>
          </Paper>

          {/* Generator Type Selection */}
          <Paper p="lg" radius="md" withBorder>
            <Group spacing="md" mb="md">
              <Button
                variant={generatorType === 'qr' ? 'filled' : 'light'}
                leftIcon={<IconQrcode size={16} />}
                onClick={() => setGeneratorType('qr')}
              >
                Códigos QR
              </Button>
              <Button
                variant={generatorType === 'templates' ? 'filled' : 'light'}
                leftIcon={<IconTemplate size={16} />}
                onClick={() => setGeneratorType('templates')}
              >
                Plantillas
              </Button>
              <Button
                variant={generatorType === 'documents' ? 'filled' : 'light'}
                leftIcon={<IconFileText size={16} />}
                onClick={() => setGeneratorType('documents')}
              >
                Documentos
              </Button>
            </Group>
          </Paper>

          {/* QR Generator */}
          {generatorType === 'qr' && (
            <Grid>
              <Grid.Col xs={12} md={8}>
                <Paper p="lg" radius="md" withBorder>
                  <Title order={3} mb="lg">
                    Generador de Códigos QR
                  </Title>
                  <Stack spacing="md">
                    <Textarea
                      label="Contenido del QR"
                      placeholder="Ingresa el texto, URL o datos que deseas codificar"
                      value={qrConfig.text}
                      onChange={(event) => setQrConfig(prev => ({ ...prev, text: event.target.value }))}
                      minRows={3}
                      required
                    />
                    
                    <Grid>
                      <Grid.Col xs={12} sm={6}>
                        <NumberInput
                          label="Tamaño (px)"
                          value={qrConfig.size}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, size: value }))}
                          min={64}
                          max={1024}
                          step={32}
                        />
                      </Grid.Col>
                      <Grid.Col xs={12} sm={6}>
                        <Select
                          label="Corrección de errores"
                          data={qrErrorLevels}
                          value={qrConfig.errorCorrection}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, errorCorrection: value }))}
                        />
                      </Grid.Col>
                    </Grid>

                    <Grid>
                      <Grid.Col xs={12} sm={6}>
                        <ColorInput
                          label="Color del código"
                          value={qrConfig.colorDark}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, colorDark: value }))}
                        />
                      </Grid.Col>
                      <Grid.Col xs={12} sm={6}>
                        <ColorInput
                          label="Color de fondo"
                          value={qrConfig.colorLight}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, colorLight: value }))}
                        />
                      </Grid.Col>
                    </Grid>

                    <Grid>
                      <Grid.Col xs={12} sm={6}>
                        <NumberInput
                          label="Margen"
                          value={qrConfig.margin}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, margin: value }))}
                          min={0}
                          max={10}
                        />
                      </Grid.Col>
                      <Grid.Col xs={12} sm={6}>
                        <Select
                          label="Formato de salida"
                          data={[
                            { value: 'png', label: 'PNG' },
                            { value: 'jpg', label: 'JPG' },
                            { value: 'svg', label: 'SVG' },
                          ]}
                          value={qrConfig.format}
                          onChange={(value) => setQrConfig(prev => ({ ...prev, format: value }))}
                        />
                      </Grid.Col>
                    </Grid>

                    <FileInput
                      label="Logo (opcional)"
                      placeholder="Selecciona un logo para insertar en el centro del QR"
                      accept="image/*"
                      value={qrConfig.logo}
                      onChange={(file) => setQrConfig(prev => ({ ...prev, logo: file }))}
                      icon={<IconPhoto size={14} />}
                    />
                  </Stack>
                </Paper>
              </Grid.Col>

              <Grid.Col xs={12} md={4}>
                <Stack spacing="md">
                  {/* Preview */}
                  <Paper p="lg" radius="md" withBorder>
                    <Title order={4} mb="md">
                      Vista Previa
                    </Title>
                    <Center>
                      <Box
                        style={{
                          width: 200,
                          height: 200,
                          backgroundColor: qrConfig.colorLight,
                          border: '1px solid #dee2e6',
                          borderRadius: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <IconQrcode size={150} color={qrConfig.colorDark} />
                      </Box>
                    </Center>
                    <Text size="sm" color="gray.6" mt="sm" align="center">
                      {qrConfig.text ? `Contenido: ${qrConfig.text.substring(0, 30)}...` : 'Ingresa contenido para ver la vista previa'}
                    </Text>
                  </Paper>

                  {/* Configuration Summary */}
                  <Paper p="lg" radius="md" withBorder>
                    <Title order={4} mb="md">
                      Configuración
                    </Title>
                    <Stack spacing="xs">
                      <Group position="apart">
                        <Text size="sm" color="gray.6">Tamaño:</Text>
                        <Text size="sm">{qrConfig.size}px</Text>
                      </Group>
                      <Group position="apart">
                        <Text size="sm" color="gray.6">Corrección:</Text>
                        <Text size="sm">{qrConfig.errorCorrection}</Text>
                      </Group>
                      <Group position="apart">
                        <Text size="sm" color="gray.6">Formato:</Text>
                        <Text size="sm">{qrConfig.format.toUpperCase()}</Text>
                      </Group>
                      <Group position="apart">
                        <Text size="sm" color="gray.6">Margen:</Text>
                        <Text size="sm">{qrConfig.margin}px</Text>
                      </Group>
                    </Stack>
                  </Paper>

                  {/* Generate Button */}
                  <Button
                    fullWidth
                    leftIcon={<IconWand size={16} />}
                    onClick={handleQrGeneration}
                    disabled={!qrConfig.text.trim() || isGenerating}
                    loading={isGenerating}
                    size="md"
                  >
                    {isGenerating ? 'Generando...' : 'Generar Código QR'}
                  </Button>

                  {isGenerating && (
                    <Progress
                      value={generationProgress}
                      size="sm"
                      color="blue"
                      animate
                    />
                  )}
                </Stack>
              </Grid.Col>
            </Grid>
          )}

          {/* Templates Generator */}
          {generatorType === 'templates' && (
            <Tabs value={activeTab} onTabChange={setActiveTab}>
              <Tabs.List>
                <Tabs.Tab value="templates" icon={<IconTemplate size={16} />}>
                  Plantillas Existentes
                </Tabs.Tab>
                <Tabs.Tab value="create" icon={<IconPlus size={16} />}>
                  Crear Plantilla
                </Tabs.Tab>
                <Tabs.Tab value="editor" icon={<IconEdit size={16} />}>
                  Editor Avanzado
                </Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="templates" pt="md">
                <Grid>
                  {templates.map((template) => (
                    <Grid.Col key={template.id} xs={12} sm={6} md={4}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Card
                          p="md"
                          radius="md"
                          withBorder
                          style={{
                            height: '100%',
                            cursor: 'pointer',
                            border: selectedTemplate?.id === template.id ? '2px solid #339af0' : undefined,
                          }}
                          onClick={() => setSelectedTemplate(template)}
                        >
                          <Stack spacing="sm">
                            <Group position="apart">
                              <ThemeIcon size="lg" variant="light" color="blue">
                                <IconTemplate size={20} />
                              </ThemeIcon>
                              <Badge size="sm" variant="light">
                                {categories.find(c => c.value === template.category)?.label}
                              </Badge>
                            </Group>
                            
                            <div>
                              <Text size="sm" weight={500} mb="xs">
                                {template.name}
                              </Text>
                              <Text size="xs" color="gray.6" lineClamp={2}>
                                {template.description}
                              </Text>
                            </div>

                            <Group spacing="xs">
                              {template.fields.slice(0, 3).map(field => (
                                <Badge key={field} size="xs" variant="outline">
                                  {field}
                                </Badge>
                              ))}
                              {template.fields.length > 3 && (
                                <Badge size="xs" variant="outline">
                                  +{template.fields.length - 3}
                                </Badge>
                              )}
                            </Group>

                            <Group spacing="xs" mt="auto">
                              <Group spacing="xs">
                                <IconStar size={12} color="orange" />
                                <Text size="xs">{template.rating}</Text>
                              </Group>
                              <Group spacing="xs">
                                <IconDownload size={12} color="gray" />
                                <Text size="xs">{template.downloads}</Text>
                              </Group>
                            </Group>
                          </Stack>
                        </Card>
                      </motion.div>
                    </Grid.Col>
                  ))}
                </Grid>

                {selectedTemplate && (
                  <Paper p="lg" radius="md" withBorder mt="md">
                    <Group position="apart" mb="md">
                      <Title order={4}>
                        Configurar: {selectedTemplate.name}
                      </Title>
                      <Group spacing="sm">
                        <Button
                          variant="light"
                          leftIcon={<IconEye size={16} />}
                          onClick={() => setPreviewOpened(true)}
                        >
                          Vista Previa
                        </Button>
                        <Button
                          leftIcon={<IconWand size={16} />}
                          onClick={handleTemplateGeneration}
                          disabled={isGenerating}
                          loading={isGenerating}
                        >
                          Generar Documento
                        </Button>
                      </Group>
                    </Group>

                    <Grid>
                      {selectedTemplate.fields.map((field, index) => (
                        <Grid.Col key={field} xs={12} sm={6} md={4}>
                          <TextInput
                            label={field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            placeholder={`Ingresa ${field}`}
                            value={templateConfig.variables[field] || ''}
                            onChange={(event) => setTemplateConfig(prev => ({
                              ...prev,
                              variables: {
                                ...prev.variables,
                                [field]: event.target.value
                              }
                            }))}
                          />
                        </Grid.Col>
                      ))}
                    </Grid>

                    {isGenerating && (
                      <Box mt="md">
                        <Text size="sm" mb="xs">
                          Generando documento...
                        </Text>
                        <Progress
                          value={generationProgress}
                          size="sm"
                          color="blue"
                          animate
                        />
                      </Box>
                    )}
                  </Paper>
                )}
              </Tabs.Panel>

              <Tabs.Panel value="create" pt="md">
                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Crear Nueva Plantilla
                  </Title>
                  <Stack spacing="md">
                    <Grid>
                      <Grid.Col xs={12} md={6}>
                        <TextInput
                          label="Nombre de la plantilla"
                          placeholder="Ej: Contrato de Servicios"
                          value={templateConfig.name}
                          onChange={(event) => setTemplateConfig(prev => ({ ...prev, name: event.target.value }))}
                          required
                        />
                      </Grid.Col>
                      <Grid.Col xs={12} md={6}>
                        <Select
                          label="Categoría"
                          placeholder="Selecciona una categoría"
                          data={categories}
                          value={templateConfig.category}
                          onChange={(value) => setTemplateConfig(prev => ({ ...prev, category: value }))}
                          required
                        />
                      </Grid.Col>
                    </Grid>

                    <Textarea
                      label="Descripción"
                      placeholder="Describe para qué se usa esta plantilla"
                      value={templateConfig.description}
                      onChange={(event) => setTemplateConfig(prev => ({ ...prev, description: event.target.value }))}
                      minRows={2}
                    />

                    <div>
                      <Group position="apart" mb="md">
                        <Text size="sm" weight={500}>
                          Campos del documento
                        </Text>
                        <Button
                          variant="light"
                          size="sm"
                          leftIcon={<IconPlus size={16} />}
                          onClick={addTemplateField}
                        >
                          Agregar Campo
                        </Button>
                      </Group>

                      <Stack spacing="sm">
                        {templateConfig.fields.map((field, index) => (
                          <Card key={index} p="sm" radius="md" withBorder>
                            <Grid>
                              <Grid.Col xs={12} sm={4}>
                                <TextInput
                                  label="Nombre del campo"
                                  placeholder="Ej: nombre_cliente"
                                  value={field.name}
                                  onChange={(event) => updateTemplateField(index, 'name', event.target.value)}
                                  size="sm"
                                />
                              </Grid.Col>
                              <Grid.Col xs={12} sm={3}>
                                <Select
                                  label="Tipo"
                                  data={[
                                    { value: 'text', label: 'Texto' },
                                    { value: 'number', label: 'Número' },
                                    { value: 'date', label: 'Fecha' },
                                    { value: 'email', label: 'Email' },
                                    { value: 'textarea', label: 'Texto largo' },
                                  ]}
                                  value={field.type}
                                  onChange={(value) => updateTemplateField(index, 'type', value)}
                                  size="sm"
                                />
                              </Grid.Col>
                              <Grid.Col xs={12} sm={4}>
                                <TextInput
                                  label="Placeholder"
                                  placeholder="Texto de ayuda"
                                  value={field.placeholder}
                                  onChange={(event) => updateTemplateField(index, 'placeholder', event.target.value)}
                                  size="sm"
                                />
                              </Grid.Col>
                              <Grid.Col xs={12} sm={1}>
                                <div style={{ marginTop: '24px' }}>
                                  <ActionIcon
                                    color="red"
                                    variant="light"
                                    onClick={() => removeTemplateField(index)}
                                  >
                                    <IconTrash size={16} />
                                  </ActionIcon>
                                </div>
                              </Grid.Col>
                            </Grid>
                            <Checkbox
                              label="Campo obligatorio"
                              checked={field.required}
                              onChange={(event) => updateTemplateField(index, 'required', event.target.checked)}
                              mt="sm"
                            />
                          </Card>
                        ))}
                      </Stack>
                    </div>

                    <Group position="right">
                      <Button variant="light">
                        Cancelar
                      </Button>
                      <Button
                        leftIcon={<IconCheck size={16} />}
                        disabled={!templateConfig.name || !templateConfig.category}
                      >
                        Crear Plantilla
                      </Button>
                    </Group>
                  </Stack>
                </Paper>
              </Tabs.Panel>

              <Tabs.Panel value="editor" pt="md">
                <Paper p="lg" radius="md" withBorder>
                  <Title order={4} mb="md">
                    Editor de Plantillas HTML/CSS
                  </Title>
                  <Alert icon={<IconInfoCircle size={16} />} title="Funcionalidad avanzada" color="blue" mb="md">
                    <Text size="sm">
                      Este editor permite crear plantillas personalizadas usando HTML y CSS. 
                      Usa variables como {'{{nombre}}'} para crear campos dinámicos.
                    </Text>
                  </Alert>
                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <Stack spacing="md">
                        <div>
                          <Text size="sm" weight={500} mb="xs">
                            HTML Template
                          </Text>
                          <Textarea
                            placeholder="Ingresa el HTML de tu plantilla..."
                            value={templateConfig.html}
                            onChange={(event) => setTemplateConfig(prev => ({ ...prev, html: event.target.value }))}
                            minRows={10}
                            style={{ fontFamily: 'monospace' }}
                          />
                        </div>
                        <div>
                          <Text size="sm" weight={500} mb="xs">
                            CSS Styles
                          </Text>
                          <Textarea
                            placeholder="Ingresa los estilos CSS..."
                            value={templateConfig.css}
                            onChange={(event) => setTemplateConfig(prev => ({ ...prev, css: event.target.value }))}
                            minRows={8}
                            style={{ fontFamily: 'monospace' }}
                          />
                        </div>
                      </Stack>
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <div>
                        <Text size="sm" weight={500} mb="xs">
                          Vista Previa
                        </Text>
                        <Box
                          style={{
                            border: '1px solid #dee2e6',
                            borderRadius: '8px',
                            padding: '16px',
                            minHeight: '400px',
                            backgroundColor: 'white',
                          }}
                        >
                          <Text size="sm" color="gray.6" align="center">
                            La vista previa aparecerá aquí
                          </Text>
                        </Box>
                      </div>
                    </Grid.Col>
                  </Grid>
                  <Group position="right" mt="md">
                    <Button variant="light" leftIcon={<IconEye size={16} />}>
                      Previsualizar
                    </Button>
                    <Button leftIcon={<IconCheck size={16} />}>
                      Guardar Plantilla
                    </Button>
                  </Group>
                </Paper>
              </Tabs.Panel>
            </Tabs>
          )}

          {/* Document Generator */}
          {generatorType === 'documents' && (
            <Paper p="lg" radius="md" withBorder>
              <Title order={3} mb="lg">
                Generador de Documentos Automático
              </Title>
              <Alert icon={<IconInfoCircle size={16} />} title="Próximamente" color="blue">
                <Text size="sm">
                  Esta funcionalidad permitirá generar documentos automáticamente basados en 
                  datos de la base de datos y reglas predefinidas.
                </Text>
              </Alert>
            </Paper>
          )}

          {/* Generated Files */}
          {generatedFiles.length > 0 && (
            <Paper p="lg" radius="md" withBorder>
              <Title order={3} mb="lg">
                Archivos Generados
              </Title>
              <Grid>
                {generatedFiles.map((file) => (
                  <Grid.Col key={file.id} xs={12} sm={6} md={4}>
                    <Card p="md" radius="md" withBorder>
                      <Group position="apart" mb="sm">
                        <ThemeIcon size="lg" variant="light" color="green">
                          {file.type === 'qr' ? <IconQrcode size={20} /> : <IconFileText size={20} />}
                        </ThemeIcon>
                        <Badge size="sm" color="green">
                          Listo
                        </Badge>
                      </Group>
                      <Stack spacing="xs">
                        <Text size="sm" weight={500}>
                          {file.name}
                        </Text>
                        <Text size="xs" color="gray.6">
                          {file.size} " {new Date(file.createdAt).toLocaleString()}
                        </Text>
                        <Group spacing="xs" mt="sm">
                          <Button
                            variant="light"
                            size="xs"
                            leftIcon={<IconDownload size={12} />}
                            fullWidth
                          >
                            Descargar
                          </Button>
                          <ActionIcon variant="light" size="sm">
                            <IconEye size={12} />
                          </ActionIcon>
                          <ActionIcon variant="light" size="sm">
                            <IconShare size={12} />
                          </ActionIcon>
                        </Group>
                      </Stack>
                    </Card>
                  </Grid.Col>
                ))}
              </Grid>
            </Paper>
          )}
        </Stack>
      </motion.div>

      {/* Preview Modal */}
      <Modal
        opened={previewOpened}
        onClose={() => setPreviewOpened(false)}
        title="Vista Previa de Plantilla"
        size="lg"
        centered
      >
        {selectedTemplate && (
          <Stack spacing="md">
            <Group>
              <ThemeIcon size="lg" variant="light" color="blue">
                <IconTemplate size={20} />
              </ThemeIcon>
              <div>
                <Text size="lg" weight={500}>
                  {selectedTemplate.name}
                </Text>
                <Text size="sm" color="gray.6">
                  {selectedTemplate.description}
                </Text>
              </div>
            </Group>
            
            <Box
              style={{
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                padding: '20px',
                minHeight: '400px',
                backgroundColor: 'white',
              }}
            >
              <Text size="sm" color="gray.6" align="center">
                Vista previa del documento generado
              </Text>
            </Box>
            
            <Group position="right">
              <Button variant="light" onClick={() => setPreviewOpened(false)}>
                Cerrar
              </Button>
              <Button leftIcon={<IconDownload size={16} />}>
                Descargar PDF
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Container>
  );
};

export default Generator;