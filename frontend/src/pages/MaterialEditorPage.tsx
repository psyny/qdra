import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import { getProjectTemplate } from '../api/projects';
import { getEntity, createEntity, getEntityParameters, addEntityParameter, updateEntity } from '../api/entities';
import { ProjectTemplateDetail, ViewConfig, ParameterDefinition } from '../types/template';
import { Entity, EntityParameter } from '../types/entity';
import { MaterialForm } from '../components/MaterialForm';
import { DraftParameter } from '../components/ParameterRow';

type MaterialEditorPageProps = {
  projectId: string;
};

export function MaterialEditorPage({ projectId }: MaterialEditorPageProps) {
  const { materialId } = useParams<{ materialId: string }>();
  const [searchParams] = useSearchParams();
  const configId = searchParams.get('configId');
  const navigate = useNavigate();
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<ViewConfig | null>(null);
  const [parameterDefinitions, setParameterDefinitions] = useState<ParameterDefinition[]>([]);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [entityParameters, setEntityParameters] = useState<EntityParameter[]>([]);
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

        if (configId) {
          // Find the config in template
          const materialView = templateData.views.find(v => v.view_key === 'material_catalog');
          if (materialView) {
            const config = materialView.configs.find(c => c.id === configId);
            if (config && config.entity_type_id) {
              setSelectedConfig(config);
              // Get parameter definitions for this entity type
              const entityType = templateData.entity_types.find(et => et.id === config.entity_type_id);
              if (entityType) {
                setParameterDefinitions(entityType.parameter_definitions);
              }
            }
          }
        }

        if (materialId) {
          const entityData = await getEntity(projectId, materialId);
          setEntity(entityData);
          const params = await getEntityParameters(projectId, materialId);
          setEntityParameters(params);
        }
      } catch (err) {
        setError('Could not load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId, materialId, configId]);

  const draftToApiParam = (p: DraftParameter) => {
    if (p.value_type === 'string') return { domain: p.domain, key: p.key, value_string: String(p.value ?? '') };
    if (p.value_type === 'number') return { domain: p.domain, key: p.key, value_number: Number(p.value ?? 0) };
    if (p.value_type === 'boolean') return { domain: p.domain, key: p.key, value_boolean: Boolean(p.value) };
    return { domain: p.domain, key: p.key, value_string: null };
  };

  const handleSubmit = async (parameters: DraftParameter[]) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (!materialId) {
        // Create new entity
        if (!selectedConfig?.entity_type_id) {
          throw new Error('No entity type selected');
        }
        const newEntity = await createEntity(projectId, { entity_type_id: selectedConfig.entity_type_id });
        
        // Add parameters
        for (const p of parameters) {
          await addEntityParameter(projectId, newEntity.id, draftToApiParam(p));
        }
      } else {
        // Update existing entity
        await updateEntity(projectId, materialId, { parameters: parameters.map(draftToApiParam) });
      }
      navigate(`/projects/${projectId}/materials${configId ? `?configId=${configId}` : ''}`);
    } catch (err) {
      setError('Could not save material');
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate(`/projects/${projectId}/materials${configId ? `?configId=${configId}` : ''}`);
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading material...</p>
      </div>
    );
  }

  if (error && !entity && !selectedConfig) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <Link to={`/projects/${projectId}/materials`} className="button button--secondary">
          Back to Materials
        </Link>
      </div>
    );
  }

  // Convert parameter definitions to draft parameters for the form
  const initialParameters: DraftParameter[] = parameterDefinitions.map((def: ParameterDefinition) => {
    // Find existing value if editing
    const existingParam = entityParameters.find((p: EntityParameter) => p.domain === def.domain && p.key === def.key);
    
    let value: any = def.default_value;
    if (existingParam) {
      if (existingParam.value_string !== null && existingParam.value_string !== undefined) {
        value = existingParam.value_string;
      } else if (existingParam.value_number !== null && existingParam.value_number !== undefined) {
        value = existingParam.value_number;
      } else if (existingParam.value_boolean !== null && existingParam.value_boolean !== undefined) {
        value = existingParam.value_boolean;
      }
    }

    return {
      domain: def.domain,
      key: def.key,
      value_type: def.value_type,
      label: def.label,
      description: def.description,
      required: def.required,
      value: value,
    };
  });

  return (
    <div>
      <h2 className="card-title mb-4">
        {materialId ? 'Edit Material' : 'New Material'}
      </h2>
      <MaterialForm
        initialParameters={initialParameters}
        isSubmitting={isSubmitting}
        errorMessage={error}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel={materialId ? 'Save Material' : 'Create Material'}
      />
    </div>
  );
}
