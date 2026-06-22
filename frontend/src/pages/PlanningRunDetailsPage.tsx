import { useState, useEffect } from 'react';
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPlanningRunWithResults, PlanningRunWithResults } from '../api/planning';
import { PlanningGraph } from '../components/planning/PlanningGraph';

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
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const loadRun = async () => {
      if (!runId) return;
      
      setLoading(true);
      setError(null);
      try {
        const runData = await getPlanningRunWithResults(runId);
        setRun(runData);
        
        // Initialize selected scores - first 4 checked by default
        if (runData.result?.plans && runData.result.plans.length > 0) {
          const scoreKeys = Object.keys(runData.result.plans[0].score || {});
          const initialSelectedScores: Record<string, boolean> = {};
          scoreKeys.forEach((key, index) => {
            initialSelectedScores[key] = index < 4;
          });
          setSelectedScores(initialSelectedScores);
        }
      } catch (error) {
        setError('Failed to load planning run details');
        console.error('Failed to load run:', error);
      } finally {
        setLoading(false);
      }
    };

    loadRun();
  }, [runId]);

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
            <h3 className="card-title" style={{ fontSize: '18px' }}>Running State</h3>
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

        {/* Subcard 6: Input JSON */}
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

        {/* Subcard 7: Result JSON */}
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

        {/* Subcard 8: Results - Stats */}
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

        {/* Subcard 9: Results - Plans */}
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

              <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }} />

              {/* Region 3: Solution */}
              <div>
                <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>
                  {selectedPlanId !== null ? `Solution of Plan ${selectedPlanId}` : 'Solution'}
                </h4>
                {selectedPlanId !== null && run.result?.plans[selectedPlanId] ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center' }}>
                    {Object.entries(run.result.plans[selectedPlanId].score || {}).map(([key, value]) => (
                      <React.Fragment key={key}>
                        <label className="form-label">{key}</label>
                        <span>{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                      </React.Fragment>
                    ))}
                  </div>
                ) : (
                  <span style={{ color: '#666' }}>Select a plan on the Plans Table to view details</span>
                )}
              </div>

              <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }} />

              {/* Region 4: Solution Graph */}
              <div>
                <h4 style={{ fontSize: '16px', marginBottom: '12px' }}>
                  {selectedPlanId !== null ? `Graph for Plan ${selectedPlanId}` : 'Solution Graph'}
                </h4>
                {selectedPlanId !== null && run.result?.plans[selectedPlanId] && run.result?.entities ? (
                  <PlanningGraph
                    graph={{
                      graph_nodes: run.result.plans[selectedPlanId].graph_nodes || [],
                      recipe_edges: run.result.plans[selectedPlanId].recipe_edges || [],
                      material_edges: run.result.plans[selectedPlanId].material_edges || [],
                    }}
                    entities={run.result.entities}
                    recipeDomainName="identity"
                    recipeKeyName="name"
                    materialDomainName="identitiy"
                    materialKeyName="name"
                    displayImages={false}
                    simplifyLevel={0}
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
    </div>
  );
}
