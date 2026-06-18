import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  listSlotGroups,
  createSlotGroup,
  updateSlotGroup,
  deleteSlotGroup,
  createSlotDefinition,
  updateSlotDefinition,
  deleteSlotDefinition,
  createGroupConstraint,
  createDefinitionConstraint,
  updateSlotConstraint,
  deleteSlotConstraint,
  getTemplate,
  getEntityType,
} from '../api/templates';

type SlotGroup = {
  id: string;
  entity_type_id: string;
  kind: string;
  min_slots: number;
  max_slots: number | null;
  sort_order: number;
  constraints: SlotConstraint[];
  slot_definitions: SlotDefinition[];
};

type SlotDefinition = {
  id: string;
  slot_group_id: string;
  slot_key: string;
  min_occurrences: number;
  max_occurrences: number | null;
  sort_order: number;
  constraints: SlotConstraint[];
};

type SlotConstraint = {
  id: string;
  slot_group_id: string | null;
  slot_definition_id: string | null;
  domain: string | null;
  key: string | null;
  operator: string | null;
  value_string: string | null;
  value_number: number | null;
  value_boolean: boolean | null;
  is_wildcard: boolean;
  sort_order: number;
};

export function SlotDefinitionsPage() {
  const { templateId, entityTypeId } = useParams<{ templateId: string; entityTypeId: string }>();
  const navigate = useNavigate();
  
  const [slotGroups, setSlotGroups] = useState<SlotGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entityName, setEntityName] = useState<string>('');
  
  const [showCreateGroupForm, setShowCreateGroupForm] = useState(false);
  const [editingGroup, setEditingGroup] = useState<SlotGroup | null>(null);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  
  const [groupForm, setGroupForm] = useState({
    kind: 'consumes',
    min_slots: 0,
    max_slots: '',
    sort_order: 0,
  });
  
  const [showDefinitionForm, setShowDefinitionForm] = useState(false);
  const [editingDefinition, setEditingDefinition] = useState<SlotDefinition | null>(null);
  const [definitionForm, setDefinitionForm] = useState({
    slot_key: '',
    min_occurrences: 0,
    max_occurrences: '',
    sort_order: 0,
  });
  
  const [showConstraintForm, setShowConstraintForm] = useState(false);
  const [constraintParent, setConstraintParent] = useState<{ type: 'group' | 'definition'; id: string } | null>(null);
  const [editingConstraint, setEditingConstraint] = useState<SlotConstraint | null>(null);
  const [constraintForm, setConstraintForm] = useState({
    is_wildcard: false,
    domain: '',
    key: '',
    operator: '=',
    value_type: 'string',
    value_string: '',
    value_number: '',
    value_boolean: false,
    sort_order: 0,
  });

  useEffect(() => {
    if (entityTypeId) {
      loadSlotGroups();
    }
    if (templateId && entityTypeId) {
      loadEntityName();
    }
  }, [entityTypeId, templateId]);

  const loadSlotGroups = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSlotGroups(entityTypeId!);
      setSlotGroups(data);
    } catch (err) {
      setError('Failed to load slot groups');
    } finally {
      setLoading(false);
    }
  };

  const loadEntityName = async () => {
    try {
      const data = await getEntityType(templateId!, entityTypeId!);
      setEntityName(data.name);
    } catch (err) {
      // Don't set error for entity name loading failure
    }
  };

  const handleCreateGroup = async () => {
    if (!groupForm.kind) {
      setError('Kind is required');
      return;
    }
    try {
      await createSlotGroup(entityTypeId!, {
        kind: groupForm.kind,
        min_slots: groupForm.min_slots,
        max_slots: groupForm.max_slots ? parseInt(groupForm.max_slots) : null,
        sort_order: groupForm.sort_order,
      });
      setShowCreateGroupForm(false);
      setGroupForm({ kind: 'consumes', min_slots: 0, max_slots: '', sort_order: 0 });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to create slot group');
    }
  };

  const handleUpdateGroup = async () => {
    if (!editingGroup) return;
    try {
      await updateSlotGroup(editingGroup.id, {
        kind: groupForm.kind,
        min_slots: groupForm.min_slots,
        max_slots: groupForm.max_slots ? parseInt(groupForm.max_slots) : null,
        sort_order: groupForm.sort_order,
      });
      setEditingGroup(null);
      setGroupForm({ kind: 'consumes', min_slots: 0, max_slots: '', sort_order: 0 });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to update slot group');
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (!confirm('Are you sure you want to delete this slot group? This will also delete all its slot definitions and constraints.')) return;
    try {
      await deleteSlotGroup(groupId);
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to delete slot group');
    }
  };

  const handleCreateDefinition = async (groupId: string) => {
    if (!definitionForm.slot_key.trim()) {
      setError('Slot key is required');
      return;
    }
    try {
      await createSlotDefinition(groupId, {
        slot_key: definitionForm.slot_key,
        min_occurrences: definitionForm.min_occurrences,
        max_occurrences: definitionForm.max_occurrences ? parseInt(definitionForm.max_occurrences) : null,
        sort_order: definitionForm.sort_order,
      });
      setShowDefinitionForm(false);
      setDefinitionForm({ slot_key: '', min_occurrences: 0, max_occurrences: '', sort_order: 0 });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to create slot definition');
    }
  };

  const handleUpdateDefinition = async () => {
    if (!editingDefinition) return;
    try {
      await updateSlotDefinition(editingDefinition.id, {
        slot_key: definitionForm.slot_key,
        min_occurrences: definitionForm.min_occurrences,
        max_occurrences: definitionForm.max_occurrences ? parseInt(definitionForm.max_occurrences) : null,
        sort_order: definitionForm.sort_order,
      });
      setEditingDefinition(null);
      setDefinitionForm({ slot_key: '', min_occurrences: 0, max_occurrences: '', sort_order: 0 });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to update slot definition');
    }
  };

  const handleDeleteDefinition = async (definitionId: string) => {
    if (!confirm('Are you sure you want to delete this slot definition?')) return;
    try {
      await deleteSlotDefinition(definitionId);
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to delete slot definition');
    }
  };

  const handleCreateConstraint = async () => {
    if (!constraintParent) return;
    
    if (!constraintForm.is_wildcard && (!constraintForm.domain || !constraintForm.key || !constraintForm.operator)) {
      setError('Non-wildcard constraints require domain, key, and operator');
      return;
    }
    
    try {
      const payload: any = {
        is_wildcard: constraintForm.is_wildcard,
        sort_order: constraintForm.sort_order,
      };
      
      if (!constraintForm.is_wildcard) {
        payload.domain = constraintForm.domain;
        payload.key = constraintForm.key;
        payload.operator = constraintForm.operator;
        
        if (constraintForm.value_type === 'string') {
          payload.value_string = constraintForm.value_string;
        } else if (constraintForm.value_type === 'number') {
          payload.value_number = constraintForm.value_number ? parseFloat(constraintForm.value_number) : null;
        } else if (constraintForm.value_type === 'boolean') {
          payload.value_boolean = constraintForm.value_boolean;
        }
      }
      
      if (constraintParent.type === 'group') {
        await createGroupConstraint(constraintParent.id, payload);
      } else {
        await createDefinitionConstraint(constraintParent.id, payload);
      }
      
      setShowConstraintForm(false);
      setConstraintParent(null);
      setConstraintForm({
        is_wildcard: false,
        domain: '',
        key: '',
        operator: '=',
        value_type: 'string',
        value_string: '',
        value_number: '',
        value_boolean: false,
        sort_order: 0,
      });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to create constraint');
    }
  };

  const handleUpdateConstraint = async () => {
    if (!editingConstraint) return;
    
    try {
      const payload: any = {
        is_wildcard: constraintForm.is_wildcard,
        sort_order: constraintForm.sort_order,
      };
      
      if (!constraintForm.is_wildcard) {
        payload.domain = constraintForm.domain;
        payload.key = constraintForm.key;
        payload.operator = constraintForm.operator;
        
        if (constraintForm.value_type === 'string') {
          payload.value_string = constraintForm.value_string;
        } else if (constraintForm.value_type === 'number') {
          payload.value_number = constraintForm.value_number ? parseFloat(constraintForm.value_number) : null;
        } else if (constraintForm.value_type === 'boolean') {
          payload.value_boolean = constraintForm.value_boolean;
        }
      }
      
      await updateSlotConstraint(editingConstraint.id, payload);
      setEditingConstraint(null);
      setConstraintForm({
        is_wildcard: false,
        domain: '',
        key: '',
        operator: '=',
        value_type: 'string',
        value_string: '',
        value_number: '',
        value_boolean: false,
        sort_order: 0,
      });
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to update constraint');
    }
  };

  const handleDeleteConstraint = async (constraintId: string) => {
    if (!confirm('Are you sure you want to delete this constraint?')) return;
    try {
      await deleteSlotConstraint(constraintId);
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to delete constraint');
    }
  };

  const startEditGroup = (group: SlotGroup) => {
    setEditingGroup(group);
    setGroupForm({
      kind: group.kind,
      min_slots: group.min_slots,
      max_slots: group.max_slots?.toString() || '',
      sort_order: group.sort_order,
    });
  };

  const startEditDefinition = (def: SlotDefinition) => {
    setEditingDefinition(def);
    setDefinitionForm({
      slot_key: def.slot_key,
      min_occurrences: def.min_occurrences,
      max_occurrences: def.max_occurrences?.toString() || '',
      sort_order: def.sort_order,
    });
  };

  const startEditConstraint = (constraint: SlotConstraint) => {
    setEditingConstraint(constraint);
    setConstraintForm({
      is_wildcard: constraint.is_wildcard,
      domain: constraint.domain || '',
      key: constraint.key || '',
      operator: constraint.operator || '=',
      value_type: constraint.value_string ? 'string' : constraint.value_number !== null ? 'number' : constraint.value_boolean !== null ? 'boolean' : 'string',
      value_string: constraint.value_string || '',
      value_number: constraint.value_number?.toString() || '',
      value_boolean: constraint.value_boolean || false,
      sort_order: constraint.sort_order,
    });
  };

  const startCreateConstraint = (type: 'group' | 'definition', id: string) => {
    setConstraintParent({ type, id });
    setShowConstraintForm(true);
    setConstraintForm({
      is_wildcard: false,
      domain: '',
      key: '',
      operator: '=',
      value_type: 'string',
      value_string: '',
      value_number: '',
      value_boolean: false,
      sort_order: 0,
    });
  };

  const getGroupKindLabel = (kind: string) => {
    const labels: Record<string, string> = {
      consumes: 'Consumes',
      requires: 'Requires',
      produces: 'Produces',
    };
    return labels[kind] || kind;
  };

  const getConstraintDisplay = (constraint: SlotConstraint) => {
    if (constraint.is_wildcard) return '*';
    const value = constraint.value_string || constraint.value_number || constraint.value_boolean;
    return `${constraint.domain}:${constraint.key} ${constraint.operator} ${value}`;
  };

  if (loading) {
    return <p>Loading slot definitions...</p>;
  }

  return (
    <div className="page">
      <div className="workspace-header">
        <div className="workspace-header__breadcrumb">
          <Link to="/home">Home</Link> &gt; <Link to="/templates">Templates</Link> &gt; <Link to={`/templates/${templateId}/edit`}>Edit Template</Link> &gt; <span>Edit Slot Definitions</span>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title">Edit Slot Definitions{entityName && ` for ${entityName}`}</h2>
          </div>
          <button
            onClick={() => setShowCreateGroupForm(true)}
            className="button button--primary"
          >
            Add Slot Group
          </button>
        </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', marginBottom: '16px' }}>
          <p style={{ color: '#EF4444', margin: 0 }}>{error}</p>
          <button onClick={() => setError(null)} style={{ marginTop: '8px', background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', textDecoration: 'underline' }}>Dismiss</button>
        </div>
      )}

      {showCreateGroupForm && (
        <div style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '18px', marginBottom: '16px' }}>
          <h3 style={{ marginTop: 0 }}>Create Slot Group</h3>
          <div className="form-field">
            <label className="form-label">Kind *</label>
            <select
              className="form-input"
              value={groupForm.kind}
              onChange={(e) => setGroupForm({ ...groupForm, kind: e.target.value })}
            >
              <option value="consumes">Consumes</option>
              <option value="requires">Requires</option>
              <option value="produces">Produces</option>
            </select>
          </div>
          <div className="form-field">
            <label className="form-label">Min Slots</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.min_slots}
              onChange={(e) => setGroupForm({ ...groupForm, min_slots: parseInt(e.target.value) || 0 })}
              min="0"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Max Slots (leave blank for unlimited)</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.max_slots}
              onChange={(e) => setGroupForm({ ...groupForm, max_slots: e.target.value })}
              min="0"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Sort Order</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.sort_order}
              onChange={(e) => setGroupForm({ ...groupForm, sort_order: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div className="form-actions">
            <button onClick={() => { setShowCreateGroupForm(false); setGroupForm({ kind: 'consumes', min_slots: 0, max_slots: '', sort_order: 0 }); }} className="button button--secondary">Cancel</button>
            <button onClick={handleCreateGroup} className="button button--primary">Create</button>
          </div>
        </div>
      )}

      {['consumes', 'requires', 'produces'].map((kind) => {
        const group = slotGroups.find(g => g.kind === kind);
        if (!group) {
          return (
            <div key={kind} style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '18px', marginBottom: '12px', border: '1px dashed rgba(255,255,255,0.15)' }}>
              <p style={{ margin: 0, color: '#666' }}>No {getGroupKindLabel(kind)} group defined</p>
              <button
                onClick={() => { setShowCreateGroupForm(true); setGroupForm({ ...groupForm, kind }); }}
                className="button button--secondary"
                style={{ marginTop: '8px', fontSize: '12px' }}
              >
                Add {getGroupKindLabel(kind)} Group
              </button>
            </div>
          );
        }

        return (
          <div key={group.id} style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '18px', marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0' }}>{getGroupKindLabel(group.kind)}</h3>
                <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                  Min: {group.min_slots} | Max: {group.max_slots || 'unlimited'} | 
                  Constraints: {group.constraints.length} | Definitions: {group.slot_definitions.length}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => setExpandedGroup(expandedGroup === group.id ? null : group.id)} className="button button--secondary" style={{ fontSize: '12px' }}>
                  {expandedGroup === group.id ? 'Collapse' : 'Expand'}
                </button>
                <button onClick={() => startEditGroup(group)} className="button button--secondary" style={{ fontSize: '12px' }}>
                  Edit
                </button>
                <button onClick={() => handleDeleteGroup(group.id)} className="button button--secondary" style={{ fontSize: '12px', color: '#c33' }}>
                  Delete
                </button>
              </div>
            </div>

            {editingGroup?.id === group.id && (
              <div style={{ marginTop: '16px', padding: '12px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                <h4 style={{ marginTop: 0 }}>Edit Slot Group</h4>
                <div className="form-field">
                  <label className="form-label">Kind *</label>
                  <select
                    className="form-input"
                    value={groupForm.kind}
                    onChange={(e) => setGroupForm({ ...groupForm, kind: e.target.value })}
                  >
                    <option value="consumes">Consumes</option>
                    <option value="requires">Requires</option>
                    <option value="produces">Produces</option>
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-label">Min Slots</label>
                  <input
                    type="number"
                    className="form-input"
                    value={groupForm.min_slots}
                    onChange={(e) => setGroupForm({ ...groupForm, min_slots: parseInt(e.target.value) || 0 })}
                    min="0"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Max Slots (leave blank for unlimited)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={groupForm.max_slots}
                    onChange={(e) => setGroupForm({ ...groupForm, max_slots: e.target.value })}
                    min="0"
                  />
                </div>
                <div className="form-actions">
                  <button onClick={() => { setEditingGroup(null); setGroupForm({ kind: 'consumes', min_slots: 0, max_slots: '', sort_order: 0 }); }} className="button button--secondary">Cancel</button>
                  <button onClick={handleUpdateGroup} className="button button--primary">Save</button>
                </div>
              </div>
            )}

            {expandedGroup === group.id && (
              <div style={{ marginTop: '16px', borderTop: '1px solid #ddd', paddingTop: '12px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0 }}>Default Constraints</h4>
                    <button onClick={() => startCreateConstraint('group', group.id)} className="button button--primary" style={{ fontSize: '12px' }}>
                      Add Constraint
                    </button>
                  </div>
                  {group.constraints.length === 0 ? (
                    <p style={{ color: '#666', fontSize: '14px' }}>No default constraints</p>
                  ) : (
                    <ul style={{ margin: 0, paddingLeft: '20px' }}>
                      {group.constraints.map((constraint) => (
                        <li key={constraint.id} style={{ marginBottom: '4px' }}>
                          <span>{getConstraintDisplay(constraint)}</span>
                          <button onClick={() => startEditConstraint(constraint)} style={{ marginLeft: '8px', fontSize: '11px' }}>Edit</button>
                          <button onClick={() => handleDeleteConstraint(constraint.id)} style={{ marginLeft: '4px', fontSize: '11px', color: '#c33' }}>Delete</button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0 }}>Slot Definitions</h4>
                    <button onClick={() => { setShowDefinitionForm(true); setEditingDefinition(null); }} className="button button--primary" style={{ fontSize: '12px' }}>
                      Add Slot Definition
                    </button>
                  </div>
                  {group.slot_definitions.length === 0 ? (
                    <p style={{ color: '#666', fontSize: '14px' }}>No slot definitions</p>
                  ) : (
                    group.slot_definitions.map((def) => (
                      <div key={def.id} style={{ padding: '8px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '12px', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <strong>{def.slot_key}</strong>
                            <span style={{ marginLeft: '8px', color: '#666', fontSize: '13px' }}>
                              Min: {def.min_occurrences} | Max: {def.max_occurrences || 'unlimited'}
                            </span>
                          </div>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button onClick={() => startEditDefinition(def)} style={{ fontSize: '11px' }}>Edit</button>
                            <button onClick={() => handleDeleteDefinition(def.id)} style={{ fontSize: '11px', color: '#c33' }}>Delete</button>
                          </div>
                        </div>
                        {def.constraints.length > 0 && (
                          <div style={{ marginTop: '8px', paddingLeft: '12px' }}>
                            <strong style={{ fontSize: '12px' }}>Constraints:</strong>
                            <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px', fontSize: '13px' }}>
                              {def.constraints.map((constraint) => (
                                <li key={constraint.id}>
                                  {getConstraintDisplay(constraint)}
                                  <button onClick={() => startEditConstraint(constraint)} style={{ marginLeft: '8px', fontSize: '11px' }}>Edit</button>
                                  <button onClick={() => handleDeleteConstraint(constraint.id)} style={{ marginLeft: '4px', fontSize: '11px', color: '#c33' }}>Delete</button>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <button onClick={() => startCreateConstraint('definition', def.id)} style={{ marginTop: '8px', fontSize: '11px' }}>
                          Add Constraint
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {showDefinitionForm && (
                  <div style={{ marginTop: '16px', padding: '12px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                    <h5 style={{ marginTop: 0 }}>{editingDefinition ? 'Edit' : 'Create'} Slot Definition</h5>
                    <div className="form-field">
                      <label className="form-label">Slot Key *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={definitionForm.slot_key}
                        onChange={(e) => setDefinitionForm({ ...definitionForm, slot_key: e.target.value })}
                        placeholder="e.g., 1, main_input, catalyst, *"
                      />
                      <small style={{ color: '#666' }}>Use numeric keys like 1, 2, 3 for positional slots, semantic keys like catalyst or main_input for named slots, or * for default unmatched slots.</small>
                    </div>
                    <div className="form-field">
                      <label className="form-label">Min Occurrences</label>
                      <input
                        type="number"
                        className="form-input"
                        value={definitionForm.min_occurrences}
                        onChange={(e) => setDefinitionForm({ ...definitionForm, min_occurrences: parseInt(e.target.value) || 0 })}
                        min="0"
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label">Max Occurrences (leave blank for unlimited)</label>
                      <input
                        type="number"
                        className="form-input"
                        value={definitionForm.max_occurrences}
                        onChange={(e) => setDefinitionForm({ ...definitionForm, max_occurrences: e.target.value })}
                        min="0"
                      />
                    </div>
                    <div className="form-actions">
                      <button onClick={() => { setShowDefinitionForm(false); setEditingDefinition(null); setDefinitionForm({ slot_key: '', min_occurrences: 0, max_occurrences: '', sort_order: 0 }); }} className="button button--secondary">Cancel</button>
                      <button onClick={editingDefinition ? handleUpdateDefinition : () => handleCreateDefinition(group.id)} className="button button--primary">
                        {editingDefinition ? 'Save' : 'Create'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {showConstraintForm && (
        <div style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', backgroundColor: 'rgba(10,10,10,0.95)', border: '1px solid rgba(255,255,255,0.1)', padding: '24px', borderRadius: '18px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)', zIndex: 1000, maxWidth: '500px', maxHeight: '90vh', overflowY: 'auto' }}>
          <h3 style={{ marginTop: 0 }}>{editingConstraint ? 'Edit' : 'Create'} Constraint</h3>
          <div className="form-field">
            <label>
              <input
                type="checkbox"
                checked={constraintForm.is_wildcard}
                onChange={(e) => setConstraintForm({ ...constraintForm, is_wildcard: e.target.checked })}
              />
              <span style={{ marginLeft: '8px' }}>Wildcard (accepts any value)</span>
            </label>
          </div>
          {!constraintForm.is_wildcard && (
            <>
              <div className="form-field">
                <label className="form-label">Domain *</label>
                <input
                  type="text"
                  className="form-input"
                  value={constraintForm.domain}
                  onChange={(e) => setConstraintForm({ ...constraintForm, domain: e.target.value })}
                  placeholder="e.g., identity"
                />
              </div>
              <div className="form-field">
                <label className="form-label">Key *</label>
                <input
                  type="text"
                  className="form-input"
                  value={constraintForm.key}
                  onChange={(e) => setConstraintForm({ ...constraintForm, key: e.target.value })}
                  placeholder="e.g., category"
                />
              </div>
              <div className="form-field">
                <label className="form-label">Operator *</label>
                <select
                  className="form-input"
                  value={constraintForm.operator}
                  onChange={(e) => setConstraintForm({ ...constraintForm, operator: e.target.value })}
                >
                  <option value="=">=</option>
                  <option value="!=">!=</option>
                  <option value="<">&lt;</option>
                  <option value="<=">&lt;=</option>
                  <option value=">">&gt;</option>
                  <option value=">=">&gt;=</option>
                  <option value="contains">contains</option>
                </select>
              </div>
              <div className="form-field">
                <label className="form-label">Value Type *</label>
                <select
                  className="form-input"
                  value={constraintForm.value_type}
                  onChange={(e) => setConstraintForm({ ...constraintForm, value_type: e.target.value })}
                >
                  <option value="string">String</option>
                  <option value="number">Number</option>
                  <option value="boolean">Boolean</option>
                </select>
              </div>
              {constraintForm.value_type === 'string' && (
                <div className="form-field">
                  <label className="form-label">Value *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={constraintForm.value_string}
                    onChange={(e) => setConstraintForm({ ...constraintForm, value_string: e.target.value })}
                  />
                </div>
              )}
              {constraintForm.value_type === 'number' && (
                <div className="form-field">
                  <label className="form-label">Value *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={constraintForm.value_number}
                    onChange={(e) => setConstraintForm({ ...constraintForm, value_number: e.target.value })}
                  />
                </div>
              )}
              {constraintForm.value_type === 'boolean' && (
                <div className="form-field">
                  <label className="form-label">Value *</label>
                  <select
                    className="form-input"
                    value={constraintForm.value_boolean.toString()}
                    onChange={(e) => setConstraintForm({ ...constraintForm, value_boolean: e.target.value === 'true' })}
                  >
                    <option value="false">False</option>
                    <option value="true">True</option>
                  </select>
                </div>
              )}
            </>
          )}
          <div className="form-actions">
            <button onClick={() => { setShowConstraintForm(false); setConstraintParent(null); setEditingConstraint(null); setConstraintForm({ is_wildcard: false, domain: '', key: '', operator: '=', value_type: 'string', value_string: '', value_number: '', value_boolean: false, sort_order: 0 }); }} className="button button--secondary">Cancel</button>
            <button onClick={editingConstraint ? handleUpdateConstraint : handleCreateConstraint} className="button button--primary">
              {editingConstraint ? 'Save' : 'Create'}
            </button>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
