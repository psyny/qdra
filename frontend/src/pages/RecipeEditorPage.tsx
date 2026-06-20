import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import { getProjectTemplate, getProject } from '../api/projects';
import { getEntity, createEntity, getEntityParameters, addEntityParameter, updateEntity } from '../api/entities';
import { listSlotGroups } from '../api/templates';
import { ProjectTemplateDetail, ViewConfig, ParameterDefinition } from '../types/template';
import { Entity, EntityParameter } from '../types/entity';
import { RecipeForm } from '../components/RecipeForm';
import { DraftParameter } from '../components/ParameterRow';

type SlotGroupConfig = {
  kind: 'requires' | 'consumes' | 'produces';
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
  const [parameterDefinitions, setParameterDefinitions] = useState<ParameterDefinition[]>([]);
  const [slotGroups, setSlotGroups] = useState<SlotGroupConfig[]>([]);
  const [materialEntityTypes, setMaterialEntityTypes] = useState<any[]>([]);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [entityParameters, setEntityParameters] = useState<EntityParameter[]>([]);
  const [imageSizePx, setImageSizePx] = useState(256);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);

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

        if (configId) {
          // Find the config in template
          const recipeView = templateData.views.find(v => v.view_key === 'recipe_catalog');
          if (recipeView) {
            const config = recipeView.configs.find(c => c.id === configId);
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
                    kind: sg.kind,
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
        }

        if (recipeId) {
          const entityData = await getEntity(projectId, recipeId);
          setEntity(entityData);
          const params = await getEntityParameters(projectId, recipeId);
          setEntityParameters(params);
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

  const handleSubmit = async (parameters: DraftParameter[], imageUrl?: string) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (!recipeId) {
        // Create new entity
        if (!selectedConfig?.entity_type_id) {
          throw new Error('No entity type selected');
        }
        const newEntity = await createEntity(projectId, { entity_type_id: selectedConfig.entity_type_id });
        
        // Add parameters
        for (const p of parameters) {
          await addEntityParameter(projectId, newEntity.id, draftToApiParam(p));
        }

        // If image was uploaded, it's already handled by ImageUpload component
        // The entity will have the image attached via the backend
      } else {
        // Update existing entity
        await updateEntity(projectId, recipeId, { parameters: parameters.map(draftToApiParam) });
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
    };
  });

  return (
    <div>
      <h2 className="card-title mb-4">
        {recipeId ? 'Edit Recipe' : 'New Recipe'}
      </h2>
      <RecipeForm
        initialParameters={initialParameters}
        isSubmitting={isSubmitting}
        errorMessage={error}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel={recipeId ? 'Save Recipe' : 'Create Recipe'}
        entityId={recipeId || undefined}
        targetImageSize={imageSizePx}
        currentImage={entity?.image?.url || null}
        slotGroups={slotGroups}
        materialEntityTypes={materialEntityTypes}
        template={template}
      />
    </div>
  );
}
