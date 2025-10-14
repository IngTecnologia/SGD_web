import React, { useState } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  Group,
  Stack,
  TextInput,
  Select,
  Button,
  Grid,
  Card,
  Badge,
  ActionIcon,
  Table,
  Pagination,
  Modal,
  Image,
  Tabs,
  MultiSelect,
  DatePicker,
  RangeSlider,
  Switch,
  Highlight,
  ScrollArea,
  Center,
  Box,
  Divider,
  ThemeIcon,
  Timeline,
  Tooltip,
  Menu,
} from '@mantine/core';
import {
  IconSearch,
  IconFilter,
  IconSortAscending,
  IconSortDescending,
  IconEye,
  IconDownload,
  IconShare,
  IconQrcode,
  IconFileText,
  IconFileCertificate,
  IconFileDescription,
  IconFile,
  IconCalendar,
  IconTag,
  IconUser,
  IconClock,
  IconExternalLink,
  IconX,
  IconAdjustments,
  IconList,
  IconLayoutGrid,
  IconRefresh,
  IconStar,
  IconStarFilled,
  IconDots,
  IconEdit,
  IconTrash,
  IconHistory,
  IconUpload,
} from '@tabler/icons-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';

const Search = () => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    documentType: '',
    category: '',
    dateRange: [null, null],
    tags: [],
    priority: '',
    fileSize: [0, 100],
    status: '',
  });
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('table');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [previewOpened, setPreviewOpened] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [favorites, setFavorites] = useState(['doc-1', 'doc-3']);

  // Mock data para documentos
  const documents = [
    {
      id: 'doc-1',
      title: 'Contrato de Trabajo - Mar�a Garc�a',
      type: 'contract',
      category: 'hr',
      description: 'Contrato de trabajo para la nueva empleada Mar�a Garc�a en el departamento de Recursos Humanos.',
      tags: ['contrato', 'empleado', 'recursos-humanos'],
      priority: 'high',
      fileType: 'pdf',
      fileSize: 2.4,
      uploadDate: '2024-01-15',
      uploadedBy: 'Ana L�pez',
      qrCode: 'QR-CTR-001',
      status: 'active',
      lastModified: '2024-01-20',
      views: 12,
      downloads: 3,
    },
    {
      id: 'doc-2',
      title: 'Informe Mensual Enero 2024',
      type: 'report',
      category: 'finance',
      description: 'Informe financiero mensual correspondiente al mes de enero 2024.',
      tags: ['informe', 'finanzas', 'mensual'],
      priority: 'medium',
      fileType: 'xlsx',
      fileSize: 1.2,
      uploadDate: '2024-02-01',
      uploadedBy: 'Carlos Ruiz',
      qrCode: 'QR-INF-002',
      status: 'active',
      lastModified: '2024-02-01',
      views: 8,
      downloads: 2,
    },
    {
      id: 'doc-3',
      title: 'Pol�tica de Seguridad Actualizada',
      type: 'policy',
      category: 'compliance',
      description: 'Documento con las nuevas pol�ticas de seguridad de la empresa.',
      tags: ['pol�tica', 'seguridad', 'compliance'],
      priority: 'high',
      fileType: 'docx',
      fileSize: 0.8,
      uploadDate: '2024-01-10',
      uploadedBy: 'Juan P�rez',
      qrCode: 'QR-POL-003',
      status: 'active',
      lastModified: '2024-01-25',
      views: 25,
      downloads: 15,
    },
    {
      id: 'doc-4',
      title: 'Manual de Procedimientos',
      type: 'manual',
      category: 'operations',
      description: 'Manual completo de procedimientos operativos de la empresa.',
      tags: ['manual', 'procedimientos', 'operaciones'],
      priority: 'medium',
      fileType: 'pdf',
      fileSize: 4.1,
      uploadDate: '2024-01-05',
      uploadedBy: 'Luis Mart�n',
      qrCode: 'QR-MAN-004',
      status: 'archived',
      lastModified: '2024-01-15',
      views: 18,
      downloads: 8,
    },
  ];

  const documentTypes = [
    { value: 'contract', label: 'Contrato' },
    { value: 'invoice', label: 'Factura' },
    { value: 'report', label: 'Informe' },
    { value: 'certificate', label: 'Certificado' },
    { value: 'policy', label: 'Pol�tica' },
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

  const availableTags = [
    { value: 'contrato', label: 'Contrato' },
    { value: 'empleado', label: 'Empleado' },
    { value: 'recursos-humanos', label: 'Recursos Humanos' },
    { value: 'informe', label: 'Informe' },
    { value: 'finanzas', label: 'Finanzas' },
    { value: 'pol�tica', label: 'Pol�tica' },
    { value: 'seguridad', label: 'Seguridad' },
    { value: 'manual', label: 'Manual' },
    { value: 'procedimientos', label: 'Procedimientos' },
  ];

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'pdf':
        return <IconFileCertificate size={20} color="red" />;
      case 'docx':
      case 'doc':
        return <IconFileText size={20} color="blue" />;
      case 'xlsx':
      case 'xls':
        return <IconFileDescription size={20} color="green" />;
      default:
        return <IconFile size={20} color="gray" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'green';
      default:
        return 'gray';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'archived':
        return 'gray';
      case 'pending':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const handleSearch = () => {
    setLoading(true);
    // Simular b�squeda
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const clearFilters = () => {
    setFilters({
      documentType: '',
      category: '',
      dateRange: [null, null],
      tags: [],
      priority: '',
      fileSize: [0, 100],
      status: '',
    });
    setSearchQuery('');
  };

  const toggleFavorite = (docId) => {
    setFavorites(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const openPreview = (document) => {
    setSelectedDocument(document);
    setPreviewOpened(true);
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = searchQuery === '' || 
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = filters.documentType === '' || doc.type === filters.documentType;
    const matchesCategory = filters.category === '' || doc.category === filters.category;
    const matchesPriority = filters.priority === '' || doc.priority === filters.priority;
    const matchesStatus = filters.status === '' || doc.status === filters.status;
    const matchesTags = filters.tags.length === 0 || 
      filters.tags.some(tag => doc.tags.includes(tag));

    return matchesSearch && matchesType && matchesCategory && matchesPriority && matchesStatus && matchesTags;
  });

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'title':
        aValue = a.title;
        bValue = b.title;
        break;
      case 'date':
        aValue = new Date(a.uploadDate);
        bValue = new Date(b.uploadDate);
        break;
      case 'size':
        aValue = a.fileSize;
        bValue = b.fileSize;
        break;
      case 'views':
        aValue = a.views;
        bValue = b.views;
        break;
      default:
        aValue = a.uploadDate;
        bValue = b.uploadDate;
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const paginatedDocuments = sortedDocuments.slice((page - 1) * 10, page * 10);

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
                  Buscar Documentos
                </Title>
                <Text color="gray.6" size="lg">
                  Encuentra documentos en el sistema de gesti�n documental
                </Text>
              </div>
              <Badge size="lg" variant="light" color="blue">
                {filteredDocuments.length} documentos encontrados
              </Badge>
            </Group>
          </Paper>

          {/* Search Bar */}
          <Paper p="lg" radius="md" withBorder>
            <Stack spacing="md">
              <Group spacing="md">
                <TextInput
                  placeholder="Buscar por t�tulo, descripci�n o etiquetas..."
                  icon={<IconSearch size={16} />}
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  style={{ flex: 1 }}
                  size="md"
                />
                <Button
                  onClick={handleSearch}
                  loading={loading}
                  leftIcon={<IconSearch size={16} />}
                  size="md"
                >
                  Buscar
                </Button>
                <Button
                  variant="light"
                  onClick={() => setAdvancedFilters(!advancedFilters)}
                  leftIcon={<IconFilter size={16} />}
                  size="md"
                >
                  Filtros
                </Button>
              </Group>

              {/* Advanced Filters */}
              <AnimatePresence>
                {advancedFilters && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Paper p="md" radius="md" withBorder style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                      <Grid>
                        <Grid.Col xs={12} sm={6} md={3}>
                          <Select
                            label="Tipo de Documento"
                            placeholder="Todos los tipos"
                            data={documentTypes}
                            value={filters.documentType}
                            onChange={(value) => setFilters(prev => ({ ...prev, documentType: value }))}
                            clearable
                          />
                        </Grid.Col>
                        <Grid.Col xs={12} sm={6} md={3}>
                          <Select
                            label="Categor�a"
                            placeholder="Todas las categor�as"
                            data={categories}
                            value={filters.category}
                            onChange={(value) => setFilters(prev => ({ ...prev, category: value }))}
                            clearable
                          />
                        </Grid.Col>
                        <Grid.Col xs={12} sm={6} md={3}>
                          <Select
                            label="Prioridad"
                            placeholder="Todas las prioridades"
                            data={[
                              { value: 'high', label: 'Alta' },
                              { value: 'medium', label: 'Media' },
                              { value: 'low', label: 'Baja' },
                            ]}
                            value={filters.priority}
                            onChange={(value) => setFilters(prev => ({ ...prev, priority: value }))}
                            clearable
                          />
                        </Grid.Col>
                        <Grid.Col xs={12} sm={6} md={3}>
                          <Select
                            label="Estado"
                            placeholder="Todos los estados"
                            data={[
                              { value: 'active', label: 'Activo' },
                              { value: 'archived', label: 'Archivado' },
                              { value: 'pending', label: 'Pendiente' },
                            ]}
                            value={filters.status}
                            onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
                            clearable
                          />
                        </Grid.Col>
                        <Grid.Col xs={12} md={6}>
                          <MultiSelect
                            label="Etiquetas"
                            placeholder="Selecciona etiquetas"
                            data={availableTags}
                            value={filters.tags}
                            onChange={(value) => setFilters(prev => ({ ...prev, tags: value }))}
                            clearable
                            searchable
                          />
                        </Grid.Col>
                        <Grid.Col xs={12} md={6}>
                          <div>
                            <Text size="sm" weight={500} mb="xs">
                              Tama�o de archivo (MB)
                            </Text>
                            <RangeSlider
                              min={0}
                              max={100}
                              step={1}
                              value={filters.fileSize}
                              onChange={(value) => setFilters(prev => ({ ...prev, fileSize: value }))}
                              marks={[
                                { value: 0, label: '0 MB' },
                                { value: 25, label: '25 MB' },
                                { value: 50, label: '50 MB' },
                                { value: 75, label: '75 MB' },
                                { value: 100, label: '100 MB' },
                              ]}
                            />
                          </div>
                        </Grid.Col>
                      </Grid>
                      <Group position="apart" mt="md">
                        <Button variant="subtle" onClick={clearFilters} leftIcon={<IconX size={16} />}>
                          Limpiar filtros
                        </Button>
                        <Text size="sm" color="gray.6">
                          {filteredDocuments.length} documentos coinciden con los filtros
                        </Text>
                      </Group>
                    </Paper>
                  </motion.div>
                )}
              </AnimatePresence>
            </Stack>
          </Paper>

          {/* Results Header */}
          <Paper p="lg" radius="md" withBorder>
            <Group position="apart">
              <Group spacing="md">
                <Text size="sm" weight={500}>
                  Resultados: {filteredDocuments.length} documentos
                </Text>
                <Select
                  placeholder="Ordenar por"
                  data={[
                    { value: 'date', label: 'Fecha de subida' },
                    { value: 'title', label: 'T�tulo' },
                    { value: 'size', label: 'Tama�o' },
                    { value: 'views', label: 'Visualizaciones' },
                  ]}
                  value={sortBy}
                  onChange={(value) => setSortBy(value)}
                  size="sm"
                  style={{ minWidth: 150 }}
                />
                <ActionIcon
                  variant="subtle"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  size="sm"
                >
                  {sortOrder === 'asc' ? <IconSortAscending size={16} /> : <IconSortDescending size={16} />}
                </ActionIcon>
              </Group>
              <Group spacing="sm">
                <ActionIcon
                  variant={viewMode === 'table' ? 'filled' : 'subtle'}
                  onClick={() => setViewMode('table')}
                  size="sm"
                >
                  <IconList size={16} />
                </ActionIcon>
                <ActionIcon
                  variant={viewMode === 'grid' ? 'filled' : 'subtle'}
                  onClick={() => setViewMode('grid')}
                  size="sm"
                >
                  <IconLayoutGrid size={16} />
                </ActionIcon>
              </Group>
            </Group>
          </Paper>

          {/* Results */}
          <Paper radius="md" withBorder>
            {viewMode === 'table' ? (
              <ScrollArea>
                <Table highlightOnHover>
                  <thead>
                    <tr>
                      <th>Documento</th>
                      <th>Tipo</th>
                      <th>Categor�a</th>
                      <th>Prioridad</th>
                      <th>Fecha</th>
                      <th>Tama�o</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedDocuments.map((doc) => (
                      <tr key={doc.id}>
                        <td>
                          <Group spacing="sm">
                            <ActionIcon
                              variant="subtle"
                              size="sm"
                              onClick={() => toggleFavorite(doc.id)}
                            >
                              {favorites.includes(doc.id) ? 
                                <IconStarFilled size={16} color="orange" /> : 
                                <IconStar size={16} />
                              }
                            </ActionIcon>
                            {getFileIcon(doc.fileType)}
                            <div>
                              <Text size="sm" weight={500}>
                                <Highlight highlight={searchQuery} highlightColor="yellow">
                                  {doc.title}
                                </Highlight>
                              </Text>
                              <Text size="xs" color="gray.6">
                                {doc.qrCode}
                              </Text>
                            </div>
                          </Group>
                        </td>
                        <td>
                          <Text size="sm">
                            {documentTypes.find(t => t.value === doc.type)?.label}
                          </Text>
                        </td>
                        <td>
                          <Text size="sm">
                            {categories.find(c => c.value === doc.category)?.label}
                          </Text>
                        </td>
                        <td>
                          <Badge size="sm" color={getPriorityColor(doc.priority)}>
                            {doc.priority === 'high' ? 'Alta' : doc.priority === 'medium' ? 'Media' : 'Baja'}
                          </Badge>
                        </td>
                        <td>
                          <Text size="sm">
                            {new Date(doc.uploadDate).toLocaleDateString()}
                          </Text>
                        </td>
                        <td>
                          <Text size="sm">
                            {doc.fileSize} MB
                          </Text>
                        </td>
                        <td>
                          <Badge size="sm" color={getStatusColor(doc.status)}>
                            {doc.status === 'active' ? 'Activo' : doc.status === 'archived' ? 'Archivado' : 'Pendiente'}
                          </Badge>
                        </td>
                        <td>
                          <Group spacing="xs">
                            <Tooltip label="Ver documento">
                              <ActionIcon
                                variant="subtle"
                                size="sm"
                                onClick={() => openPreview(doc)}
                              >
                                <IconEye size={16} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Descargar">
                              <ActionIcon variant="subtle" size="sm">
                                <IconDownload size={16} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Compartir">
                              <ActionIcon variant="subtle" size="sm">
                                <IconShare size={16} />
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
                                  Editar metadatos
                                </Menu.Item>
                                <Menu.Item icon={<IconHistory size={14} />}>
                                  Ver historial
                                </Menu.Item>
                                <Menu.Item icon={<IconQrcode size={14} />}>
                                  Generar QR
                                </Menu.Item>
                                <Menu.Divider />
                                <Menu.Item icon={<IconTrash size={14} />} color="red">
                                  Eliminar
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
            ) : (
              <Box p="lg">
                <Grid>
                  {paginatedDocuments.map((doc) => (
                    <Grid.Col key={doc.id} xs={12} sm={6} md={4} lg={3}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Card p="md" radius="md" withBorder style={{ height: '100%' }}>
                          <Group position="apart" mb="sm">
                            <ThemeIcon size="lg" variant="light" color="blue">
                              {getFileIcon(doc.fileType)}
                            </ThemeIcon>
                            <ActionIcon
                              variant="subtle"
                              size="sm"
                              onClick={() => toggleFavorite(doc.id)}
                            >
                              {favorites.includes(doc.id) ? 
                                <IconStarFilled size={16} color="orange" /> : 
                                <IconStar size={16} />
                              }
                            </ActionIcon>
                          </Group>
                          <Stack spacing="xs">
                            <Text size="sm" weight={500} lineClamp={2}>
                              <Highlight highlight={searchQuery} highlightColor="yellow">
                                {doc.title}
                              </Highlight>
                            </Text>
                            <Text size="xs" color="gray.6" lineClamp={2}>
                              {doc.description}
                            </Text>
                            <Group spacing="xs">
                              <Badge size="xs" color={getPriorityColor(doc.priority)}>
                                {doc.priority === 'high' ? 'Alta' : doc.priority === 'medium' ? 'Media' : 'Baja'}
                              </Badge>
                              <Badge size="xs" color={getStatusColor(doc.status)}>
                                {doc.status === 'active' ? 'Activo' : doc.status === 'archived' ? 'Archivado' : 'Pendiente'}
                              </Badge>
                            </Group>
                            <Group spacing="xs" mt="sm">
                              <Text size="xs" color="gray.6">
                                {doc.fileSize} MB
                              </Text>
                              <Text size="xs" color="gray.6">
                                {new Date(doc.uploadDate).toLocaleDateString()}
                              </Text>
                            </Group>
                            <Group spacing="xs" mt="sm">
                              <Button
                                variant="light"
                                size="xs"
                                leftIcon={<IconEye size={12} />}
                                onClick={() => openPreview(doc)}
                                fullWidth
                              >
                                Ver
                              </Button>
                              <ActionIcon variant="light" size="sm">
                                <IconDownload size={12} />
                              </ActionIcon>
                              <ActionIcon variant="light" size="sm">
                                <IconShare size={12} />
                              </ActionIcon>
                            </Group>
                          </Stack>
                        </Card>
                      </motion.div>
                    </Grid.Col>
                  ))}
                </Grid>
              </Box>
            )}

            {/* Pagination */}
            {filteredDocuments.length > 10 && (
              <Center p="lg">
                <Pagination
                  total={Math.ceil(filteredDocuments.length / 10)}
                  value={page}
                  onChange={setPage}
                />
              </Center>
            )}
          </Paper>
        </Stack>
      </motion.div>

      {/* Document Preview Modal */}
      <Modal
        opened={previewOpened}
        onClose={() => setPreviewOpened(false)}
        title={selectedDocument?.title}
        size="lg"
        centered
      >
        {selectedDocument && (
          <Stack spacing="md">
            <Group>
              <ThemeIcon size="lg" variant="light" color="blue">
                {getFileIcon(selectedDocument.fileType)}
              </ThemeIcon>
              <div style={{ flex: 1 }}>
                <Text size="lg" weight={500}>
                  {selectedDocument.title}
                </Text>
                <Text size="sm" color="gray.6">
                  {selectedDocument.qrCode}
                </Text>
              </div>
              <Group spacing="xs">
                <Badge color={getPriorityColor(selectedDocument.priority)}>
                  {selectedDocument.priority === 'high' ? 'Alta' : 
                   selectedDocument.priority === 'medium' ? 'Media' : 'Baja'}
                </Badge>
                <Badge color={getStatusColor(selectedDocument.status)}>
                  {selectedDocument.status === 'active' ? 'Activo' : 
                   selectedDocument.status === 'archived' ? 'Archivado' : 'Pendiente'}
                </Badge>
              </Group>
            </Group>

            <Divider />

            <Tabs defaultValue="info">
              <Tabs.List>
                <Tabs.Tab value="info">Informaci�n</Tabs.Tab>
                <Tabs.Tab value="activity">Actividad</Tabs.Tab>
                <Tabs.Tab value="qr">C�digo QR</Tabs.Tab>
              </Tabs.List>

              <Tabs.Panel value="info" pt="sm">
                <Stack spacing="sm">
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Descripci�n:
                    </Text>
                    <Text size="sm">{selectedDocument.description}</Text>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Tipo:
                    </Text>
                    <Text size="sm">
                      {documentTypes.find(t => t.value === selectedDocument.type)?.label}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Categor�a:
                    </Text>
                    <Text size="sm">
                      {categories.find(c => c.value === selectedDocument.category)?.label}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Etiquetas:
                    </Text>
                    <Group spacing="xs">
                      {selectedDocument.tags.map(tag => (
                        <Badge key={tag} size="sm" variant="light">
                          {tag}
                        </Badge>
                      ))}
                    </Group>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Tama�o:
                    </Text>
                    <Text size="sm">{selectedDocument.fileSize} MB</Text>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Subido por:
                    </Text>
                    <Text size="sm">{selectedDocument.uploadedBy}</Text>
                  </Group>
                  <Group>
                    <Text size="sm" weight={500} style={{ minWidth: 100 }}>
                      Fecha:
                    </Text>
                    <Text size="sm">{new Date(selectedDocument.uploadDate).toLocaleDateString()}</Text>
                  </Group>
                </Stack>
              </Tabs.Panel>

              <Tabs.Panel value="activity" pt="sm">
                <Timeline active={2} bulletSize={24} lineWidth={2}>
                  <Timeline.Item
                    bullet={<IconUpload size={12} />}
                    title="Documento subido"
                  >
                    <Text color="gray.6" size="sm">
                      {selectedDocument.uploadedBy} subi� el documento
                    </Text>
                    <Text size="xs" color="gray.6">
                      {new Date(selectedDocument.uploadDate).toLocaleDateString()}
                    </Text>
                  </Timeline.Item>
                  <Timeline.Item
                    bullet={<IconQrcode size={12} />}
                    title="C�digo QR generado"
                  >
                    <Text color="gray.6" size="sm">
                      Se gener� el c�digo QR {selectedDocument.qrCode}
                    </Text>
                    <Text size="xs" color="gray.6">
                      {new Date(selectedDocument.uploadDate).toLocaleDateString()}
                    </Text>
                  </Timeline.Item>
                  <Timeline.Item
                    bullet={<IconEye size={12} />}
                    title="Visualizaciones"
                  >
                    <Text color="gray.6" size="sm">
                      El documento ha sido visto {selectedDocument.views} veces
                    </Text>
                    <Text size="xs" color="gray.6">
                      �ltima visualizaci�n: {new Date(selectedDocument.lastModified).toLocaleDateString()}
                    </Text>
                  </Timeline.Item>
                </Timeline>
              </Tabs.Panel>

              <Tabs.Panel value="qr" pt="sm">
                <Center>
                  <Stack spacing="md" style={{ textAlign: 'center' }}>
                    <Box
                      style={{
                        width: 200,
                        height: 200,
                        backgroundColor: '#f8f9fa',
                        border: '1px solid #dee2e6',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <IconQrcode size={100} color="gray" />
                    </Box>
                    <Text size="sm" weight={500}>
                      {selectedDocument.qrCode}
                    </Text>
                    <Button variant="light" leftIcon={<IconDownload size={16} />}>
                      Descargar QR
                    </Button>
                  </Stack>
                </Center>
              </Tabs.Panel>
            </Tabs>

            <Group position="apart" mt="md">
              <Button variant="light" leftIcon={<IconDownload size={16} />}>
                Descargar Documento
              </Button>
              <Button variant="light" leftIcon={<IconShare size={16} />}>
                Compartir
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Container>
  );
};

export default Search;