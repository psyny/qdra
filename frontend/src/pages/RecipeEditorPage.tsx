import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import { getProjectTemplate, getProject } from '../api/projects';
import { getEntity, createEntity, getEntityParameters, addEntityParameter, updateEntity } from '../api/entities';
import { listSlotGroups } from '../api/templates';
import {
  createRecipeSlot,
  createRecipeOption,
  createRecipeConstraint,
  getRecipeSlots,
  getRecipeOptions,
  getRecipeConstraints,
  deleteRecipeSlot,
  deleteRecipeOption,
  deleteRecipeConstraint,
} from '../api/entities';
import { ProjectTemplateDetail, ViewConfig, ParameterDefinition } from '../types/template';
import { Entity, EntityParameter } from '../types/entity';
import { RecipeForm } from '../components/RecipeForm';
import { DraftParameter } from '../components/ParameterRow';

type SlotGroupConfig = {
  type: 'requires' | 'consumes' | 'produces';
  min_slots: number;
  max_slots: number;
};

type RecipeEditorPageProps = {
  projectId: string;
};

export function RecipeEditorPage({ projectId }: RecipeEditorPageProps) {
  const { recipeId } = useParams<{ recipeId: string }>();
  const [searchParams] = useSearchParams();
  const configId = searchParams.get('configId');
  const navigate = useNavigate();
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<ViewConfig | null>(null);
  const [recipeCatalogView, setRecipeCatalogView] = useState<any>(null);
  const [parameterDefinitions, setParameterDefinitions] = useState<ParameterDefinition[]>([]);
  const [slotGroups, setSlotGroups] = useState<SlotGroupConfig[]>([]);
  const [materialEntityTypes, setMaterialEntityTypes] = useState<any[]>([]);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [entityParameters, setEntityParameters] = useState<EntityParameter[]>([]);
  const [imageSizePx, setImageSizePx] = useState(256);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialSlotCounts, setInitialSlotCounts] = useState<Record<string, number>>({});
  const [initialSlotConstraints, setInitialSlotConstraints] = useState<any>({});

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);

        // Get recipe catalog view for dynamic labels
        const recipeCatalogView = templateData.views.find(v => v.view_key === 'recipe_catalog');
        setRecipeCatalogView(recipeCatalogView || null);

        // Load project to get image_size_px
        const projectData = await getProject(projectId);
        setImageSizePx(projectData.image_size_px || 256);

        // Extract material entity types (all entity types except the recipe type)
        const materialTypes = templateData.entity_types.filter((et: any) => {
          // Filter out recipe types (those used in recipe_catalog view)
          const recipeView = templateData.views.find((v: any) => v.view_key === 'recipe_catalog');
          if (recipeView) {
            const recipeConfigIds = recipeView.configs.map((c: any) => c.entity_type_id);
            return !recipeConfigIds.includes(et.id);
          }
          return true;
        });
        setMaterialEntityTypes(materialTypes);

        // Find the config in template
        const recipeView = templateData.views.find(v => v.view_key === 'recipe_catalog');
        if (recipeView) {
          let config = null;
          if (configId) {
            config = recipeView.configs.find(c => c.id === configId);
          } else if (recipeView.configs.length > 0) {
            // Use first config if none specified
            config = recipeView.configs[0];
          }

          if (config && config.entity_type_id) {
            setSelectedConfig(config);
            // Get parameter definitions for this entity type
            const entityType = templateData.entity_types.find(et => et.id === config.entity_type_id);
            if (entityType) {
              setParameterDefinitions(entityType.parameter_definitions);

              // Load slot groups for this entity type
              try {
                const slotGroupsData = await listSlotGroups(config.entity_type_id);
                const formattedSlotGroups: SlotGroupConfig[] = slotGroupsData.map((sg: any) => ({
                  type: sg.type,
                  min_slots: sg.min_slots,
                  max_slots: sg.max_slots,
                }));
                setSlotGroups(formattedSlotGroups);
              } catch (err) {
                // If slot groups fail to load, just use empty array
                setSlotGroups([]);
              }
            }
          }
        }

        if (recipeId) {
          const entityData = await getEntity(projectId, recipeId);
          setEntity(entityData);
          const params = await getEntityParameters(projectId, recipeId);
          setEntityParameters(params);

          // Load existing slot definitions
          try {
            const slots = await getRecipeSlots(projectId, recipeId);
            const slotCounts: Record<string, number> = { requires: 0, consumes: 0, produces: 0 };
            const slotConstraints: any = { requires: [], consumes: [], produces: [] };

            for (const slot of slots) {
              slotCounts[slot.kind] = (slotCounts[slot.kind] || 0) + 1;
              const options = await getRecipeOptions(projectId, recipeId, slot.id);
              const slotIndex = slotCounts[slot.kind] - 1;
              slotConstraints[slot.kind][slotIndex] = [];

              for (const option of options) {
                const constraints = await getRecipeConstraints(projectId, recipeId, slot.id, option.id);
                // Transform constraints to include origin field
                const transformedConstraints = constraints.map((c: any) => {
                  if (c.domain === '__system__') {
                    // For system origin
                    return {
                      ...c,
                      origin: 'system',
                      system_key: c.key, // key contains system_key for system
                      entity_type_id: null,
                      domain: null,
                      key: null,
                    };
                  } else {
                    // For parameter origin, try to look up entity_type_id from domain/key
                    let entityTypeId = null;
                    if (c.domain === 'entity_type' && template) {
                      // The key is the entity_type_id when domain is entity_type
                      const entityType = template?.entity_types?.find((et: any) => et.id === c.key);
                      if (entityType) {
                        entityTypeId = entityType.id;
                      }
                    }
                    return {
                      ...c,
                      origin: 'parameter',
                      system_key: null,
                      entity_type_id: entityTypeId,
                    };
                  }
                });
                // Create option spec with quantity and constraints
                slotConstraints[slot.kind][slotIndex].push({
                  constraints: transformedConstraints,
                  quantity: option.quantity || 1,
                });
              }
            }

            setInitialSlotCounts(slotCounts);
            setInitialSlotConstraints(slotConstraints);
          } catch (err) {
            console.error('Failed to load slot definitions:', err);
            setInitialSlotCounts({ requires: 0, consumes: 0, produces: 0 });
            setInitialSlotConstraints({ requires: [], consumes: [], produces: [] });
          }
        }
      } catch (err) {
        setError('Could not load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId, recipeId, configId]);

  const draftToApiParam = (p: DraftParameter) => {
    if (p.value_type === 'string') return { domain: p.domain, key: p.key, value_string: String(p.value ?? '') };
    if (p.value_type === 'number') return { domain: p.domain, key: p.key, value_number: Number(p.value ?? 0) };
    if (p.value_type === 'boolean') return { domain: p.domain, key: p.key, value_boolean: Boolean(p.value) };
    return { domain: p.domain, key: p.key, value_string: null };
  };

  const handleSubmit = async (parameters: DraftParameter[], imageUrl?: string, slotData?: { slotCounts: Record<string, number>; slotConstraints: any }) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (!recipeId) {
        // Create new entity
        if (!selectedConfig?.entity_type_id) {
          throw new Error('No entity type selected');
        }
        // Get entity type name for the group field
        const entityType = template?.entity_types.find(et => et.id === selectedConfig.entity_type_id);
        const groupName = entityType?.name || '';
        const newEntity = await createEntity(projectId, { 
          entity_type_id: selectedConfig.entity_type_id,
          group: groupName
        });
        
        // Add parameters
        for (const p of parameters) {
          await addEntityParameter(projectId, newEntity.id, draftToApiParam(p));
        }

        // Save slot definitions
        if (slotData) {
          await saveSlotDefinitions(projectId, newEntity.id, slotData);
        }

        // If image was uploaded, it's already handled by ImageUpload component
        // The entity will have the image attached via the backend
      } else {
        // Update existing entity
        await updateEntity(projectId, recipeId, { parameters: parameters.map(draftToApiParam) });
        
        // Update slot definitions - delete all and recreate
        if (slotData) {
          await updateSlotDefinitions(projectId, recipeId, slotData);
        }
        
        // Image upload is handled separately by ImageUpload component
      }
      navigate(`/projects/${projectId}/recipes${configId ? `?configId=${configId}` : ''}`);
    } catch (err) {
      setError('Could not save recipe');
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate(`/projects/${projectId}/recipes${configId ? `?configId=${configId}` : ''}`);
  };

  const saveSlotDefinitions = async (projectId: string, recipeId: string, slotData: { slotCounts: Record<string, number>; slotConstraints: any }) => {
    const { slotCounts, slotConstraints } = slotData;
    const kinds = ['requires', 'consumes', 'produces'] as const;

    for (const kind of kinds) {
      const count = slotCounts[kind] || 0;
      for (let i = 0; i < count; i++) {
        const slot = await createRecipeSlot(projectId, recipeId, kind, i);
        const options = slotConstraints[kind]?.[i] || [];

        for (const option of options) {
          const optionQuantity = option.quantity || 1;
          const recipeOption = await createRecipeOption(projectId, recipeId, slot.id, optionQuantity, 0);
          for (const constraint of option.constraints) {
            // For system origin, use special domain/key format
            let domain = constraint.domain;
            let key = constraint.key;
            if (constraint.origin === 'system') {
              domain = '__system__';
              key = constraint.system_key; // Store system_key in key for system
            }

            await createRecipeConstraint(projectId, recipeId, slot.id, recipeOption.id, {
              domain: domain,
              key: key,
              operator: constraint.operator,
              value_string: constraint.value_string,
              value_number: constraint.value_number,
              value_boolean: constraint.value_boolean,
              is_wildcard: false,
            });
          }
        }
      }
    }
  };

  const updateSlotDefinitions = async (projectId: string, recipeId: string, slotData: { slotCounts: Record<string, number>; slotConstraints: any }) => {
    // Delete all existing slots
    const existingSlots = await getRecipeSlots(projectId, recipeId);
    for (const slot of existingSlots) {
      const options = await getRecipeOptions(projectId, recipeId, slot.id);
      for (const option of options) {
        const constraints = await getRecipeConstraints(projectId, recipeId, slot.id, option.id);
        for (const constraint of constraints) {
          await deleteRecipeConstraint(projectId, recipeId, slot.id, option.id, constraint.id);
        }
        await deleteRecipeOption(projectId, recipeId, slot.id, option.id);
      }
      await deleteRecipeSlot(projectId, recipeId, slot.id);
    }

    // Create new slots
    await saveSlotDefinitions(projectId, recipeId, slotData);
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading recipe...</p>
      </div>
    );
  }

  if (error && !entity && !selectedConfig) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <Link to={`/projects/${projectId}/recipes`} className="button button--secondary">
          Back to Recipes
        </Link>
      </div>
    );
  }

  // Convert parameter definitions to draft parameters for the form
  const initialParameters: DraftParameter[] = parameterDefinitions.map((def: ParameterDefinition) => {
    // Find existing value if editing
    const existingParam = entityParameters.find((p: EntityParameter) => p.domain === def.domain && p.key === def.key);
    
    let value: any = null;
    if (existingParam) {
      if (existingParam.value_string !== null && existingParam.value_string !== undefined) {
        value = existingParam.value_string;
      } else if (existingParam.value_number !== null && existingParam.value_number !== undefined) {
        value = existingParam.value_number;
      } else if (existingParam.value_boolean !== null && existingParam.value_boolean !== undefined) {
        value = existingParam.value_boolean;
      }
    } else if (def.default_value !== null && def.default_value !== undefined) {
      // Convert default_value to proper type
      if (def.value_type === 'boolean') {
        const strValue = String(def.default_value).toLowerCase();
        value = strValue === 'true';
      } else if (def.value_type === 'number') {
        value = Number(def.default_value);
      } else {
        value = def.default_value;
      }
    }

    return {
      domain: def.domain,
      key: def.key,
      value_type: def.value_type,
      label: def.label,
      description: def.description,
      required: def.required,
      sort_order: def.sort_order,
      value: value,
      is_searchable: def.is_searchable,
      is_unique: def.is_unique,
    };
  });

  return (
    <div>
      <h2 className="card-title mb-4">
        {recipeId ? 'Edit Entity' : 'New Entity'}
      </h2>
      <RecipeForm
        initialParameters={initialParameters}
        isSubmitting={isSubmitting}
        errorMessage={error}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel={recipeId ? 'Save Entity' : 'Create Entity'}
        entityId={recipeId || undefined}
        targetImageSize={imageSizePx}
        currentImage={entity?.image?.url || null}
        slotGroups={slotGroups}
        materialEntityTypes={materialEntityTypes}
        template={template}
        projectId={projectId}
        initialSlotCounts={initialSlotCounts}
        initialSlotConstraints={initialSlotConstraints}
        group={entity?.group || selectedConfig ? template?.entity_types.find(et => et.id === selectedConfig.entity_type_id)?.name : undefined}
      />
    </div>
  );
}
