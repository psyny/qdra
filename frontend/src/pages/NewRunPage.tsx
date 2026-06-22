import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  createOutputSolverRun,
  ConstraintSpec,
  TargetSpec,
  DomainConstraints,
  SearchParameters,
  ScoreRules,
} from '../api/planning';
import { getProjectTemplate } from '../api/projects';
import { ConstraintBuilder } from '../components/ConstraintBuilder';

type NewRunPageProps = {
  projectId: string;
};

type SubcardKey = 'planTarget' | 'planOptions' | 'searchParameters' | 'scoreRules';

export function NewRunPage({ projectId }: NewRunPageProps) {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [template, setTemplate] = useState<any>(null);

  useEffect(() => {
    const loadTemplate = async () => {
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);
      } catch (err) {
        console.error('Failed to load template:', err);
      }
    };
    loadTemplate();
  }, [projectId]);
  
  // Subcard expansion state
  const [expandedCards, setExpandedCards] = useState<Record<SubcardKey, boolean>>({
    planTarget: true,
    planOptions: true,
    searchParameters: false,
    scoreRules: false,
  });

  // Target state
  const [target, setTarget] = useState<TargetSpec>({
    quantity: 1,
    target_type: 'material',
    constraints: [],
  });

  // Domain constraints state
  const [domainConstraints, setDomainConstraints] = useState<DomainConstraints>({
    do_not_expand_materials_matching: [],
    forbidden_materials_matching: [],
    forbidden_recipe_matching: [],
    required_materials_matching: [],
    required_recipe_matching: [],
    max_recipe_depth: 10,
    allow_partial_recipe_execution: false,
  });

  // Search parameters state
  const [searchParameters, setSearchParameters] = useState<SearchParameters>({
    max_recursion_depth: 20,
    max_branch_width: 10,
    allow_loops: false,
    max_solutions_returned: 10,
    optimization_level: 0,
  });

  // Score rules state
  const [scoreRules, setScoreRules] = useState<ScoreRules>({
    user_variables: [],
    score_formulas: [],
  });

  const toggleCard = (key: SubcardKey) => {
    setExpandedCards(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Debug: Print payload before API call
    const payload = {
      project_id: projectId,
      target,
      domain_constraints: domainConstraints,
      search_parameters: searchParameters,
      score_rules: scoreRules.user_variables.length > 0 || scoreRules.score_formulas.length > 0 ? scoreRules : undefined,
      name: name || undefined,
    };
    console.log('Create Output Solver Run Payload:', JSON.stringify(payload, null, 2));
    
    // Return early for debugging - don't call API yet
    setLoading(false);
    return;

    try {
      const result = await createOutputSolverRun({
        project_id: projectId,
        target,
        domain_constraints: domainConstraints,
        search_parameters: searchParameters,
        score_rules: scoreRules.user_variables.length > 0 || scoreRules.score_formulas.length > 0 ? scoreRules : undefined,
        name: name || undefined,
      });
      // Navigate to the new run details page
      navigate(`/projects/${projectId}/planning/planning_output_solver/${result.id}`);
    } catch (err) {
      setError('Failed to create run. Please try again.');
      console.error('Failed to create run:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="card-title mb-4" style={{ marginBottom: '24px' }}>New Output Solver Run</h2>

      {error && (
        <div style={{ color: 'red', marginBottom: '16px', padding: '12px', backgroundColor: '#fee', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Name field */}
        <div className="form-field mb-4" style={{ marginBottom: '24px' }}>
          <label htmlFor="run-name" className="form-label">Name (optional)</label>
          <input
            id="run-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="form-input"
            placeholder="Enter a name for this run"
          />
        </div>

        {/* Subcard 1: Plan Target */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Target</h3>
            <button
              type="button"
              onClick={() => toggleCard('planTarget')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.planTarget ? '-' : '+'}
            </button>
          </div>
          {expandedCards.planTarget && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="target-quantity" className="form-label">Quantity</label>
                <input
                  id="target-quantity"
                  type="number"
                  value={target.quantity}
                  onChange={(e) => setTarget({ ...target, quantity: parseFloat(e.target.value) || 0 })}
                  className="form-input"
                  step="any"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="target-type" className="form-label">Target Type</label>
                <select
                  id="target-type"
                  value={target.target_type}
                  onChange={(e) => setTarget({ ...target, target_type: e.target.value, constraints: [] })}
                  className="form-input"
                >
                  <option value="material">Material</option>
                  <option value="recipe">Recipe</option>
                </select>
              </div>
              <div className="form-field">
                <label className="form-label">Constraints</label>
                <ConstraintBuilder
                  constraints={target.constraints}
                  onChange={(constraints) => setTarget({ ...target, constraints })}
                  projectId={projectId}
                  template={template}
                  disabled={loading}
                  targetType={target.target_type}
                />
              </div>
            </div>
          )}
        </div>

        {/* Subcard 2: Plan Options (Domain Constraints) */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Options (Domain Constraints)</h3>
            <button
              type="button"
              onClick={() => toggleCard('planOptions')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.planOptions ? '-' : '+'}
            </button>
          </div>
          {expandedCards.planOptions && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="max-recipe-depth" className="form-label">Max Recipe Depth</label>
                <input
                  id="max-recipe-depth"
                  type="number"
                  value={domainConstraints.max_recipe_depth}
                  onChange={(e) => setDomainConstraints({ ...domainConstraints, max_recipe_depth: parseInt(e.target.value) || 0 })}
                  className="form-input"
                />
              </div>
              <div className="form-field">
                <label>
                  <input
                    type="checkbox"
                    checked={domainConstraints.allow_partial_recipe_execution}
                    onChange={(e) => setDomainConstraints({ ...domainConstraints, allow_partial_recipe_execution: e.target.checked })}
                  /> Allow Partial Recipe Execution
                </label>
              </div>
              <p className="card-description" style={{ fontSize: '14px' }}>
                Additional constraint rules will be implemented here.
              </p>
            </div>
          )}
        </div>

        {/* Subcard 3: Search Parameters */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Search Parameters</h3>
            <button
              type="button"
              onClick={() => toggleCard('searchParameters')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.searchParameters ? '-' : '+'}
            </button>
          </div>
          {expandedCards.searchParameters && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="max-recursion-depth" className="form-label">Max Recursion Depth</label>
                <input
                  id="max-recursion-depth"
                  type="number"
                  value={searchParameters.max_recursion_depth}
                  onChange={(e) => setSearchParameters({ ...searchParameters, max_recursion_depth: parseInt(e.target.value) || 0 })}
                  className="form-input"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="max-branch-width" className="form-label">Max Branch Width</label>
                <input
                  id="max-branch-width"
                  type="number"
                  value={searchParameters.max_branch_width}
                  onChange={(e) => setSearchParameters({ ...searchParameters, max_branch_width: parseInt(e.target.value) || 0 })}
                  className="form-input"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="max-solutions-returned" className="form-label">Max Solutions Returned</label>
                <input
                  id="max-solutions-returned"
                  type="number"
                  value={searchParameters.max_solutions_returned}
                  onChange={(e) => setSearchParameters({ ...searchParameters, max_solutions_returned: parseInt(e.target.value) || 0 })}
                  className="form-input"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <label htmlFor="optimization-level" className="form-label">Optimization Level</label>
                <input
                  id="optimization-level"
                  type="number"
                  value={searchParameters.optimization_level}
                  onChange={(e) => setSearchParameters({ ...searchParameters, optimization_level: parseInt(e.target.value) || 0 })}
                  className="form-input"
                />
              </div>
              <div className="form-field">
                <label>
                  <input
                    type="checkbox"
                    checked={searchParameters.allow_loops}
                    onChange={(e) => setSearchParameters({ ...searchParameters, allow_loops: e.target.checked })}
                  /> Allow Loops
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Subcard 4: Score Rules */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Score Rules</h3>
            <button
              type="button"
              onClick={() => toggleCard('scoreRules')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.scoreRules ? '-' : '+'}
            </button>
          </div>
          {expandedCards.scoreRules && (
            <p className="card-description" style={{ fontSize: '14px' }}>
              Score rules (user variables and formulas) will be implemented here.
            </p>
          )}
        </div>

        {/* Form actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
          <Link
            to={`/projects/${projectId}/planning/planning_output_solver`}
            className="button button--secondary"
            style={{ textDecoration: 'none' }}
          >
            Cancel
          </Link>
          <button
            type="submit"
            className="button button--primary"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Run'}
          </button>
        </div>
      </form>
    </div>
  );
}
