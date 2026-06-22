import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProjectTemplate } from '../api/projects';
import { listPlanningRuns, PlanningRun } from '../api/planning';

type PlanningOutputSolverPageProps = {
  projectId: string;
};

type OrderByField = 'id' | 'name' | 'created_at' | 'updated_at';

export function PlanningOutputSolverPage({ projectId }: PlanningOutputSolverPageProps) {
  const [viewLabel, setViewLabel] = useState<string>('Output Solver');
  const [runs, setRuns] = useState<PlanningRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [orderBy, setOrderBy] = useState<OrderByField>('created_at');
  const [orderReverse, setOrderReverse] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const template = await getProjectTemplate(projectId);
        const outputSolverView = template.views.find(v => v.view_key === 'planning_output_solver');
        if (outputSolverView) {
          setViewLabel(outputSolverView.label);
        }
        
        const runsData = await listPlanningRuns('output_solver');
        setRuns(runsData);
      } catch (error) {
        setError('Failed to load planning runs');
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId]);

  // Filter and sort runs
  const filteredAndSortedRuns = runs
    .filter(run => {
      const matchesSearch = searchQuery === '' || 
        (run.name && run.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        run.id.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesStatus = statusFilter === '' || run.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let comparison = 0;
      
      switch (orderBy) {
        case 'id':
          comparison = a.id.localeCompare(b.id);
          break;
        case 'name':
          const nameA = a.name || a.id;
          const nameB = b.name || b.id;
          comparison = nameA.localeCompare(nameB);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'updated_at':
          const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
          const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
          comparison = timeA - timeB;
          break;
      }
      
      return orderReverse ? -comparison : comparison;
    });

  const getDisplayName = (run: PlanningRun) => {
    return run.name || run.id.substring(0, 10);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'failed':
        return '#d52828'; // red
      case 'completed':
        return '#2e894f'; // green
      case 'running':
        return '#d4a720'; // yellow
      case 'pending':
        return '#3b62a1'; // blue
      default:
        return '#6b7280'; // gray
    }
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading planning runs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <button onClick={() => window.location.reload()} className="button button--secondary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="catalog-header">
        <div className="catalog-header__title">
          <h2 className="card-title">{viewLabel}</h2>
          <p className="card-description">View and manage planning runs.</p>
        </div>
        <Link 
          to={`/projects/${projectId}/planning/planning_output_solver/new`}
          className="button button--primary"
          style={{ textDecoration: 'none' }}
        >
          + New Run
        </Link>
      </div>
      <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }} />

      <div className="mb-6" style={{ marginBottom: '24px' }}>
        <input
          type="text"
          placeholder="Search runs..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="form-input"
          style={{ marginBottom: '12px' }}
        />
        
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label htmlFor="status-filter" style={{ width: 'auto', textAlign: 'right', marginRight: '8px', whiteSpace: 'nowrap' }}>Status:</label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-input"
              style={{ padding: '4px 8px' }}
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label htmlFor="order-by" style={{ width: 'auto', textAlign: 'right', marginRight: '8px', whiteSpace: 'nowrap' }}>Order by:</label>
            <select
              id="order-by"
              value={orderBy}
              onChange={(e) => setOrderBy(e.target.value as OrderByField)}
              className="form-input"
              style={{ padding: '4px 8px' }}
            >
              <option value="id">ID</option>
              <option value="name">Name</option>
              <option value="created_at">Created At</option>
              <option value="updated_at">Updated At</option>
            </select>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label htmlFor="order-reverse" style={{ width: 'auto', textAlign: 'right', marginRight: '8px', whiteSpace: 'nowrap' }}>Descending:</label>
            <input
              type="checkbox"
              id="order-reverse"
              checked={orderReverse}
              onChange={(e) => setOrderReverse(e.target.checked)}
              style={{ verticalAlign: 'middle' }}
            />
          </div>
        </div>
        <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }} />
      </div>

      {filteredAndSortedRuns.length === 0 ? (
        <div className="card state-message">
          <p className="state-message__text">
            {runs.length === 0 ? 'No planning runs found.' : 'No planning runs match your search.'}
          </p>
        </div>
      ) : (
        <div className="project-grid">
          {filteredAndSortedRuns.map((run) => (
            <Link
              key={run.id}
              to={`/projects/${projectId}/planning/planning_output_solver/${run.id}`}
              className="card project-card"
              style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'row', padding: 0 }}
            >
              <div
                style={{
                  width: '15px',
                  height: '100%',
                  backgroundColor: getStatusColor(run.status),
                  flexShrink: 0,
                }}
              />
              <div style={{ padding: '18px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <h3 className="project-card__title">{getDisplayName(run)}</h3>
                <p className="project-card__description">
                  <strong>Status:</strong> {run.status}
                </p>
                <p className="project-card__description">
                  <strong>Updated:</strong> {formatDate(run.updated_at)}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
