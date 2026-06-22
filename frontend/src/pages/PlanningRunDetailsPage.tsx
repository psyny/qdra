import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPlanningRunWithResults, PlanningRunWithResults } from '../api/planning';

type PlanningRunDetailsPageProps = {
  projectId: string;
};

type SubcardKey = 'runningState' | 'planTarget' | 'planOptions' | 'searchParameters' | 'scoreRules' | 'inputJson' | 'resultJson' | 'results';

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

        {/* Subcard 8: Results */}
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
            <p className="card-description">Results visualization will be implemented here.</p>
          )}
        </div>
    </div>
  );
}
