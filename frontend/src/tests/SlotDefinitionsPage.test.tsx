import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SlotDefinitionsPage } from '../pages/SlotDefinitionsPage';
import * as templatesApi from '../api/templates';

// Mock the API module
jest.mock('../api/templates');

const mockSlotGroups = [
  {
    id: 'group-1',
    entity_type_id: 'entity-type-1',
    kind: 'consumes',
    min_slots: 0,
    max_slots: 5,
    sort_order: 0,
    constraints: [],
    slot_definitions: [],
  },
];

describe('SlotDefinitionsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithRouter = () => {
    return render(
      <BrowserRouter>
        <SlotDefinitionsPage />
      </BrowserRouter>
    );
  };

  test('renders loading state initially', () => {
    (templatesApi.listSlotGroups as jest.Mock).mockImplementation(() => new Promise(() => {}));
    renderWithRouter();
    expect(screen.getByText('Loading slot definitions...')).toBeInTheDocument();
  });

  test('renders slot groups after loading', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Edit Slot Definitions')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Consumes')).toBeInTheDocument();
  });

  test('shows empty state for missing slot groups', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue([]);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('No Consumes group defined')).toBeInTheDocument();
    });
    expect(screen.getByText('No Requires group defined')).toBeInTheDocument();
    expect(screen.getByText('No Produces group defined')).toBeInTheDocument();
  });

  test('opens create slot group form', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue([]);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Add Slot Group')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Slot Group'));
    expect(screen.getByText('Create Slot Group')).toBeInTheDocument();
  });

  test('creates a new slot group', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue([]);
    (templatesApi.createSlotGroup as jest.Mock).mockResolvedValue(mockSlotGroups[0]);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Add Slot Group')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Slot Group'));
    
    const kindSelect = screen.getByLabelText('Kind *');
    fireEvent.change(kindSelect, { target: { value: 'consumes' } });
    
    const createButton = screen.getByText('Create');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(templatesApi.createSlotGroup).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ kind: 'consumes' })
      );
    });
  });

  test('expands slot group to show details', async () => {
    const groupWithDefinitions = {
      ...mockSlotGroups[0],
      slot_definitions: [
        {
          id: 'def-1',
          slot_group_id: 'group-1',
          slot_key: '1',
          min_occurrences: 1,
          max_occurrences: 1,
          sort_order: 0,
          constraints: [],
        },
      ],
    };
    
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue([groupWithDefinitions]);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    expect(screen.getByText('Slot Definitions')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  test('opens create slot definition form', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Add Slot Definition')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Slot Definition'));
    expect(screen.getByText('Create Slot Definition')).toBeInTheDocument();
  });

  test('creates a new slot definition', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    (templatesApi.createSlotDefinition as jest.Mock).mockResolvedValue({
      id: 'def-1',
      slot_group_id: 'group-1',
      slot_key: 'main_input',
      min_occurrences: 1,
      max_occurrences: 1,
      sort_order: 0,
      constraints: [],
    });
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Add Slot Definition')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Slot Definition'));
    
    const slotKeyInput = screen.getByLabelText('Slot Key *');
    fireEvent.change(slotKeyInput, { target: { value: 'main_input' } });
    
    const createButton = screen.getByText('Create');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(templatesApi.createSlotDefinition).toHaveBeenCalledWith(
        'group-1',
        expect.objectContaining({ slot_key: 'main_input' })
      );
    });
  });

  test('opens constraint form for slot group', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Add Constraint')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Constraint'));
    expect(screen.getByText('Create Constraint')).toBeInTheDocument();
  });

  test('creates a wildcard constraint', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    (templatesApi.createGroupConstraint as jest.Mock).mockResolvedValue({
      id: 'constraint-1',
      slot_group_id: 'group-1',
      slot_definition_id: null,
      domain: null,
      key: null,
      operator: null,
      value_string: null,
      value_number: null,
      value_boolean: null,
      is_wildcard: true,
      sort_order: 0,
    });
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Add Constraint')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Constraint'));
    
    const wildcardCheckbox = screen.getByLabelText(/Wildcard/);
    fireEvent.click(wildcardCheckbox);
    
    const createButton = screen.getByText('Create');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(templatesApi.createGroupConstraint).toHaveBeenCalledWith(
        'group-1',
        expect.objectContaining({ is_wildcard: true })
      );
    });
  });

  test('creates a normal constraint', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    (templatesApi.createGroupConstraint as jest.Mock).mockResolvedValue({
      id: 'constraint-1',
      slot_group_id: 'group-1',
      slot_definition_id: null,
      domain: 'identity',
      key: 'category',
      operator: '=',
      value_string: 'raw_item',
      value_number: null,
      value_boolean: null,
      is_wildcard: false,
      sort_order: 0,
    });
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const expandButton = screen.getByText('Expand');
    fireEvent.click(expandButton);
    
    await waitFor(() => {
      expect(screen.getByText('Add Constraint')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Add Constraint'));
    
    const domainInput = screen.getByLabelText('Domain *');
    fireEvent.change(domainInput, { target: { value: 'identity' } });
    
    const keyInput = screen.getByLabelText('Key *');
    fireEvent.change(keyInput, { target: { value: 'category' } });
    
    const valueInput = screen.getByLabelText('Value *');
    fireEvent.change(valueInput, { target: { value: 'raw_item' } });
    
    const createButton = screen.getByText('Create');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(templatesApi.createGroupConstraint).toHaveBeenCalledWith(
        'group-1',
        expect.objectContaining({
          domain: 'identity',
          key: 'category',
          value_string: 'raw_item',
        })
      );
    });
  });

  test('deletes a slot group', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    (templatesApi.deleteSlotGroup as jest.Mock).mockResolvedValue(undefined);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Consumes')).toBeInTheDocument();
    });
    
    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);
    
    // Confirm dialog
    window.confirm = jest.fn(() => true);
    
    await waitFor(() => {
      expect(templatesApi.deleteSlotGroup).toHaveBeenCalledWith('group-1');
    });
  });

  test('shows error message on API failure', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockRejectedValue(new Error('API Error'));
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load slot groups')).toBeInTheDocument();
    });
  });

  test('navigates back to template editor', async () => {
    (templatesApi.listSlotGroups as jest.Mock).mockResolvedValue(mockSlotGroups);
    renderWithRouter();
    
    await waitFor(() => {
      expect(screen.getByText('Back to Template Editor')).toBeInTheDocument();
    });
    
    const backButton = screen.getByText('Back to Template Editor');
    expect(backButton).toHaveAttribute('href', '/templates/undefined/edit');
  });
});
