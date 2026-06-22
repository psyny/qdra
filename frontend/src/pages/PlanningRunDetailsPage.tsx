import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPlanningRunWithResults, createPlanningRun, PlanningRunWithResults } from '../api/planning';

type PlanningRunDetailsPageProps = {
  projectId: string;
};

type SubcardKey = 'runningState' | 'planTarget' | 'planOptions' | 'searchParameters' | 'scoreRules' | 'results';

export function PlanningRunDetailsPage({ projectId }: PlanningRunDetailsPageProps) {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<PlanningRunWithResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cloning, setCloning] = useState(false);
  
  // Subcard expansion state
  const [expandedCards, setExpandedCards] = useState<Record<SubcardKey, boolean>>({
    runningState: true,
    planTarget: true,
    planOptions: true,
    searchParameters: false,
    scoreRules: false,
    results: true,
  });

  useEffect(() => {
    const loadRun = async () => {
      if (!runId) return;
      
      setLoading(true);
      setError(null);
      try {
        const runData = await getPlanningRunWithResults(runId);
        setRun(runData);
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

  const formatJson = (data: any) => {
    if (!data) return 'No data';
    return JSON.stringify(data, null, 2);
  };

  const handleClone = async () => {
    if (!run) return;
    
    setCloning(true);
    setError(null);
    try {
      const clonedRun = await createPlanningRun({
        name: run.name,
        type: run.type,
        status: 'pending',
        input: run.input,
      });
      navigate(`/projects/${projectId}/planning/planning_output_solver/${clonedRun.id}`);
    } catch (err) {
      setError('Failed to clone run. Please try again.');
      console.error('Failed to clone run:', err);
    } finally {
      setCloning(false);
    }
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
      <div className="mb-4" style={{ marginBottom: '16px' }}>
        <Link to={`/projects/${projectId}/planning/planning_output_solver`} className="button button--secondary">
          ← Back to Runs
        </Link>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 className="card-title mb-4">{displayName}</h2>
          <button
            onClick={handleClone}
            disabled={cloning}
            className="button button--primary"
          >
            {cloning ? 'Cloning...' : 'Clone Run'}
          </button>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <span><strong>ID:</strong> {run.id}</span>
                <span><strong>Status:</strong> {run.status}</span>
                <span><strong>Type:</strong> {run.type}</span>
              </div>
              <div style={{ display: 'flex', gap: '16px' }}>
                <span><strong>Created:</strong> {formatDate(run.created_at)}</span>
                <span><strong>Updated:</strong> {formatDate(run.updated_at)}</span>
              </div>
              <div style={{ display: 'flex', gap: '16px' }}>
                <span><strong>Started:</strong> {formatDate(run.started_at)}</span>
                <span><strong>Finished:</strong> {formatDate(run.finished_at)}</span>
              </div>
              {run.error && (
                <div style={{ color: 'red' }}>
                  <strong>Error:</strong> {run.error}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Subcard 2: Plan Target */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Target</h3>
            <button
              onClick={() => toggleCard('planTarget')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.planTarget ? '-' : '+'}
            </button>
          </div>
          {expandedCards.planTarget && (
            <p className="card-description">Plan target contents will be implemented here.</p>
          )}
        </div>

        {/* Subcard 3: Plan Options */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Plan Options</h3>
            <button
              onClick={() => toggleCard('planOptions')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.planOptions ? '-' : '+'}
            </button>
          </div>
          {expandedCards.planOptions && (
            <p className="card-description">Plan options (DomainConstraints) will be implemented here.</p>
          )}
        </div>

        {/* Subcard 4: Search Parameters */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Search Parameters</h3>
            <button
              onClick={() => toggleCard('searchParameters')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.searchParameters ? '-' : '+'}
            </button>
          </div>
          {expandedCards.searchParameters && (
            <p className="card-description">Search parameters will be implemented here.</p>
          )}
        </div>

        {/* Subcard 5: Score Rules */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Score Rules</h3>
            <button
              onClick={() => toggleCard('scoreRules')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.scoreRules ? '-' : '+'}
            </button>
          </div>
          {expandedCards.scoreRules && (
            <p className="card-description">Score rules will be implemented here.</p>
          )}
        </div>

        {/* Subcard 6: Results */}
        <div className="card mb-4" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="card-title" style={{ fontSize: '18px' }}>Results</h3>
            <button
              onClick={() => toggleCard('results')}
              className="button button--secondary"
              style={{ padding: '2px 8px', minWidth: '30px' }}
            >
              {expandedCards.results ? '-' : '+'}
            </button>
          </div>
          {expandedCards.results && (
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
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
    </div>
  );
}
