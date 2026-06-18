import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MaterialCatalogPage } from '../pages/MaterialCatalogPage';
import * as projectsApi from '../api/projects';
import * as entitiesApi from '../api/entities';

// Mock the API modules
jest.mock('../api/projects');
jest.mock('../api/entities');

const mockTemplate = {
  template: {
    id: 'template-1',
    name: 'Factory Template',
    description: 'Test template',
    version: 1,
    is_builtin: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  entity_types: [
    {
      id: 'entity-type-1',
      project_template_id: 'template-1',
      kind: 'material',
      name: 'Raw Material',
      description: 'Raw materials',
      sort_order: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      parameter_definitions: [],
    },
  ],
  parameter_definitions: [],
  views: [
    {
      id: 'view-1',
      project_template_id: 'template-1',
      view_key: 'material_catalog',
      label: 'Material Catalog',
      description: 'Materials',
      is_system: false,
      sort_order: 0,
      configs: [
        {
          id: 'config-1',
          view_id: 'view-1',
          entity_type_id: 'entity-type-1',
          filter_params: null,
          display_slots: [
            { source: 'parameter', domain: 'identity', key: 'name' },
            { source: 'parameter', domain: 'identity', key: 'category' },
          ],
          sort_order: 0,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ],
};

const mockEntities = [
  {
    id: 'entity-1',
    project_id: 'project-1',
    entity_type_id: 'entity-type-1',
    kind: 'material',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockEntityParameters = [
  {
    id: 'param-1',
    entity_id: 'entity-1',
    domain: 'identity',
    key: 'name',
    value_string: 'Steel',
    value_number: null,
    value_boolean: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'param-2',
    entity_id: 'entity-1',
    domain: 'identity',
    key: 'category',
    value_string: 'Metal',
    value_number: null,
    value_boolean: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

describe('MaterialCatalogPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithRouter = (projectId: string = 'project-1') => {
    return render(
      <BrowserRouter>
        <MaterialCatalogPage projectId={projectId} />
      </BrowserRouter>
    );
  };

  test('renders loading state initially', () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockImplementation(() => new Promise(() => {}));
    renderWithRouter();
    expect(screen.getByText('Loading material catalog...')).toBeInTheDocument();
  });

  test('renders material catalog after loading', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Raw Material')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Steel')).toBeInTheDocument();
  });

  test('shows group selection when multiple configs exist', async () => {
    const multiConfigTemplate = {
      ...mockTemplate,
      views: [
        {
          ...mockTemplate.views[0],
          configs: [
            { ...mockTemplate.views[0].configs[0], id: 'config-1' },
            { ...mockTemplate.views[0].configs[0], id: 'config-2', entity_type_id: 'entity-type-2' },
          ],
        },
      ],
    };
    
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(multiConfigTemplate);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Select a material group to view materials.')).toBeInTheDocument();
    });
  });

  test('auto-selects single config', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Raw Material')).toBeInTheDocument();
    });
    
    // Should not show group selection since there's only one config
    expect(screen.queryByText('Select a material group to view materials.')).not.toBeInTheDocument();
  });

  test('filters entities by search query', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Steel')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search materials...');
    fireEvent.change(searchInput, { target: { value: 'steel' } });
    
    // Should still show Steel since it matches
    expect(screen.getByText('Steel')).toBeInTheDocument();
  });

  test('shows empty state when no entities', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue([]);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('No materials found.')).toBeInTheDocument();
    });
  });

  test('shows error message on API failure', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockRejectedValue(new Error('API Error'));
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Could not load template')).toBeInTheDocument();
    });
  });

  test('navigates to new material form', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('+ New Material')).toBeInTheDocument();
    });
    
    const newButton = screen.getByText('+ New Material');
    expect(newButton).toHaveAttribute('href', '/projects/project-1/materials/new?configId=config-1');
  });

  test('navigates to edit material form', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });
    
    const editButton = screen.getByText('Edit');
    expect(editButton).toHaveAttribute('href', '/projects/project-1/materials/entity-1/edit?configId=config-1');
  });

  test('opens delete confirmation dialog', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    (entitiesApi.deleteEntity as jest.Mock).mockResolvedValue(undefined);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Delete'));
    
    await waitFor(() => {
      expect(screen.getByText('Delete Material')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
    });
  });

  test('deletes entity after confirmation', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    (entitiesApi.deleteEntity as jest.Mock).mockResolvedValue(undefined);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Delete'));
    
    await waitFor(() => {
      expect(screen.getByText('Delete')).toBeInTheDocument(); // Confirm button
    });
    
    fireEvent.click(screen.getAllByText('Delete')[1]); // Click confirm button
    
    await waitFor(() => {
      expect(entitiesApi.deleteEntity).toHaveBeenCalledWith('project-1', 'entity-1');
    });
  });

  test('cancels delete operation', async () => {
    (projectsApi.getProjectTemplate as jest.Mock).mockResolvedValue(mockTemplate);
    (entitiesApi.getEntitiesByViewConfig as jest.Mock).mockResolvedValue(mockEntities);
    (entitiesApi.getEntityParameters as jest.Mock).mockResolvedValue(mockEntityParameters);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Delete'));
    
    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Cancel'));
    
    await waitFor(() => {
      expect(screen.queryByText('Delete Material')).not.toBeInTheDocument();
    });
  });
});
