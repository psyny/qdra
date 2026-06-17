import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { EntityTypeEditor } from './EntityTypeEditor'
import * as templatesApi from '../api/templates'

// Mock the templates API
vi.mock('../api/templates')

describe('EntityTypeEditor', () => {
  const mockTemplateId = 'template-123'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(templatesApi.listEntityTypes).mockImplementation(() => new Promise(() => {}))
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    expect(screen.getByText('Loading entity types...')).toBeInTheDocument()
  })

  it('renders empty state when no entity types exist', async () => {
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue([])
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText(/No entity types defined yet/)).toBeInTheDocument()
    })
  })

  it('renders entity types list', async () => {
    const mockEntityTypes = [
      {
        id: 'et-1',
        project_template_id: mockTemplateId,
        kind: 'material',
        name: 'Item',
        description: 'A craftable item',
        sort_order: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameter_definitions: [],
      },
      {
        id: 'et-2',
        project_template_id: mockTemplateId,
        kind: 'recipe',
        name: 'Recipe',
        description: 'A crafting recipe',
        sort_order: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameter_definitions: [],
      },
    ]
    
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue(mockEntityTypes)
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Item')).toBeInTheDocument()
      expect(screen.getByText('Recipe')).toBeInTheDocument()
    })
  })

  it('shows create form when Add Entity Type button is clicked', async () => {
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue([])
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText(/No entity types defined yet/)).toBeInTheDocument()
    })
    
    fireEvent.click(screen.getByText('Add Entity Type'))
    
    expect(screen.getByText('Create Entity Type')).toBeInTheDocument()
    expect(screen.getByLabelText('Kind *')).toBeInTheDocument()
    expect(screen.getByLabelText('Name *')).toBeInTheDocument()
  })

  it('creates entity type when form is submitted', async () => {
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue([])
    vi.mocked(templatesApi.createEntityType).mockResolvedValue({
      id: 'new-et',
      project_template_id: mockTemplateId,
      kind: 'material',
      name: 'New Item',
      description: 'Test description',
      sort_order: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      parameter_definitions: [],
    })
    
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Entity Type'))
    })
    
    const nameInput = screen.getByLabelText('Name *')
    const descriptionInput = screen.getByLabelText('Description')
    
    fireEvent.change(nameInput, { target: { value: 'New Item' } })
    fireEvent.change(descriptionInput, { target: { value: 'Test description' } })
    
    fireEvent.click(screen.getByText('Create'))
    
    await waitFor(() => {
      expect(templatesApi.createEntityType).toHaveBeenCalledWith(
        mockTemplateId,
        {
          kind: 'material',
          name: 'New Item',
          description: 'Test description',
          sort_order: 0,
        }
      )
    })
  })

  it('shows recipe slot explanation for recipe entity types', async () => {
    const mockEntityTypes = [
      {
        id: 'et-1',
        project_template_id: mockTemplateId,
        kind: 'recipe',
        name: 'Crafting Recipe',
        description: 'A recipe',
        sort_order: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameter_definitions: [],
      },
    ]
    
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue(mockEntityTypes)
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Recipes can define runtime slots/)).toBeInTheDocument()
    })
  })

  it('expands parameter definitions when Parameters button is clicked', async () => {
    const mockEntityTypes = [
      {
        id: 'et-1',
        project_template_id: mockTemplateId,
        kind: 'material',
        name: 'Item',
        description: null,
        sort_order: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        parameter_definitions: [],
      },
    ]
    
    vi.mocked(templatesApi.listEntityTypes).mockResolvedValue(mockEntityTypes)
    vi.mocked(templatesApi.listParameterDefinitions).mockResolvedValue([])
    
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Item')).toBeInTheDocument()
    })
    
    fireEvent.click(screen.getByText('Parameters'))
    
    await waitFor(() => {
      expect(templatesApi.listParameterDefinitions).toHaveBeenCalledWith(mockTemplateId, 'et-1')
    })
  })

  it('shows error message when API call fails', async () => {
    vi.mocked(templatesApi.listEntityTypes).mockRejectedValue(new Error('API Error'))
    render(<EntityTypeEditor templateId={mockTemplateId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load entity types')).toBeInTheDocument()
    })
  })
})
