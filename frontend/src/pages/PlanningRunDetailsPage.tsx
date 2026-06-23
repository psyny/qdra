import { useState, useEffect, useRef } from 'react';
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPlanningRunWithResults, PlanningRunWithResults } from '../api/planning';
import { PlanningGraph } from '../components/planning/PlanningGraph';
import { getProjectTemplate } from '../api/projects';
import { getEntity } from '../api/entities';

type PlanningRunDetailsPageProps = {
  projectId: string;
};

type SubcardKey = 'runningState' | 'planTarget' | 'planOptions' | 'searchParameters' | 'scoreRules' | 'inputJson' | 'resultJson' | 'resultsStats' | 'resultsPlans';

export function PlanningRunDetailsPage({ projectId }: PlanningRunDetailsPageProps) {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<PlanningRunWithResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [template, setTemplate] = useState<any>(null);
  const [imagesMap, setImagesMap] = useState<Record<string, string>>({});
  
  // Graph selector state
  const [recipeDomainKey, setRecipeDomainKey] = useState<string>('');
  const [materialDomainKey, setMaterialDomainKey] = useState<string>('');
  const [simplifyLevel, setSimplifyLevel] = useState<number>(1);
  const [useImages, setUseImages] = useState<boolean>(false);
  const graphSectionRef = useRef<HTMLDivElement>(null);
  
  // Subcard expansion state
  const [expandedCards, setExpandedCards] = useState<Record<SubcardKey, boolean>>({
    runningState: true,
    planTarget: true,
    planOptions: true,
    searchParameters: false,
    scoreRules: false,
    inputJson: false,
    resultJson: false,
    resultsStats: false,
    resultsPlans: true,
  });

  // Results tab state
  const [selectedScores, setSelectedScores] = useState<Record<string, boolean>>({});
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [hoveredPlanId, setHoveredPlanId] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Helper function to get domain:key options from template data
  const getDomainKeyOptionsFromTemplate = (templateData: any, kind: 'recipe' | 'material') => {
    if (!templateData?.entity_types) return [];
    
    const entityType = templateData.entity_types.find((et: any) => et.kind === kind);
    if (!entityType?.parameter_definitions) return [];
    
    const domainKeySet = new Set<string>();
    entityType.parameter_definitions.forEach((param: any) => {
      if (param.domain && param.key) {
        domainKeySet.add(`${param.domain}:${param.key}`);
      }
    });
    
    return Array.from(domainKeySet).sort();
  };

  const loadRun = async () => {
    if (!runId) return;

    setLoading(true);
    setError(null);
    try {
      const runData = await getPlanningRunWithResults(runId);
      setRun(runData);

      // Load template to get domain:key options
      const templateData = await getProjectTemplate(projectId);
      setTemplate(templateData);

      // Initialize domain keys from template defaults
      const recipeOptions = getDomainKeyOptionsFromTemplate(templateData, 'recipe');
      const materialOptions = getDomainKeyOptionsFromTemplate(templateData, 'material');
      
      // Apply template defaults for graph display if available
      const resultsDefaults = templateData?.plan_output_solver?.results_view_defaults;
      if (resultsDefaults) {
        if (resultsDefaults.recipe_display_param && recipeOptions.includes(resultsDefaults.recipe_display_param)) {
          setRecipeDomainKey(resultsDefaults.recipe_display_param);
        } else if (recipeOptions.length > 0) {
          setRecipeDomainKey(recipeOptions[0]);
        }
        
        if (resultsDefaults.material_display_param && materialOptions.includes(resultsDefaults.material_display_param)) {
          setMaterialDomainKey(resultsDefaults.material_display_param);
        } else if (materialOptions.length > 0) {
          setMaterialDomainKey(materialOptions[0]);
        }
        
        if (resultsDefaults.simplify_label !== undefined) {
          setSimplifyLevel(resultsDefaults.simplify_label);
        }
        
        if (resultsDefaults.use_images !== undefined) {
          setUseImages(resultsDefaults.use_images);
        }
      } else {
        // Fallback to first option if no template defaults
        if (recipeOptions.length > 0) setRecipeDomainKey(recipeOptions[0]);
        if (materialOptions.length > 0) setMaterialDomainKey(materialOptions[0]);
      }

      // Initialize selected scores and sorting based on template defaults
      if (runData.result?.plans && runData.result.plans.length > 0) {
        const scoreKeys = Object.keys(runData.result.plans[0].score || {});
        const initialSelectedScores: Record<string, boolean> = {};
        
        // Start with all unchecked
        scoreKeys.forEach(key => {
          initialSelectedScores[key] = false;
        });
        
        // Apply template defaults if available
        const resultsDefaults = templateData?.plan_output_solver?.results_view_defaults;
        if (resultsDefaults) {
          // Mark main score if it exists in the scores list
          if (resultsDefaults.main_score_name && scoreKeys.includes(resultsDefaults.main_score_name)) {
            initialSelectedScores[resultsDefaults.main_score_name] = true;
          }
          
          // Mark default scores if they exist in the scores list
          if (resultsDefaults.default_scores && Array.isArray(resultsDefaults.default_scores)) {
            resultsDefaults.default_scores.forEach((scoreName: string) => {
              if (scoreKeys.includes(scoreName)) {
                initialSelectedScores[scoreName] = true;
              }
            });
          }
          
          // Set initial sorting based on main score
          if (resultsDefaults.main_score_name && scoreKeys.includes(resultsDefaults.main_score_name)) {
            setSortColumn(resultsDefaults.main_score_name);
            setSortDirection(resultsDefaults.main_score_descending ? 'desc' : 'asc');
          }
        }
        
        // If we have fewer than 4 marked scores, mark additional scores until we have 4
        const markedCount = Object.values(initialSelectedScores).filter(v => v).length;
        if (markedCount < 4) {
          let additionalNeeded = 4 - markedCount;
          for (const key of scoreKeys) {
            if (!initialSelectedScores[key]) {
              initialSelectedScores[key] = true;
              additionalNeeded--;
              if (additionalNeeded === 0) break;
            }
          }
        }
        
        setSelectedScores(initialSelectedScores);
      }
    } catch (error) {
      setError('Failed to load planning run details');
      console.error('Failed to load run:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRun();
  }, [runId, projectId]);

  // Poll for run completion every 2 seconds
  useEffect(() => {
    if (!run || run.status === 'completed' || run.status === 'failed') {
      return;
    }

    const interval = setInterval(() => {
      loadRun();
    }, 2000);

    return () => clearInterval(interval);
  }, [run]);

  // Dynamically expand/collapse cards based on run status
  useEffect(() => {
    if (!run) return;

    if (run.status === 'completed') {
      setExpandedCards({
        runningState: false,
        planTarget: false,
        planOptions: false,
        searchParameters: false,
        scoreRules: false,
        inputJson: false,
        resultJson: false,
        resultsStats: false,
        resultsPlans: true,
      });

      // Auto-select first plan if available
      if (run.result?.plans && run.result.plans.length > 0) {
        setSelectedPlanId(0);
      }
    } else {
      setExpandedCards({
        runningState: true,
        planTarget: false,
        planOptions: false,
        searchParameters: false,
        scoreRules: false,
        inputJson: false,
        resultJson: false,
        resultsStats: false,
        resultsPlans: false,
      });
    }
  }, [run]);

  // Build imagesMap when useImages is enabled and a plan is selected
  useEffect(() => {
    if (!useImages || selectedPlanId === null || !run?.result) {
      setImagesMap({});
      return;
    }

    const plan = run.result.plans[selectedPlanId];
    if (!plan?.graph_nodes) return;

    const entities = run.result.entities;
    const newMap: Record<string, string> = {};
    const fetches: Promise<void>[] = [];

    plan.graph_nodes.forEach((node: any) => {
      if (node.kind === 'material' && node.material_id) {
        const entity = entities?.materials[node.material_id];
        if (entity) {
          if (entity.image?.url) {
            newMap[entity.id] = entity.image.url;
          } else {
            fetches.push(
              getEntity(projectId, entity.id)
                .then(fetched => { if (fetched.image?.url) newMap[entity.id] = fetched.image.url; })
                .catch(() => {})
            );
          }
        }
      }
      if (node.kind === 'recipe_execution' && node.recipe_id) {
        const entity = entities?.recipes[node.recipe_id];
        if (entity) {
          if (entity.image?.url) {
            newMap[entity.id] = entity.image.url;
          } else {
            fetches.push(
              getEntity(projectId, entity.id)
                .then(fetched => { if (fetched.image?.url) newMap[entity.id] = fetched.image.url; })
                .catch(() => {})
            );
          }
        }
      }
    });

    Promise.all(fetches).then(() => setImagesMap({ ...newMap }));
  }, [useImages, selectedPlanId, run, projectId]);

  // Scroll to graph section when a plan is selected
  useEffect(() => {
    if (selectedPlanId !== null) {
      // Small delay to ensure DOM is rendered
      const timeout = setTimeout(() => {
        if (graphSectionRef.current) {
          graphSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
      return () => clearTimeout(timeout);
    }
  }, [selectedPlanId]);

  const scrollToGraph = () => {
    if (graphSectionRef.current) {
      graphSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const toggleCard = (key: SubcardKey) => {
    setExpandedCards(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startDate: string | null, endDate: string | null) => {
    if (!startDate || !endDate) return 'N/A';
    
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const diffMs = end - start;
    
    if (diffMs < 0) return 'N/A';
    
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
      const remainingHours = diffHours % 24;
      if (remainingHours > 0) {
        return `${diffDays}d ${remainingHours}h`;
      }
      return `${diffDays}d`;
    }
    
    if (diffHours > 0) {
      const remainingMinutes = diffMinutes % 60;
      if (remainingMinutes > 0) {
        return `${diffHours}h ${remainingMinutes}m`;
      }
      return `${diffHours}h`;
    }
    
    if (diffMinutes > 0) {
      const remainingSeconds = diffSeconds % 60;
      if (remainingSeconds > 0) {
        return `${diffMinutes}m ${remainingSeconds}s`;
      }
      return `${diffMinutes}m`;
    }
    
    if (diffSeconds > 0) {
      return `${diffSeconds}s`;
    }
    
    return '0s';
  };

  const formatJson = (data: any) => {
    if (!data) return 'No data';
    return JSON.stringify(data, null, 2);
  };

  const handleClone = () => {
    if (!run) return;
    
    // Navigate to new run page with cloned data
    navigate(`/projects/${projectId}/planning/planning_output_solver/new`, {
      state: { cloneData: run.input, cloneName: run.name }
    });
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortedPlans = () => {
    if (!run.result?.plans) return [];
    
    const plans = [...run.result.plans];
    
    if (!sortColumn) return plans;
    
    plans.sort((a, b) => {
      let aValue: number;
      let bValue: number;
      
      if (sortColumn === 'id') {
        aValue = a.id || 0;
        bValue = b.id || 0;
      } else {
        aValue = a.score?.[sortColumn] ?? 0;
        bValue = b.score?.[sortColumn] ?? 0;
      }
      
      if (sortDirection === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });
    
    return plans;
  };

  // Helper to get domain:key options from template
  const getDomainKeyOptions = (kind: 'recipe' | 'material') => {
    return getDomainKeyOptionsFromTemplate(template, kind);
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading planning run details...</p>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error || 'Planning run not found'}</p>
        <Link to={`/projects/${projectId}/planning/planning_output_solver`} className="button button--secondary">
          Back to Runs
        </Link>
      </div>
    );
  }

  const displayName = run.name || run.id;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 className="card-title mb-4">{displayName}</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Link 
            to={`/projects/${projectId}/planning/planning_output_solver`} 
            className="button button--secondary"
            style={{ height: '35px', display: 'inline-flex', alignItems: 'center' }}
          >
            ← Back to Runs
          </Link>
          <button
            onClick={handleClone}
            className="button button--primary"
            style={{ height: '35px' }}
          >
            Clone Run
          </button>
        </div>
      </div>

        {/* Subcard 1: Running State */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Run Stats</h3>
            <button
              onClick={() => toggleCard('runningState')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.runningState ? '-' : '+'}
            </button>
          </div>
          {expandedCards.runningState && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">ID</label>
                <span>{run.id}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Status</label>
                <span>{run.status}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Type</label>
                <span>{run.type}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Created</label>
                <span>{formatDate(run.created_at)}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Updated</label>
                <span>{formatDate(run.updated_at)}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Started</label>
                <span>{formatDate(run.started_at)}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Finished</label>
                <span>{formatDate(run.finished_at)}</span>
              </div>
              {run.error && (
                <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                  <label className="form-label" style={{ color: 'red' }}>Error</label>
                  <span style={{ color: 'red' }}>{run.error}</span>
                </div>
              )}
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Time to Start</label>
                <span>{formatDuration(run.created_at, run.started_at)}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Time to Complete</label>
                <span>{formatDuration(run.started_at, run.finished_at)}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                <label className="form-label">Time to Solve</label>
                <span>{formatDuration(run.started_at, run.finished_at)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Subcard 2: Results - Plans */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Results - Plans</h3>
            <button
              onClick={() => toggleCard('resultsPlans')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.resultsPlans ? '-' : '+'}
            </button>
          </div>
          {expandedCards.resultsPlans && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

              {/* Region 1: Scores and Plans - Horizontal Layout */}
              <div style={{ display: 'flex', gap: '24px' }}>
                {/* Scores on the left */}
                <div style={{ width: '200px', flexShrink: 0 }}>
                  <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>Scores Displayed</h4>
                  {run.result?.plans && run.result.plans.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {Object.keys(run.result.plans[0].score || {}).map((scoreKey) => (
                        <div key={scoreKey} style={{ display: 'flex', alignItems: 'center' }}>
                          <input
                            type="checkbox"
                            id={`score-${scoreKey}`}
                            checked={selectedScores[scoreKey] || false}
                            onChange={(e) => setSelectedScores(prev => ({ ...prev, [scoreKey]: e.target.checked }))}
                            style={{ marginRight: '8px', verticalAlign: 'middle' }}
                          />
                          <label htmlFor={`score-${scoreKey}`} style={{ cursor: 'pointer', fontSize: '13px' }}>{scoreKey}</label>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span style={{ color: '#666' }}>No scores available</span>
                  )}
                </div>

                {/* Plans on the right */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>Plans Table</h4>
                  {run.result?.plans && run.result.plans.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                            <th 
                              style={{ padding: '8px', textAlign: 'left', cursor: 'pointer', userSelect: 'none', fontSize: '12px' }}
                              onClick={() => handleSort('id')}
                            >
                              ID {sortColumn === 'id' && (sortDirection === 'asc' ? '↑' : '↓')}
                            </th>
                            {Object.keys(selectedScores).filter(key => selectedScores[key]).map(scoreKey => (
                              <th 
                                key={scoreKey}
                                style={{ padding: '8px', textAlign: 'left', cursor: 'pointer', userSelect: 'none', fontSize: '12px' }}
                                onClick={() => handleSort(scoreKey)}
                              >
                                {scoreKey} {sortColumn === scoreKey && (sortDirection === 'asc' ? '↑' : '↓')}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {getSortedPlans().map((plan, index) => (
                            <tr 
                              key={index}
                              onClick={() => setSelectedPlanId(index)}
                              onMouseEnter={(e: React.MouseEvent) => {
                                setHoveredPlanId(index);
                                setMousePosition({ x: e.clientX, y: e.clientY });
                              }}
                              onMouseMove={(e: React.MouseEvent) => {
                                if (hoveredPlanId === index) {
                                  setMousePosition({ x: e.clientX, y: e.clientY });
                                }
                              }}
                              onMouseLeave={() => {
                                setHoveredPlanId(null);
                                setMousePosition(null);
                              }}
                              style={{ 
                                cursor: 'pointer',
                                backgroundColor: selectedPlanId === index ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                                borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
                              }}
                            >
                              <td style={{ padding: '8px' }}>{index}</td>
                              {Object.keys(selectedScores).filter(key => selectedScores[key]).map(scoreKey => (
                                <td key={scoreKey} style={{ padding: '8px' }}>
                                  {plan.score?.[scoreKey] !== undefined ? plan.score[scoreKey].toFixed(2) : 'N/A'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <span style={{ color: '#666' }}>No plans available</span>
                  )}
                </div>
              </div>

              {/* Tooltip for hovered plan */}
              {hoveredPlanId !== null && run.result?.plans[hoveredPlanId] && mousePosition && (
                <div style={{
                  position: 'fixed',
                  left: mousePosition.x + 10,
                  top: mousePosition.y + 10,
                  backgroundColor: '#1a1a1a',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '4px',
                  padding: '8px',
                  minWidth: '200px',
                  zIndex: 1000,
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
                  fontSize: '11px',
                  pointerEvents: 'none',
                }}>
                  {Object.entries(run.result.plans[hoveredPlanId].score || {}).map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '2px' }}>
                      <span style={{ opacity: 0.7 }}>{key}:</span>
                      <span>{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Region 3: Solution Graph */}
              <div ref={graphSectionRef} style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '24px' }}>
                <h4 
                  style={{ fontSize: '16px', marginBottom: '12px', cursor: 'pointer' }}
                  onClick={scrollToGraph}
                >
                  {selectedPlanId !== null ? `Graph for Plan ${selectedPlanId}` : 'Solution Graph'}
                </h4>
                
                {/* Graph selectors */}
                <div style={{ display: 'flex', gap: '16px', marginBottom: '12px', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
                    <label style={{ fontSize: '13px', fontWeight: 'bold' }}>Recipe Display Parameter</label>
                    <select
                      value={recipeDomainKey}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setRecipeDomainKey(e.target.value)}
                      className="form-input"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      {getDomainKeyOptions('recipe').map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
                    <label style={{ fontSize: '13px', fontWeight: 'bold' }}>Material Display Parameter</label>
                    <select
                      value={materialDomainKey}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMaterialDomainKey(e.target.value)}
                      className="form-input"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      {getDomainKeyOptions('material').map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
                    <label style={{ fontSize: '13px', fontWeight: 'bold' }}>Simplify Level</label>
                    <input
                      type="number"
                      value={simplifyLevel}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSimplifyLevel(Number(e.target.value))}
                      className="form-input"
                      style={{ padding: '4px 8px', fontSize: '12px', width: '60px' }}
                      min="0"
                      step="1"
                    />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
                    <label style={{ fontSize: '13px', fontWeight: 'bold' }}>Use Images</label>
                    <input
                      type="checkbox"
                      checked={useImages}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUseImages(e.target.checked)}
                      style={{ width: '19px', height: '19px' }}
                    />
                  </div>
                </div>
                
                {selectedPlanId !== null && run.result?.plans[selectedPlanId] && run.result?.entities ? (
                  <PlanningGraph
                    graph={{
                      graph_nodes: run.result.plans[selectedPlanId].graph_nodes || [],
                      recipe_edges: run.result.plans[selectedPlanId].recipe_edges || [],
                      material_edges: run.result.plans[selectedPlanId].material_edges || [],
                    }}
                    entities={run.result.entities}
                    imagesMap={imagesMap}
                    recipeDomainName={recipeDomainKey.split(':')[0]}
                    recipeKeyName={recipeDomainKey.split(':')[1]}
                    materialDomainName={materialDomainKey.split(':')[0]}
                    materialKeyName={materialDomainKey.split(':')[1]}
                    simplifyLevel={simplifyLevel}
                  />
                ) : (
                  <span style={{ color: '#666' }}>
                    {selectedPlanId !== null ? 'No graph data available for this plan' : 'Select a plan on the Plans Table to view the graph'}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Subcard 3: Results - Stats */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Results - Stats</h3>
            <button
              onClick={() => toggleCard('resultsStats')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.resultsStats ? '-' : '+'}
            </button>
          </div>
          {expandedCards.resultsStats && (
            <div>
              {run.result?.discarded_plans_stats ? (
                <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                  {Object.entries(run.result.discarded_plans_stats).map(([key, value]) => (
                    <React.Fragment key={key}>
                      <label className="form-label">{key}</label>
                      <span>{String(value)}</span>
                    </React.Fragment>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#666' }}>No stats available</span>
              )}
            </div>
          )}
        </div>

        {/* Subcard 4: Input JSON */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Input JSON</h3>
            <button
              onClick={() => toggleCard('inputJson')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.inputJson ? '-' : '+'}
            </button>
          </div>
          {expandedCards.inputJson && (
            <pre style={{ 
              backgroundColor: '#1a1a1a', 
              color: '#ffffff',
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              maxHeight: '400px',
              fontSize: '12px'
            }}>
              {formatJson(run.input)}
            </pre>
          )}
        </div>

        {/* Subcard 5: Result JSON */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Result JSON</h3>
            <button
              onClick={() => toggleCard('resultJson')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.resultJson ? '-' : '+'}
            </button>
          </div>
          {expandedCards.resultJson && (
            <pre style={{ 
              backgroundColor: '#1a1a1a', 
              color: '#ffffff',
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              maxHeight: '400px',
              fontSize: '12px'
            }}>
              {formatJson(run.result)}
            </pre>
          )}
        </div>
    </div>
  );
}
