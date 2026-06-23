import { useState, useEffect } from 'react';
import {
  ConstraintSpec,
  TargetSpec,
  DomainConstraints,
  SearchParameters,
  ScoreRules,
  ConstraintRule,
} from '../api/planning';
import { getPlanOutputSolver, createPlanOutputSolver, updatePlanOutputSolver } from '../api/templates';
import { ConstraintBuilder } from './ConstraintBuilder';
import { HorizontalLine } from './HorizontalLine';
import { ConstraintRuleCard } from './ConstraintRuleCard';
import { UserVariableCard } from './UserVariableCard';
import { ScoreFormulaCard } from './ScoreFormulaCard';

type OutputSolverTemplateEditorProps = {
  templateId: string;
  template: any;
};

type SubcardKey = 'planTarget' | 'planOptions' | 'searchParameters' | 'scoreRules' | 'planResultsDefaults';

export function OutputSolverTemplateEditor({ templateId, template }: OutputSolverTemplateEditorProps) {
  // Loading and saving state
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Subcard expansion state
  const [expandedCards, setExpandedCards] = useState<Record<SubcardKey, boolean>>({
    planTarget: true,
    planOptions: false,
    searchParameters: false,
    scoreRules: false,
    planResultsDefaults: false,
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
    max_recipe_depth: 30,
    allow_partial_recipe_execution: false,
  });

  // Search parameters state
  const [searchParameters, setSearchParameters] = useState<SearchParameters>({
    max_recursion_depth: 50,
    max_branch_width: 50,
    allow_loops: true,
    max_solutions_returned: 30,
    optimization_level: 1,
  });

  // Score rules state
  const [scoreRules, setScoreRules] = useState<ScoreRules>({
    user_variables: [],
    score_formulas: [],
  });

  // Plan Results Defaults state
  const [mainScoreName, setMainScoreName] = useState<string>('');
  const [mainScoreDescending, setMainScoreDescending] = useState<boolean>(false);
  const [defaultScores, setDefaultScores] = useState<string[]>([]);
  const [materialDisplayParam, setMaterialDisplayParam] = useState<string>('');
  const [recipeDisplayParam, setRecipeDisplayParam] = useState<string>('');
  const [simplifyLabel, setSimplifyLabel] = useState<number>(1);
  const [useImages, setUseImages] = useState<boolean>(true);

  // Helper to get domain:key options from template
  const getDomainKeyOptions = (kind: 'recipe' | 'material') => {
    if (!template?.entity_types) return [];
    
    const entityType = template.entity_types.find((et: any) => et.kind === kind);
    if (!entityType?.parameter_definitions) return [];
    
    const domainKeySet = new Set<string>();
    entityType.parameter_definitions.forEach((param: any) => {
      if (param.domain && param.key) {
        domainKeySet.add(`${param.domain}:${param.key}`);
      }
    });
    
    return Array.from(domainKeySet).sort();
  };

  // Initialize display parameters when template changes
  useEffect(() => {
    if (template) {
      const materialOptions = getDomainKeyOptions('material');
      const recipeOptions = getDomainKeyOptions('recipe');
      if (materialOptions.length > 0 && !materialDisplayParam) {
        setMaterialDisplayParam(materialOptions[0]);
      }
      if (recipeOptions.length > 0 && !recipeDisplayParam) {
        setRecipeDisplayParam(recipeOptions[0]);
      }
    }
  }, [template]);

  // Load saved configuration when templateId changes
  useEffect(() => {
    if (templateId) {
      loadSavedConfiguration();
    }
  }, [templateId]);

  const loadSavedConfiguration = async () => {
    setLoading(true);
    setError(null);
    try {
      const config = await getPlanOutputSolver(templateId);
      if (config) {
        // Load new_plan_defaults
        if (config.new_plan_defaults) {
          if (config.new_plan_defaults.target) {
            setTarget(config.new_plan_defaults.target);
          }
          if (config.new_plan_defaults.domain_constraints) {
            setDomainConstraints(config.new_plan_defaults.domain_constraints);
          }
          if (config.new_plan_defaults.search_parameters) {
            setSearchParameters(config.new_plan_defaults.search_parameters);
          }
          if (config.new_plan_defaults.score_rules) {
            setScoreRules(config.new_plan_defaults.score_rules);
          }
        }
        // Load results_view_defaults
        if (config.results_view_defaults) {
          if (config.results_view_defaults.main_score_name !== undefined) {
            setMainScoreName(config.results_view_defaults.main_score_name);
          }
          if (config.results_view_defaults.main_score_descending !== undefined) {
            setMainScoreDescending(config.results_view_defaults.main_score_descending);
          }
          if (config.results_view_defaults.default_scores) {
            setDefaultScores(config.results_view_defaults.default_scores);
          }
          if (config.results_view_defaults.material_display_param) {
            setMaterialDisplayParam(config.results_view_defaults.material_display_param);
          }
          if (config.results_view_defaults.recipe_display_param) {
            setRecipeDisplayParam(config.results_view_defaults.recipe_display_param);
          }
          if (config.results_view_defaults.simplify_label !== undefined) {
            setSimplifyLabel(config.results_view_defaults.simplify_label);
          }
          if (config.results_view_defaults.use_images !== undefined) {
            setUseImages(config.results_view_defaults.use_images);
          }
        }
      }
    } catch (err) {
      setError('Failed to load saved configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      // Build new_plan_defaults object (format matches planning_runs API)
      const newPlanDefaults = {
        target,
        domain_constraints: domainConstraints,
        search_parameters: searchParameters,
        score_rules: scoreRules,
      };

      // Build results_view_defaults object
      const resultsViewDefaults = {
        main_score_name: mainScoreName,
        main_score_descending: mainScoreDescending,
        default_scores: defaultScores,
        material_display_param: materialDisplayParam,
        recipe_display_param: recipeDisplayParam,
        simplify_label: simplifyLabel,
        use_images: useImages,
      };

      // Check if config already exists
      const existing = await getPlanOutputSolver(templateId);
      if (existing) {
        await updatePlanOutputSolver(templateId, {
          new_plan_defaults: newPlanDefaults,
          results_view_defaults: resultsViewDefaults,
        });
      } else {
        await createPlanOutputSolver(templateId, {
          new_plan_defaults: newPlanDefaults,
          results_view_defaults: resultsViewDefaults,
        });
      }
    } catch (err) {
      setError('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const toggleCard = (key: SubcardKey) => {
    setExpandedCards((prev: Record<SubcardKey, boolean>) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Helper to add a new constraint rule to a list
  const addConstraintRule = (field: keyof DomainConstraints) => {
    const newRule: ConstraintRule = { constraints: [] };
    setDomainConstraints((prev: DomainConstraints) => ({
      ...prev,
      [field]: [...(prev[field] as ConstraintRule[]), newRule]
    }));
  };

  // Helper to remove a constraint rule from a list
  const removeConstraintRule = (field: keyof DomainConstraints, index: number) => {
    setDomainConstraints((prev: DomainConstraints) => ({
      ...prev,
      [field]: (prev[field] as ConstraintRule[]).filter((_: ConstraintRule, i: number) => i !== index)
    }));
  };

  // Helper to update constraints within a rule
  const updateRuleConstraints = (field: keyof DomainConstraints, ruleIndex: number, constraints: ConstraintSpec[]) => {
    setDomainConstraints((prev: DomainConstraints) => {
      const rules = [...(prev[field] as ConstraintRule[])];
      rules[ruleIndex] = { constraints };
      return { ...prev, [field]: rules };
    });
  };

  // Helper to add a new user variable
  const addUserVariable = () => {
    const availableParams = template?.entity_types?.[0]?.parameter_definitions || [];
    const firstParam = availableParams[0];
    
    const newVariable = {
      name: '',
      parameter_domain: firstParam?.domain || '',
      parameter_key: firstParam?.key || '',
      constraints: [],
    };
    
    setScoreRules((prev: ScoreRules) => ({
      ...prev,
      user_variables: [...prev.user_variables, newVariable]
    }));
  };

  // Helper to remove a user variable
  const removeUserVariable = (index: number) => {
    setScoreRules((prev: ScoreRules) => ({
      ...prev,
      user_variables: prev.user_variables.filter((_: any, i: number) => i !== index)
    }));
  };

  // Helper to update a user variable
  const updateUserVariable = (index: number, variable: any) => {
    setScoreRules((prev: ScoreRules) => {
      const variables = [...prev.user_variables];
      variables[index] = variable;
      return { ...prev, user_variables: variables };
    });
  };

  // Helper to add a new score formula
  const addScoreFormula = () => {
    const newFormula = {
      name: '',
      formula: '',
    };
    
    setScoreRules((prev: ScoreRules) => ({
      ...prev,
      score_formulas: [...prev.score_formulas, newFormula]
    }));
  };

  // Helper to remove a score formula
  const removeScoreFormula = (index: number) => {
    setScoreRules((prev: ScoreRules) => ({
      ...prev,
      score_formulas: prev.score_formulas.filter((_: any, i: number) => i !== index)
    }));
  };

  // Helper to update a score formula
  const updateScoreFormula = (index: number, formula: any) => {
    setScoreRules((prev: ScoreRules) => {
      const formulas = [...prev.score_formulas];
      formulas[index] = formula;
      return { ...prev, score_formulas: formulas };
    });
  };

  // Helper to add a default score
  const addDefaultScore = () => {
    setDefaultScores((prev: string[]) => [...prev, '']);
  };

  // Helper to remove a default score
  const removeDefaultScore = (index: number) => {
    setDefaultScores((prev: string[]) => prev.filter((_: string, i: number) => i !== index));
  };

  // Helper to update a default score
  const updateDefaultScore = (index: number, value: string) => {
    setDefaultScores((prev: string[]) => {
      const scores = [...prev];
      scores[index] = value;
      return scores;
    });
  };

  return (
    <div className="card" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 className="card-title">Output Solver Template</h2>
          <p className="card-description">Configure default values for new planning runs.</p>
        </div>
        <button
          onClick={handleSave}
          className="button button--primary"
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>

      {error && (
        <div className="card state-message" style={{ marginBottom: '16px' }}>
          <p className="state-message__text state-message__text--error">{error}</p>
          <button onClick={() => setError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      {/* Subcard 1: Plan Target */}
      <div className="card mb-4" style={{ marginBottom: '16px', marginTop: '16px' }}>
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
                onChange={(e) => setTarget({ ...target, target_type: e.target.value as 'material' | 'recipe', constraints: [] })}
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
                projectId={undefined}
                template={template}
                disabled={false}
                targetType={target.target_type}
              />
            </div>
          </div>
        )}
      </div>

      {/* Subcard 2: Plan Options (Domain Constraints) */}
      <div className="card mb-4" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Options</h3>
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
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
              <label htmlFor="allow-partial-recipe-execution" className="form-label">Allow Partial Recipe Execution</label>
              <input
                id="allow-partial-recipe-execution"
                type="checkbox"
                checked={domainConstraints.allow_partial_recipe_execution}
                onChange={(e) => setDomainConstraints({ ...domainConstraints, allow_partial_recipe_execution: e.target.checked })}
                style={{ width: '19px', height: '19px' }}
              />
            </div>

            <HorizontalLine />

            {/* Do Not Expand Materials Matching */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Do Not Expand Materials Matching</h4>
              {domainConstraints.do_not_expand_materials_matching.map((rule: ConstraintRule, index: number) => (
                <ConstraintRuleCard
                  key={index}
                  constraints={rule.constraints}
                  onChange={(constraints) => updateRuleConstraints('do_not_expand_materials_matching', index, constraints)}
                  onRemove={() => removeConstraintRule('do_not_expand_materials_matching', index)}
                  projectId={undefined}
                  template={template}
                  disabled={false}
                  targetType="material"
                />
              ))}
              <button
                type="button"
                onClick={() => addConstraintRule('do_not_expand_materials_matching')}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Rule
              </button>
            </div>

            <HorizontalLine />

            {/* Forbidden Materials Matching */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Forbidden Materials Matching</h4>
              {domainConstraints.forbidden_materials_matching.map((rule: ConstraintRule, index: number) => (
                <ConstraintRuleCard
                  key={index}
                  constraints={rule.constraints}
                  onChange={(constraints) => updateRuleConstraints('forbidden_materials_matching', index, constraints)}
                  onRemove={() => removeConstraintRule('forbidden_materials_matching', index)}
                  projectId={undefined}
                  template={template}
                  disabled={false}
                  targetType="material"
                />
              ))}
              <button
                type="button"
                onClick={() => addConstraintRule('forbidden_materials_matching')}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Rule
              </button>
            </div>

            <HorizontalLine />

            {/* Forbidden Recipe Matching */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Forbidden Recipe Matching</h4>
              {domainConstraints.forbidden_recipe_matching.map((rule: ConstraintRule, index: number) => (
                <ConstraintRuleCard
                  key={index}
                  constraints={rule.constraints}
                  onChange={(constraints) => updateRuleConstraints('forbidden_recipe_matching', index, constraints)}
                  onRemove={() => removeConstraintRule('forbidden_recipe_matching', index)}
                  projectId={undefined}
                  template={template}
                  disabled={false}
                  targetType="recipe"
                />
              ))}
              <button
                type="button"
                onClick={() => addConstraintRule('forbidden_recipe_matching')}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Rule
              </button>
            </div>

            <HorizontalLine />

            {/* Required Materials Matching */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Required Materials Matching</h4>
              {domainConstraints.required_materials_matching.map((rule: ConstraintRule, index: number) => (
                <ConstraintRuleCard
                  key={index}
                  constraints={rule.constraints}
                  onChange={(constraints) => updateRuleConstraints('required_materials_matching', index, constraints)}
                  onRemove={() => removeConstraintRule('required_materials_matching', index)}
                  projectId={undefined}
                  template={template}
                  disabled={false}
                  targetType="material"
                />
              ))}
              <button
                type="button"
                onClick={() => addConstraintRule('required_materials_matching')}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Rule
              </button>
            </div>

            <HorizontalLine />

            {/* Required Recipe Matching */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Required Recipe Matching</h4>
              {domainConstraints.required_recipe_matching.map((rule: ConstraintRule, index: number) => (
                <ConstraintRuleCard
                  key={index}
                  constraints={rule.constraints}
                  onChange={(constraints) => updateRuleConstraints('required_recipe_matching', index, constraints)}
                  onRemove={() => removeConstraintRule('required_recipe_matching', index)}
                  projectId={undefined}
                  template={template}
                  disabled={false}
                  targetType="recipe"
                />
              ))}
              <button
                type="button"
                onClick={() => addConstraintRule('required_recipe_matching')}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Rule
              </button>
            </div>
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
            <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
              <label htmlFor="allow-loops" className="form-label">Allow Loops</label>
              <input
                id="allow-loops"
                type="checkbox"
                checked={searchParameters.allow_loops}
                onChange={(e) => setSearchParameters({ ...searchParameters, allow_loops: e.target.checked })}
                style={{ width: '19px', height: '19px' }}
              />
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* User Variables Section */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>User Variables</h4>
              <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                Define variables that can be used in score formulas. Each variable aggregates parameter values from materials/recipes matching the constraints.
              </p>
              {scoreRules.user_variables.map((variable: any, index: number) => (
                <div key={index}>
                  <UserVariableCard
                    variable={variable}
                    onChange={(variable) => updateUserVariable(index, variable)}
                    onRemove={() => removeUserVariable(index)}
                    projectId={undefined}
                    template={template}
                    disabled={false}
                  />
                </div>
              ))}
              <button
                type="button"
                onClick={addUserVariable}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add User Variable
              </button>
            </div>

            <HorizontalLine />

            {/* Score Formulas Section */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Score Formulas</h4>
              <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                Define formulas to calculate scores for plans. Use variable names from User Variables.
              </p>
              {scoreRules.score_formulas.map((formula: any, index: number) => (
                <div key={index}>
                  <ScoreFormulaCard
                    formula={formula}
                    onChange={(formula) => updateScoreFormula(index, formula)}
                    onRemove={() => removeScoreFormula(index)}
                    disabled={false}
                  />
                </div>
              ))}
              <button
                type="button"
                onClick={addScoreFormula}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Score Formula
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Subcard 5: Plan Results Defaults */}
      <div className="card mb-4" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Results Defaults</h3>
          <button
            type="button"
            onClick={() => toggleCard('planResultsDefaults')}
            className="button button--secondary"
            style={{ padding: '2px 8px', minWidth: '30px' }}
          >
            {expandedCards.planResultsDefaults ? '-' : '+'}
          </button>
        </div>
        {expandedCards.planResultsDefaults && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Main Score */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Main Score</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                  <label htmlFor="main-score-name" className="form-label">Score Name</label>
                  <input
                    id="main-score-name"
                    type="text"
                    value={mainScoreName}
                    onChange={(e) => setMainScoreName(e.target.value)}
                    className="form-input"
                    placeholder="e.g., total_score"
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                  <label htmlFor="main-score-descending" className="form-label">Descending</label>
                  <input
                    id="main-score-descending"
                    type="checkbox"
                    checked={mainScoreDescending}
                    onChange={(e) => setMainScoreDescending(e.target.checked)}
                    style={{ width: '19px', height: '19px' }}
                  />
                </div>
              </div>
            </div>

            <HorizontalLine />

            {/* Default Scores */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Default Scores</h4>
              <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                Define which scores are displayed by default in the results table.
              </p>
              {defaultScores.map((score, index) => (
                <div key={index} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                  <input
                    type="text"
                    value={score}
                    onChange={(e) => updateDefaultScore(index, e.target.value)}
                    className="form-input"
                    placeholder="Score name"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={() => removeDefaultScore(index)}
                    className="button button--danger"
                    style={{ padding: '4px 8px', fontSize: '12px' }}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addDefaultScore}
                className="button button--secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                + Add Score
              </button>
            </div>

            <HorizontalLine />

            {/* Material Display Parameter */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Material Display Parameter</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label htmlFor="material-display-param" className="form-label">Domain:Key</label>
                <select
                  id="material-display-param"
                  value={materialDisplayParam}
                  onChange={(e) => setMaterialDisplayParam(e.target.value)}
                  className="form-input"
                >
                  {getDomainKeyOptions('material').map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
            </div>

            <HorizontalLine />

            {/* Recipe Display Parameter */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Recipe Display Parameter</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label htmlFor="recipe-display-param" className="form-label">Domain:Key</label>
                <select
                  id="recipe-display-param"
                  value={recipeDisplayParam}
                  onChange={(e) => setRecipeDisplayParam(e.target.value)}
                  className="form-input"
                >
                  {getDomainKeyOptions('recipe').map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
            </div>

            <HorizontalLine />

            {/* Simplify Label */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Simplify Label</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label htmlFor="simplify-label" className="form-label">Level</label>
                <input
                  id="simplify-label"
                  type="number"
                  value={simplifyLabel}
                  onChange={(e) => setSimplifyLabel(Number(e.target.value))}
                  className="form-input"
                  min="0"
                  step="1"
                />
              </div>
            </div>

            <HorizontalLine />

            {/* Use Images */}
            <div>
              <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Use Images</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label htmlFor="use-images" className="form-label">Enabled</label>
                <input
                  id="use-images"
                  type="checkbox"
                  checked={useImages}
                  onChange={(e) => setUseImages(e.target.checked)}
                  style={{ width: '19px', height: '19px' }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
